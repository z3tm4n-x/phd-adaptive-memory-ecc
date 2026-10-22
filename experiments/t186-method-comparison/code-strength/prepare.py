"""Reproduce the single preparatory table; never invent pending Q certificates."""
import argparse
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path
import subprocess
import sys

from codec import Code, ROOT
from cost import packing
from checks import run as checks

HERE = Path(__file__).resolve().parent
REL = HERE.relative_to(ROOT).as_posix()
BASE = "76413140a8ce4c3884a44df5dbeb619580339faa"


def digest(data):
    return hashlib.sha256(data.replace(b"\r\n",b"\n")).hexdigest()


def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True,
                       default=lambda x: str(x) if isinstance(x,F) else None)+"\n").encode("utf-8")


def verify():
    sources = json.loads((HERE / "sources.json").read_text(encoding="utf-8"))
    for source in sources["files"]:
        old = subprocess.check_output(["git","show",f'{source["commit"]}:{source["path"]}'],cwd=ROOT)
        actual = (ROOT / source["path"]).read_bytes()
        if digest(old) != source["sha256"] or digest(actual) != source["sha256"]:
            raise ValueError("source mismatch: " + source["path"])
    changed = subprocess.check_output(["git","diff","--name-only",BASE,"--","experiments/t186-method-comparison"],cwd=ROOT,text=True).splitlines()
    if any(not p.startswith(REL + "/") for p in changed):
        raise ValueError("previous comparison changed; this table must preserve stage1-4")
    return sources


def agreement_gaps(agreement, input_digest):
    gaps = []
    if agreement.get("common_input_sha256") != input_digest:
        gaps.append("agreement is not bound to the current proposed input")
    if agreement.get("status") != "agreed":
        gaps.append("common input has not been agreed")
    for role in ("theorist","map_engineer"):
        record = agreement[role]
        if record.get("status") != "agreed" or not record.get("reply_url"):
            gaps.append(role + ": no explicit answer to the proposed input")
        if record.get("input_sha256") != input_digest:
            gaps.append(role + ": no matching input hash in agreement record")
    if not agreement["theorist"].get("certificate_sha"):
        gaps.append("no new n39 adaptation / t2 with application certificate")
    return gaps


def render(cfg, resources, gaps):
    W = cfg["words"]
    r1,r2 = resources["1"],resources["2"]
    g1,g2 = packing(W,39),packing(W,44)
    geometry = lambda g: f'{g["useful_bits"]//8} / {g["code_bits"]//8} / {g["allocated_bits"]//8} байт'
    op = lambda r: f'{r["syndrome_two_input_xors"]} XOR + ROM + {r["correction_two_input_xors"]} XOR; encoder {r["encoder_two_input_xors"]} XOR'
    mem = lambda r: f'{r["lookup_entries"]}×{r["lookup_width_bits"]} бит = {r["lookup_bytes"]} байт ROM + регистры'
    lines = ["# Одна таблица трёх вариантов — подготовка #186/#196/#206", "",
             "Статус: предложение общего входа от 22.10.2026; согласование не получено.",
             "Числа геометрии и функционального кодека вычислены. Сравнительные Q, периоды,",
             "полные численные цены и победитель пока не установлены. Таблица не является",
             "готовым сравнением. После ответов меняется эта же таблица, а не создаётся вторая.", "",
             "| Показатель | Одна ошибка, постоянный | Одна ошибка, адаптация | Две ошибки, постоянный |",
             "|---|---|---|---|"]
    rows = [
        ("Внешний код (n,k,t)", "(39,32,1)", "(39,32,1)", "(44,32,2)"),
        ("Полезная / кодовая / занятая ёмкость", geometry(g1), geometry(g1), geometry(g2)),
        ("Проверочные / добавочные разряды на слово", "7 / 9", "7 / 9", "12 / 4"),
        ("Физическая упаковка / полный read / RMW", "3 x16 адреса; 3 / 6 тактов обмена", "то же", "то же"),
        ("Общий закон воздействия", "на бит r(t), массив 39Wr(t)", "тот же 39Wr(t)", "тот же r(t), массив 44Wr(t)"),
        ("Общий срок / допуск / приложение", "315576000 с / 0.001 / strict-uniform", "то же", "то же"),
        ("Период / таймеры", "P1: после согласования сервиса и Q", "ka, w, h, NR: новый расчёт #196", "P2: после согласования сервиса и Q"),
        ("Q-upper за T и запас epsilon−Q", "fixed-E T187 (3); приложение/начало ещё не подписаны", "новый n39 upper отсутствует; старый full38 не перенесён", "fixed-E T187 (3); S3 и mixed/direct отдельно"),
        ("Постоянный класс / интервал оптимума", "sufficient отдельно; class lower ещё не задан", "выигрыш против fixed-класса пока не установлен", "sufficient отдельно; class lower ещё не задан"),
        ("Обнаружение / исправление", "3r + d1; при ERR +3w+u", "то же + доставка/решение по замороженному договору", "3r + d2; при ERR +3w+u"),
        ("RMW / ответ приложению", "3r+d1+e1+3w+u; + очередь и доставка", "то же; проверяется общий deadline 3 мкс", "3r+d2+e2+3w+u; + очередь и доставка"),
        ("Средняя полная SRAM / пик", "B1/T; пик на каждом 1 мс <=80% проверяется", "Ba/T; skip не отменяет цену решения", "B2/T; задержка кодека входит в ресурс"),
        ("Кодек: логические операции на слово", op(r1), op(r1), op(r2)),
        ("Кодек: предложенная плотная таблица", mem(r1), mem(r1), mem(r2)),
        ("Контроллер/наблюдение/полезный канал", "полный вектор C1; долю ненужного monitor согласовать", "полный Ca: cuts, records, timer, decisions, payload", "полный C2; та же политика common transport"),
        ("Память, LUT/BRAM, энергия", "131136 байт frozen transport/state, если сохранён; + policy/buffers; LUT/BRAM/J параметры", "то же + адаптивные таймеры/состояние", "то же + цена кодека t2"),
        ("После A / незавершённая операция", "счёт до T; полное started-work даёт верх pending-хвоста", "то же, без остановки на первом превышении", "то же"),
        ("Происхождение цены", "геометрия/операции вычислены; времён/FPGA измерений нет", "то же; n39 перенос не подписан", "то же; 10/20 мкс T187 не использованы"),
        ("Условие смены предпочтения", "сопоставимые lower/upper, не отношение двух sufficient", "Ca vs C2 при общем входе и координате цены", "d2_bus < (B_a−B2_other)/Ndecode,2, плюс временные/ресурсные ограничения"),
    ]
    lines += ["| " + " | ".join(row) + " |" for row in rows]
    lines += ["", "Обозначения: r/w — время x16 read/write; d/e — decode/encode; u —",
              "разворот шины; B — полная оплаченная занятость за T. Блокировка шины",
              "кодеком и его полная задержка — отдельные параметры. Все формулы и",
              "области порогов — [COST](../COST.md). Кодовые позиции считаются полностью,",
              "добавочные неиспользуемые разряды исключены только при заявленном маскировании.", "",
              "Не закрыто: " + "; ".join(gaps) + ".", ""]
    return "\n".join(lines).encode("utf-8")


def build():
    sources = verify()
    raw = (HERE/"common-input.proposed.json").read_bytes()
    cfg = json.loads(raw)
    agreement = json.loads((HERE/"agreement.json").read_text(encoding="utf-8"))
    gaps = agreement_gaps(agreement,digest(raw))
    resources = {str(t):Code(t).resources() for t in (1,2)}
    results = dict(status="PREPARATION_ONLY_NOT_COMPLETED_COMPARISON", common_input_sha256=digest(raw),
                   agreement_gaps=gaps, codes=resources, geometries={str(n):packing(cfg["words"],n) for n in (39,44)},
                   comparative_probability_results=None, comparative_price_results=None,
                   recommendation=None, science_inputs_changed_in_old_stages=False,
                   source_manifest=sources,
                   implementation_sha256={p.name:digest(p.read_bytes()) for p in sorted(HERE.glob("*.py"))})
    validation = checks()
    # Incomplete, stale or one-sided answers must not be treated as agreement.
    h=digest(raw)
    fake={"status":"agreed","common_input_sha256":h,
          "theorist":{"status":"agreed","reply_url":"unit-test-only","certificate_sha":"unit-test-only","input_sha256":h},
          "map_engineer":{"status":"agreed","reply_url":"unit-test-only","input_sha256":h}}
    assert not agreement_gaps(fake,h)
    assert agreement_gaps(fake,"different-input")
    assert agreement_gaps({**fake,"map_engineer":{"status":"requested_not_received"}},h)
    validation["checks"] += ["agreement requires matching input hash", "both counterparts must answer"]
    validation["count"] += 2
    return {"preparation.json":encode(results),"validation.json":encode(validation),"table.md":render(cfg,resources,gaps)}, gaps


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--record",action="store_true",help="write only this new package's preparation outputs")
    ap.add_argument("--require-agreement",action="store_true",help="fail if comparative calculation is not yet authorized by the common input")
    args=ap.parse_args()
    files,gaps=build()
    if args.require_agreement and gaps:
        print(json.dumps({"comparison_ready":False,"gaps":gaps},ensure_ascii=False,indent=2))
        return 2
    out=HERE/"outputs"
    for name,data in files.items():
        if args.record:
            out.mkdir(exist_ok=True)
            (out/name).write_bytes(data)
        elif (out/name).read_bytes().replace(b"\r\n",b"\n") != data:
            raise ValueError("preparation replay differs: " + name)
    print(json.dumps({"preparation_reproduced":True,"comparison_ready":False,
                      "checks":json.loads(files["validation.json"])["count"],
                      "files":{name:digest(data) for name,data in files.items()},
                      "pending_common_input":bool(gaps)},ensure_ascii=False,indent=2))
    return 0


if __name__=="__main__":
    sys.exit(main())
