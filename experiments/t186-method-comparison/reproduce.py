"""One command: python -B experiments/t186-method-comparison/reproduce.py."""
from datetime import datetime, timezone
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import platform
import subprocess
import time
from checks import validate, check_pilot_results
from model import run, resource_checks

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[1]
OUT=HERE/"outputs"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def canonical(path):
    return path.read_bytes().replace(b"\r\n",b"\n")


def write_json(path, data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+"\n",encoding="utf-8",newline="\n")


def verify_sources():
    manifest=json.loads((HERE/"sources.json").read_text(encoding="utf-8"))
    for src in manifest["repository_sources"]:
        pinned=subprocess.check_output(["git","show",src["commit"]+":"+src["path"]],cwd=REPO)
        if digest(pinned)!=src["sha256"] or digest(canonical(REPO/src["path"]))!=src["sha256"]:
            raise AssertionError("pinned dependency drift: "+src["path"])
    for src in manifest["frozen"]:
        pinned=subprocess.check_output(["git","show",src["commit"]+":"+src["path"]],cwd=REPO)
        if digest(pinned)!=src["sha256"] or digest(canonical(REPO/src["path"]))!=src["sha256"]:
            raise AssertionError("pre-run input drift: "+src["path"])
    return dict(status="PASS",repository_sources=len(manifest["repository_sources"]),
                pre_run_files=len(manifest["frozen"]),pre_run_commit=manifest["preregistered"],
                external_PDFs_required_for_numeric_repeat=False,
                external_source_scope="sources.json/SOURCES.md; no network silently needed")


def table(results, resource):
    names={"constant_fast":"Заданный постоянный FAST","our_err_r4":"Наше ERR/r4"}
    text=["# Пилот: общий сервис, фиксированная трасса",
          "",
          "OWN RESULT, проверка реализации. Q(T) не оценивается; FAST не оптимальный постоянный.",
          "",
          "| Правило | Начатые проверки | База, нс | Коррекции, нс | Приложение, нс | Вся шина, % | Первый A_T, с | Работа после A_T, нс |",
          "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for r in results:
        b=r["bus"]
        text.append(f"| {names[r['method']]} | {r['started_control_operations']} | {b['control_base_ns']} | {b['correction_extra_ns']} | {b['application_read_ns']} | {r['mean_bus_percent']:.9f} | {r['first_exceedance']['t']/1e9:.9f} | {r['bus_after_first_exceedance']['total_ns']} |")
    delta=Fraction(results[0]["mean_bus_fraction_exact"])-Fraction(results[1]["mean_bus_fraction_exact"])
    text+=["",f"Разность {float(delta)*100:.9f} п.п. на данной трассе; никакой миссионной экономии из неё не следует.",
           f"Общий консервативный верх любого1мс: {resource['peak_any_1ms_bus_upper_percent']:.9f}%; это не измеренный максимум.",
           "Оба метода имеют максимальную модельную задержку приложения2344нс. Незавершённых операций на закреплённом конце0; отдельные граничные тесты покрывают обрезанные операции.",
           "Каждое правило имеет свою ERR-историю; полные времена и цена после первого превышения — в results.json.",""]
    return "\n".join(text)


def main():
    start=time.perf_counter()
    sources=verify_sources()
    cfg=json.loads((HERE/"inputs.json").read_text(encoding="utf-8"))
    validation=validate(cfg,REPO)
    first_start=time.perf_counter()
    results=[run(cfg,m) for m in cfg["methods"]]
    first_seconds=time.perf_counter()-first_start
    independent=check_pilot_results(cfg,results,REPO)
    repeat_start=time.perf_counter()
    repeated=[run(cfg,m) for m in cfg["methods"]]
    repeat_seconds=time.perf_counter()-repeat_start
    assert repeated==results,"same-input repeat changed"
    resource=resource_checks(cfg)
    OUT.mkdir(exist_ok=True)
    own_files=["inputs.json","sources.json","model.py","checks.py","reproduce.py"]
    hashes={p:digest(canonical(HERE/p)) for p in own_files}
    output=dict(status="OWN RESULT; first stage awaiting contract review",
                inputs_sha256=hashes["inputs.json"],implementation_sha256=hashes,
                results=results,resource_checks=resource)
    write_json(OUT/"results.json",output)
    write_json(OUT/"validation.json",dict(sources=sources,directed=validation,independent_price=independent))
    # Planning diagnostic only, not a sampled realization or mission proof.
    mission=315576000
    expected_marks=float(Fraction("0.000154704")*mission+Fraction("28310.473728"))
    expected_words=cfg["words"]*(-math.expm1(-expected_marks/cfg["words"]))
    cost=dict(scope="planning diagnostic under uniform singleton Poisson; not a qualified R0-A law",
              expected_marks=expected_marks,expected_distinct_words=expected_words,
              watch_all_expected_visits=expected_words*mission/(cfg["words"]*196e-9),
              row_budget_upper=480,zero_failure_binomial_sample_sizes=[])
    for eps in [0.001,0.0001]:
        cost["zero_failure_binomial_sample_sizes"].append(dict(
            epsilon=eps,one_sided_alpha=0.05,
            one_row=math.ceil(math.log(0.05)/math.log1p(-eps)),
            family480_bonferroni_per_row=math.ceil(math.log(0.05/480)/math.log1p(-eps))))
    write_json(OUT/"cost-budget.json",cost)
    (OUT/"table.md").write_text(table(results,resource),encoding="utf-8",newline="\n")
    stable={p:digest((OUT/p).read_bytes()) for p in ["results.json","validation.json","table.md","cost-budget.json"]}
    write_json(OUT/"repeat.json",dict(status="PASS",equal_runs=2,outputs_sha256=stable,
                                    meaning="deterministic reproducibility; no new statistical samples"))
    # Timings are deliberately outside repeat.json's deterministic output set.
    write_json(OUT/"performance.json",dict(
        measured_at_utc=datetime.now(timezone.utc).isoformat(),
        python=platform.python_version(),system=platform.system(),machine=platform.machine(),
        paired_pilot_first_wall_s=first_seconds,paired_pilot_repeat_wall_s=repeat_seconds,
        total_wall_s=time.perf_counter()-start,
        scope="local wall time only; not target CPU execution or mission MC forecast"))
    print(json.dumps(dict(status="PASS",checks=validation["checks"],source_files=sources["repository_sources"],
                          pilot_rows=len(results),same_input_repeat=True,
                          paired_pilot_wall_s=first_seconds,output="experiments/t186-method-comparison/outputs"),
                     ensure_ascii=True))


if __name__=="__main__":
    main()
