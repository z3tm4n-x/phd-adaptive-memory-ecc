"""Render the published tables from the saved generator, simulation and cost outputs."""
import argparse
from decimal import Decimal, ROUND_CEILING, ROUND_FLOOR
import json
from pathlib import Path

HERE=Path(__file__).resolve().parent


def get(name): return json.loads((HERE/name).read_text(encoding="utf-8"))


def number(x,digits=0):
    return format(x,f",.{digits}f").replace(","," ").replace(".",",")


def interval(r):
    a,b=r["wilson95"]
    def edge(x,how):
        return str(Decimal(str(x)).quantize(Decimal("0.000001"),rounding=how)).replace(".",",")
    return edge(a,ROUND_FLOOR)+"…"+edge(b,ROUND_CEILING)


def main():
    cli=argparse.ArgumentParser(description=__doc__);cli.add_argument("--check",action="store_true")
    args=cli.parse_args(); ge=get("ge-results.json"); legacy=get("legacy-results.json"); ideal=get("ideal-results.json")
    lines=["# Полные результаты по восьми профилям","",
           "В каждой строке 1500 реализаций. Интервал Уилсона 95% дан для вероятности первого превышения на одном фиксированном профиле, границы округлены наружу. Измерение Q и стоимости в паре использует одни частицы. Корреляция между политиками учитывается при подсчёте стандартной ошибки парной экономии в JSON.","",
           "## Профили в нормировке банка","",
           "Экспозиция — ожидаемые разрядные инверсии за срок. Рост и сумма подъёмов относятся к частоте инверсий банка. Приведены максимальный наклон линейных участков, первоначальный избыток над фоном и последующая положительная вариация.","",
           "| Профиль | Пик, с⁻¹ | Экспозиция | Макс. рост, с⁻² | Начальный избыток, с⁻¹ | Последующие подъёмы, с⁻¹ | Сумма, с⁻¹ |",
           "|---|---:|---:|---:|---:|---:|---:|"]
    for k,v in get("profile-audit.json")["profiles"].items():
        vals=[v["peak_bank_s_inv"],v["S1_bank"],v["max_slope"],v["start_excess"],v["positive_variation"],v["initial_plus_rises"]]
        cells=[k]+[number(x,n) for x,n in zip(vals,(9,6,10,9,9,9))]
        lines.append("| "+" | ".join(cells)+" |")
    lines+=["","## Исходные часы, 656 слов","",
            "Столбец C — исходная остановка и её доля сканирования в процентах десятилетия. Столбец «до T» — полный объём начатых слов на исходных часах в эквиваленте времени идеального обхода. Исходная и независимо проверенная классификации первого превышения совпали по каждой траектории.","",
            "| Профиль | Правило | Первые превышения | Q по частоте | Интервал 95% | C, % | До T, % | Ремонты до T, среднее |",
            "|---|---|---:|---:|---|---:|---:|---:|"]
    for k,v in legacy.items():
        for name,r in v.items():
            assert r["paired_disagreements"]==0
            original=ideal[k]["rows"][name]["source"]
            cells=[k,name,str(r["corrected_failures"]),number(r["corrected_failures"]/1500,6),interval(r),
                   number(original["stopped_scan_pct"],4),number(r["full_scan_pct"],4),number(r["mean_repairs"],2)]
            lines.append("| "+" | ".join(cells)+" |")
    lines+=["","## Один порт -45, 65 536 слов","",
            "Каждая строка использует новый L=45,8752 мс. age — решение советника по возрасту последнего замеченного исправления. cell — решение по подтверждённым нулям завершённых интервалов. FAST означает шаг L в адаптивной политике. Цена — среднее за срок в парных прогонах. Для постоянного календаря отсутствует переключаемое состояние FAST. Пик — верх для номинальных реализованных защитных операций в любом окне 1 мс, общий аппаратный резерв приведён в паспорте.","",
            "| Профиль | Правило | Превышения | Q по частоте | Интервал 95% | Ремонты | Шина, с | Шина, % T | Пик ≤, % | FAST, с | Переключения |",
            "|---|---|---:|---:|---|---:|---:|---:|---:|---:|---:|"]
    for k,v in ge.items():
        for name,r in v["rows"].items():
            cells=[k,name,str(r["failures"]),number(r["Q_MC"],6),interval(r),number(r["mean_repairs"],2),
                   number(r["bus_s"],3),number(r["bus_pct"],6),number(r["nominal_path_peak_upper_pct"],3),
                   "—" if r["mean_fast_s"] is None else number(r["mean_fast_s"],2),number(r["mean_switches"],2)]
            lines.append("| "+" | ".join(cells)+" |")
    text="\n".join(lines)+"\n"; path=HERE/"TABLES.md"
    if args.check: assert path.read_text(encoding="utf-8")==text
    else: path.write_text(text,encoding="utf-8",newline="\n")


if __name__=="__main__": main()
