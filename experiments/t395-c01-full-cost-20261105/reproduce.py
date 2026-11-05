"""Issue395: three fixed c01 rows, complete conditional bus/serial cost.

No grid, author solver imports, simulation or physical calibration.
Sources, including the unmerged PR394, are immutable Git objects.
"""
import argparse
from fractions import Fraction as F
from hashlib import sha256
import json
from math import comb, gcd
from pathlib import Path
import subprocess

from verify import verify_decimal

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NS = 10**9


def digest(data):
    return sha256(data.replace(b"\r\n", b"\n")).hexdigest()


def source(pin):
    result = subprocess.run(["git", "show", pin["ref"] + ":" + pin["path"]],
                            cwd=ROOT, capture_output=True)
    if result.returncode:
        raise RuntimeError("Missing pinned Git object; git fetch origin " + pin["ref"])
    assert digest(result.stdout) == pin["sha256_lf"], pin["path"]
    return result.stdout.decode("utf-8")


def ceil(x):
    return -(-x.numerator // x.denominator)


def decimal(x, places=6, upper=False):
    x = F(x) * 10**places
    k = ceil(x) if upper else x.numerator // x.denominator
    sign, k = ("-" if k < 0 else ""), abs(k)
    return f"{sign}{k // 10**places}.{k % 10**places:0{places}d}"


def encode(value):
    if isinstance(value, F):
        return str(value)
    if isinstance(value, dict):
        return {k: encode(v) for k, v in value.items()}
    if isinstance(value, list):
        return [encode(v) for v in value]
    return value


def nominal_audit(Tns, W, k, operation_ns):
    """Integer count for xi=1,J=0 only; uniform lifetime bound is separate."""
    if k is None:
        return {"started": 0, "startup": 0, "periodic_after_startup": 0,
                "partial_final_pass_words": 0, "scope": "OFF on all histories"}
    cycle = 196 * k * W
    blocks, remainder = divmod(Tns, cycle)
    q = lambda j: 1568 * (j // 8) + 164 * (j % 8)
    lo, hi = 0, W
    while lo < hi:
        mid = (lo + hi) // 2
        if q(mid) < remainder:
            lo = mid + 1
        else:
            hi = mid
    partial = lo
    # Independent closed-form count of the same batch8 prefix.
    frames, rem = divmod(remainder, 1568)
    closed = min(W, 8 * frames + min(8, (rem + 163) // 164))
    assert partial == closed
    total = blocks * W + partial
    last = ((total - 1) // W) * cycle + q((total - 1) % W)
    assert last < Tns
    return {"started": total, "startup": W, "periodic_after_startup": total-W,
            "partial_final_pass_words": partial if partial < W else 0,
            "last_start_ns": last, "last_completion_ns": last+operation_ns,
            "completion_tail_after_T_ns": max(0, last+operation_ns-Tns),
            "scope": "nominal witness only; not a replacement for (13)"}


def calculate(cfg):
    texts = {k: source(v) for k, v in cfg["sources"].items()}
    src = {k: json.loads(v) for k, v in texts.items() if cfg["sources"][k]["path"].endswith(".json")}
    env, svc = src["map_inputs"]["environment"], src["map_inputs"]["service"]
    common, lower = src["common"], src["class_lower"]
    app, codec = common["application"], common["service"]
    cell = src["map_result"]["cells"]["c01"]
    fixed = cell["methods"]["F_max"]
    accepted = cell["price_bounds"][fixed["price"]]["price"]
    W, T, eps = 1048576, F(src["map_inputs"]["bank"]["mission_s"]), F(1, 1000)
    grid = next(x for x in src["map_cells"]["cells"] if x["id"] == "c01")
    assert (grid["words"], F(grid["alpha"]), F(grid["epsilon"])) == (W, 0, eps)
    assert gcd(3,W) == gcd(5,W) == 1
    assert fixed["pair"] == [52, 52] and lower["words"] == W
    assert F(lower["alpha"]) == 0 and F(lower["epsilon"]) == eps and F(lower["mission_s"]) == T
    assert F(lower["fixed_class_cutoff_s"]) == 14
    xp, xm, J = F(svc["xi_plus"]), F(svc["xi_minus"]), F(svc["J_ns"])
    delta = F(src["map_inputs"]["information"]["lifetime_delta_exec"])
    D, b, Fs = env["reference_positions"], F(env["b"]), F(env["Fs"])
    pulse_count, width = env["template"]["count"], env["template"]["width_s"]
    a = 2 * Fs / (pulse_count * width)
    S1 = b*T+Fs
    S2 = b*b*T+2*b*Fs+F(pulse_count*width, 3)*a*a
    S3 = b**3*T+3*b*b*Fs+pulse_count*width*b*a*a+F(pulse_count*width, 4)*a**3
    M1, M2, M3, Bu = S1/D, S2/D**2, S3/D**3, (b+a)/D
    P = lambda k, up: (196*k*W*(xp if up else xm)+(J if up else -J))/NS
    Nmax = W*(T/P(1, False)+2)
    assert Nmax == F(cell["resource"]["calendar"]["necessary_class_maximum_reads_upper"])
    h, Tns = app["epoch_ns"], int(T)*NS
    offset_r = app["first_ns"]+app["read_offset_ns"]
    offset_w = app["first_ns"]+app["write_offset_ns"]
    Nar = (Tns-1-offset_r)//h+1
    Naw_off = (Tns-1-offset_w)//h+1
    assert (Nar, Naw_off) == (315569688607, 315569688606)
    deadline = F(svc["app_deadline_ns"])
    Happ = ((eps-delta)/(W*comb(39, 2))-2*Bu*(deadline/NS)*M1)/M2
    Papp = F(W*h, NS)
    gaps, free_gap = int(T//Papp)-1, Papp-deadline/NS
    mu = 39*Bu*free_gap
    zlo = W*gaps*comb(39, 2)*(b/D)**2*free_gap**2*(1-mu)
    off_lower = zlo/(1+zlo)-delta
    assert 0 < mu < 1 and off_lower > F(cfg["rows"][2]["risk_lower_checkpoint"]) > eps

    def q44(extra_ns=F(0)):
        dE = (128*xp+3*J+extra_ns)/NS
        L = P(5102, True)+dE
        return delta+W*comb(44, 3)*(L*L*M3+3*Bu*dE*L*M2+3*Bu**2*dE*dE*M1)

    assert q44() < F(cfg["rows"][1]["risk_upper_checkpoint"]) < eps
    result = {
        "status": "OWN RESULT; conditional cost; joint independent acceptance with PR394 pending",
        "base_main": cfg["base_main"], "theory394_head": cfg["theory394_head"],
        "inputs_sha256_lf": digest((HERE/"inputs.json").read_bytes()),
        "code_sha256_lf": {p: digest((HERE/p).read_bytes()) for p in ("reproduce.py", "verify.py")},
        "common": {"W": W, "T_s": T, "epsilon": eps, "alpha": F(0),
                   "useful_bytes": 4*W, "allocated_bytes": 6*W,
                   "Nmax": Nmax, "delta0": delta, "xp": xp, "xm": xm, "J_ns": J,
                   "S1": S1, "S2": S2, "S3": S3, "reference_positions": D,
                   "app_reads": Nar, "off_app_writes": Naw_off},
        "off_update": {"P_app_s": Papp, "H_app1_s": Happ,
                       "P_minus_H_s": Papp-Happ, "P_over_H": Papp/Happ,
                       "Q_lower_replayed": off_lower, "counts_m": gaps,
                       "actual_stream_changed": False},
        "rows": [],
    }
    for spec in cfg["rows"]:
        key, n, k = spec["id"], spec["n"], spec["k"]
        dec, enc = F(codec[f"decode{n}_ns"]), F(codec[f"encode{n}_ns"])
        Rnom, Enom, Anom, Inom = 48+dec, 104+dec, 104+dec+enc, 56+enc
        R, E, Aw = Rnom*xp+J, Enom*xp+J, Anom*xp+J
        if k is None:
            NR = ND = F(0)
            read_terms = {"steady": F(0), "startup_padding": F(0), "end_padding": F(0), "bad_execution": F(0)}
            repair_terms = {"none_by_OFF_contract": F(0)}
            Q, qtype, Naw = off_lower, "strict_lower_excludes", Naw_off
        else:
            read_terms = {"steady": W*T/P(k, False), "startup_padding": F(W),
                          "end_padding": F(W), "bad_execution": delta*Nmax}
            NR = min(Nmax, sum(read_terms.values(), F(0)))
            if n == 39:
                Q, qtype = F(fixed["Q_upper"]), "accepted_sufficient_upper"
                assert NR == F(accepted["reads_upper"])
                ND = F(accepted["repairs_upper"])
                repair_terms = {x:F(y) for x,y in accepted["repair_terms_upper"].items()}
                assert ND == min(NR, sum(repair_terms.values(), F(0)))
            else:
                Q, qtype, ND = q44(), "preliminary_PR394_sufficient_upper", NR
                repair_terms = {"all_started_reads_including_bad_histories": NR}
            Naw = 0
        counts = {"scrub_read": NR, "scrub_repair": ND, "app_read": Nar, "app_write": Naw,
                  "init": W, "decode": NR+Nar+Naw, "encode": Naw+W,
                  "read16": 3*(NR+Nar+Naw), "write16": 3*(ND+Naw+W), "turnaround": ND+Naw+W,
                  "payload_read_bytes": 4*Nar, "payload_write_bytes": 4*Naw}
        costs = {}
        for coord in ("bus", "serial"):
            rt = F(48) if coord == "bus" else Rnom
            at = F(104) if coord == "bus" else Anom
            it = F(56) if coord == "bus" else Inom
            payload = F(32)*xp*(Nar+Naw)/NS
            if key == "F39":
                old = accepted["coordinates"][coord]
                check, repair = F(old["checks_upper_s"]), F(old["repairs_upper_s"])
                ar, init = F(old["app_s"]["upper"]), F(old["init_s"]["upper"])
                aw = F(0)
                assert check == NR*(rt*xp+J)/NS and repair == ND*(56*xp+J)/NS
            else:
                check = NR*(rt*xp+J)/NS
                # Serial has one E+ span. Pure bus has two separated segments;
                # keep the inherited per-segment J instead of subtracting decode.
                repair = ND*(56*xp+(J if coord == "bus" else 0))/NS
                ar = Nar*(rt*xp+J)/NS
                aw = Naw*(at*xp+(2*J if coord == "bus" else J))/NS
                init = W*(it*xp+J)/NS
            app_total, protection = ar+aw, check+repair
            total = protection+app_total+init
            if key == "F39":
                assert total == F(accepted["coordinates"][coord]["all_known_upper_s"])
            costs[coord] = {"control_reads_s": check, "repairs_s": repair,
                            "dedicated_protection_s": protection,
                            "app_reads_s": ar, "app_writes_s": aw, "app_total_s": app_total,
                            "payload_action_time_s": payload,
                            "app_protection_overhead_s": app_total-payload, "init_s": init,
                            "known_added_protection_excluding_init_s": protection+app_total-payload,
                            "all_known_upper_s": total, "average_fraction_upper": total/T,
                            "unknown_additional_cost": "K_"+key+"_"+coord+" >= 0, not set to zero"}
            assert total == payload+(protection+app_total-payload)+init

        frames = 2+ceil((F(10**6)+max(E, Aw)+J)/(1568*xm))
        app_each = 1+ceil(F(10**6+int(deadline), h))
        ctrl_slots = 8*frames if k is not None else 0
        management = 64*xp+J
        peak_serial = (ctrl_slots*E+app_each*(R+Aw)+frames*management)/10**6
        peak_bus = (ctrl_slots*(104*xp+2*J)+app_each*((48+104)*xp+3*J)+frames*management)/10**6
        response = 820+1568*xp+J+Aw
        local = {"frames_per_ms_upper": frames, "app_each_per_ms_upper": app_each,
                 "control_slots_per_ms_upper": ctrl_slots,
                 "control_E_margin_ns": 164*xm-J-E,
                 "app_grant_margin_ns": 256*xm-J-Aw,
                 "app_to_management_margin_ns": 160*xm-J-Aw,
                 "response_upper_ns": response, "deadline_margin_ns": deadline-response,
                 "serial_peak_upper": peak_serial, "pure_bus_peak_upper": peak_bus,
                 "serial_peak_extra_budget_ns_per_ms": 800000-peak_serial*10**6,
                 "management_chunk_lower_ns": 64*xm-J,
                 "atomic_management_upper_ns": F(32),
                 "management_progress_lower_ns": 64*xm-J-32,
                 "management_to_next_control_margin_ns": 96*xm-2*J-64*xp,
                 "full_reserved_management_already_in_peak": True,
                 "both_app_streams_retained_in_peak": True}
        assert frames == 640 and app_each == 3
        assert local["management_to_next_control_margin_ns"] == F(cell["resource"]["resource"]["gap_before_next_control_ns"])
        if key == "F39":
            assert peak_serial == F(cell["resource"]["resource"]["peak_including_full_reserved_management_slot"])
        if key == "F44":
            assert peak_serial == F("0.69988196992") and response == F("2541.0172")
        assert peak_bus <= peak_serial < F(4,5) and response < deadline
        assert local["app_to_management_margin_ns"] > 0 and local["control_E_margin_ns"] > 0
        audit = nominal_audit(Tns, W, k, int(Enom))
        if k is not None:
            assert audit["started"] <= sum(v for a,v in read_terms.items() if a != "bad_execution")
        tails = {"read_last_arrival_ns": offset_r+(Nar-1)*h,
                 "read_completion_upper_ns": offset_r+(Nar-1)*h+deadline,
                 "write_last_arrival_ns": offset_w+(Naw-1)*h if Naw else None,
                 "write_completion_upper_ns": offset_w+(Naw-1)*h+deadline if Naw else None,
                 "all_offered_operations_fully_priced": True}
        result["rows"].append({"id": key, "n": n, "k": k, "Q": Q, "Q_type": qtype,
                               "Q_slack_or_exclusion_gap": eps-Q if k else Q-eps,
                               "P_nominal_s": F(196*k*W, NS) if k else Papp,
                               "period_lower_s": P(k, False) if k else Papp,
                               "read_terms_upper": read_terms, "repair_terms_upper": repair_terms,
                               "counts_upper": counts, "costs": costs, "local": local,
                               "nominal_calendar_audit": audit, "application_tail": tails,
                               "after_first_exceedance_accounted": True,
                               "hardware_qualified": False})

    strong = result["rows"][1]
    budgets = {}
    for coord in ("bus", "serial"):
        old = lower["costs"][coord]
        L = F(old["fixed_class_with_common_lower_s"])
        C = strong["costs"][coord]["all_known_upper_s"]
        gap = L-C
        assert gap > 0
        budgets[coord] = {"F39_class_protection_lower_s": F(old["fixed_class_new_protection_lower_s"]),
                         "F39_class_full_lower_s": L, "F44_known_upper_s": C,
                         "strict_extra_price_budget_s": gap,
                         "strict_extra_price_budget_us_per_s": gap/T*10**6,
                         "selector_only_intercept_ns": gap*NS/Nmax,
                         "issued_strict_cap_seconds_down": decimal(gap,6),
                         "issued_strict_cap_us_per_s_down": decimal(gap/T*10**6,6),
                         "unknown_F39_lower_used": F(0),
                         "condition": "all extra F44 price < budget; unknown F39 lower 0 by nonnegativity"}
    ctrl_margin = strong["local"]["control_E_margin_ns"]
    qextra = q44(ctrl_margin)
    assert qextra < eps
    # This box fixes the frame count used in the affine peak constraint.
    max_E = 128*xp+J+ctrl_margin
    max_Aw = 160*xm-J
    assert 2+ceil((F(10**6)+max(max_E,max_Aw)+J)/(1568*xm)) == 640
    result["F44_vs_all_F39"] = budgets
    result["joint_F44_region"] = {
        "units": "d,e,r true additional ns per decode/encode/repair; ell external non-SRAM response delay ns; K_x additional seconds not already charged",
        "nonnegative": ["d", "e", "r", "ell", "K_bus", "K_serial"],
        "d_plus_r_control_max_ns": ctrl_margin,
        "d_plus_e_app_management_max_ns": strong["local"]["app_to_management_margin_ns"],
        "d_plus_e_plus_ell_response_max_ns": strong["local"]["deadline_margin_ns"],
        "peak_coefficients": {"d": F(5126), "e": F(3), "r": F(5120)},
        "peak_rhs_ns_per_ms": strong["local"]["serial_peak_extra_budget_ns_per_ms"],
        "codec_price_seconds_per_extra_ns": {"decode": strong["counts_upper"]["decode"]/NS,
                                             "encode": F(W,NS), "repair": strong["counts_upper"]["scrub_repair"]/NS},
        "issued_codec_coefficients_up_s_per_ns": {"decode": F(ceil(strong["counts_upper"]["decode"]),NS),
                                                  "encode": F(W,NS), "repair": F(ceil(strong["counts_upper"]["scrub_repair"]),NS)},
        "Q_upper_at_max_control_extension": qextra,
        "management_requirement": "actual work obeys the inherited slot/atomic/progress and dispatch contract; its price is in K, its full slot is already in peak",
        "CPU_energy_logic_memory_idle": "separate unknown coordinates; no numerical advantage established",
        "all_conditions_required_together": True,
    }
    result["verification"] = verify_decimal(src, encode(result))
    return result


def table(r):
    pair = lambda row, key: " / ".join(decimal(row["costs"][c][key], 6, True) for c in ("bus", "serial"))
    lines = ["# Полная условная цена c01: три заданные строки", "",
             "В парных ячейках: **чистая шина / последовательное обслуживание**; эти две координаты не суммируются.",
             "Все цены — верх ожидаемых секунд за T=315576000 с, включая полный начатый хвост; подготовка амортизирована. Неизвестная добавка K остаётся сверх чисел.", "",
             "| Строка; номинальный P, с | Статус Q(T) | Контроль + ремонт, с | App read + write, с | До 0: init, с | Все известные работы, с | Средняя загрузка, % |",
             "|---|---|---:|---:|---:|---:|---:|---:|"]
    names = {"F39":"Долгоживущая (39,32), k=52", "F44":"Долгоживущая (44,32), k=5102", "OFF39":"Перезаписываемая (39,32), OFF"}
    for row in r["rows"]:
        upper = row["id"] != "OFF39"
        q = ("≤" if upper else ">")+decimal(row["Q"],12,upper)
        q += "; достаточный" if upper else "; исключён"
        avg = " / ".join(decimal(100*row["costs"][c]["average_fraction_upper"],9,True) for c in ("bus","serial"))
        lines.append("| "+" | ".join([names[row["id"]]+"; "+decimal(row["P_nominal_s"],9,True),q,pair(row,"dedicated_protection_s"),pair(row,"app_total_s"),pair(row,"init_s"),pair(row,"all_known_upper_s"),avg])+" |")
    lines += ["", "F39 — принятые Q/цена map-14; F44 — условный кандидат PR394 до итоговой независимой приёмки. OFF — цена исключённой программы, не допустимый конкурент.",
              "Контроль/ремонт, app-read/app-write, полезные beat и добавочные действия разложены в result.json; определения и совместные пределы K — в REPORT.md.",
              "Два верха этой таблицы не являются доказанной экономией. Сравнение F44 с необходимым низом всего F39 выполнено отдельно по PR320."]
    return "\n".join(lines)+"\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    cfg = json.loads((HERE/"inputs.json").read_text(encoding="utf-8"))
    r = calculate(cfg)
    out = {"result.json":json.dumps(encode(r),ensure_ascii=False,indent=2)+"\n", "TABLE.md":table(r)}
    for name,text in out.items():
        path = HERE/name
        if args.check:
            assert path.read_text(encoding="utf-8") == text, "Saved output differs: "+name
        else:
            path.write_text(text,encoding="utf-8",newline="\n")
    print("PASS: 3 fixed c01 rows; 12 pinned sources; accepted F39/PR320 reuse; whole-horizon accounting; local/peak constraints; Decimal cross-check.")
    if not args.check:
        print(out["TABLE.md"])
        print(json.dumps(encode(r["F44_vs_all_F39"]),ensure_ascii=False,indent=2))


if __name__ == "__main__":
    main()
