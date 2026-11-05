"""Own independent arithmetic path, not an independent scientific review."""
from decimal import Decimal as D, localcontext


def number(x):
    a, sep, b = str(x).partition("/")
    return D(a)/D(b) if sep else D(a)


def verify_decimal(src, result):
    with localcontext() as ctx:
        ctx.prec = 100
        close = lambda a,b: abs(a-b) < D("1e-70")
        g = result["common"]
        W, T, xp, xm, J = (number(g[k]) for k in ("W","T_s","xp","xm","J_ns"))
        nr_app, nw_off = number(g["app_reads"]), number(g["off_app_writes"])
        hard = W*(T/((196*W*xm-J)/D(10**9))+2)
        assert close(hard, number(g["Nmax"]))
        for row in result["rows"]:
            counts = row["counts_upper"]
            NR, ND = number(counts["scrub_read"]), number(counts["scrub_repair"])
            Naw = number(counts["app_write"])
            if row["k"]:
                p = (196*row["k"]*W*xm-J)/D(10**9)
                n_independent = W*(T/p+2)+number(g["delta0"])*hard
                assert close(NR, min(hard,n_independent))
            else:
                assert NR == ND == 0 and Naw == nw_off
            assert close(number(counts["decode"]), NR+nr_app+Naw)
            assert close(number(counts["read16"]),3*(NR+nr_app+Naw))
            assert close(number(counts["write16"]),3*(ND+Naw+W))
            for coord in ("bus","serial"):
                dec = D(src["common"]["service"][f"decode{row['n']}_ns"])
                enc = D(src["common"]["service"][f"encode{row['n']}_ns"])
                rnom = D(48) if coord == "bus" else D(48)+dec
                anom = D(104) if coord == "bus" else D(104)+dec+enc
                inom = D(56) if coord == "bus" else D(56)+enc
                # F39 accepted bound pays a separate endpoint reserve on repair.
                repair = D(56)*xp+(J if row["id"] == "F39" or coord == "bus" else 0)
                write = anom*xp+(2*J if coord == "bus" else J)
                total = ((NR+nr_app)*(rnom*xp+J)+ND*repair+Naw*write+W*(inom*xp+J))/D(10**9)
                c = row["costs"][coord]
                assert close(total,number(c["all_known_upper_s"]))
                assert close(total/T,number(c["average_fraction_upper"]))
                assert close(total,number(c["payload_action_time_s"])+number(c["known_added_protection_excluding_init_s"])+number(c["init_s"]))
            assert number(row["local"]["serial_peak_upper"]) < D("0.8")
            assert number(row["local"]["response_upper_ns"]) < 3000
            assert row["after_first_exceedance_accounted"]
        for coord in ("bus","serial"):
            low = number(src["class_lower"]["costs"][coord]["fixed_class_with_common_lower_s"])
            high = number(result["rows"][1]["costs"][coord]["all_known_upper_s"])
            gap = result["F44_vs_all_F39"][coord]
            assert low > high and close(low-high,number(gap["strict_extra_price_budget_s"]))
            assert D(gap["issued_strict_cap_seconds_down"]) <= low-high
            assert D(gap["issued_strict_cap_us_per_s_down"]) <= (low-high)/T*10**6
        env = src["map_inputs"]["environment"]
        b, Fs, ref = D(env["b"]), D(env["Fs"]), D(env["reference_positions"])
        pulse_count, width = D(env["template"]["count"]), D(env["template"]["width_s"])
        amplitude = 2*Fs/(pulse_count*width)
        s1 = b*T+Fs
        s2 = b*b*T+2*b*Fs+pulse_count*width*amplitude**2/3
        pairs = W*39*38/2
        dapp = D(src["map_inputs"]["service"]["app_deadline_ns"])/D(10**9)
        H = ((D("0.001")-number(g["delta0"]))/pairs-2*(b+amplitude)/ref*dapp*s1/ref)/(s2/ref**2)
        assert close(H,number(result["off_update"]["H_app1_s"]))
        assert H < number(result["off_update"]["P_app_s"])
        region = result["joint_F44_region"]
        for key,value in region["issued_codec_coefficients_up_s_per_ns"].items():
            assert number(value) >= number(region["codec_price_seconds_per_extra_ns"][key])
        assert len(result["rows"]) == 3
    return {"status":"PASS", "method":"separate 100-digit Decimal totals, counts, lower-minus-upper and H_app", "independent_scientific_review":False}
