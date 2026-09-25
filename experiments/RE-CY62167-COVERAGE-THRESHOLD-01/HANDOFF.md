# HANDOFF Orchestrator — численная поставка для Scientific Review

RE-CY62167-COVERAGE-THRESHOLD-01, Issue №15, 2026-09-15.
Постановка: 64a7a1f436b2abd6997d37d14e6ce571e3a480c8.
Уточнение: 7971484c4d054f521cc0086e2df6d4d0f63ed7b7.
История c8ee76b/fa3a550/e7a4c727 и фактическое авторство сохранены.
Exact source delivery и publication SHA разделены во внешней передаче /
PUBLISHED_DELIVERY.json; Git bundle сохраняет исходные локальные Git-объекты.

**Результат для неизменного среза 24h/10mm/main_loglog/central_mean/DREG/tau=1s:**

    I1 = 0.00015554758614445987634181976318359375
    I2 ≈ 1.1913844740529997964e-12 s^-1
    U(Delta) = min(1,a_upper+b_upper*Delta)
    a_upper = 0.0003098157772336203819978391463469440873
    b_upper = 2528.1037181797039690725 s^-1
    s(Delta) = 0.001-U(Delta)

**Достаточно** в declared registered data-only модели при
0<=Delta<=Delta_star≈273.0047101324 ns. Точная threshold-дробь и безопасное
округление вниз — recovery/outputs/cw_bounds.json. Для переноса нужны отдельное
сопряжение вне V и 0<=P(V)<=delta_cov_upper<=s(Delta). Например, при
условном Delta=100 ns требуется coverage upper<=0.0004373738509484092210949108536530559127.
При Delta=1 microsecond остаток отрицателен (-0.00183791949541332435…):
эта upper **недостаточна**, физическая невозможность не утверждается.

Существующих физических сведений **недостаточно** для такого upper.
Принятие конкретной физической Fixed **не установлено**; WCET не измерен.
Приоритет — количественный контракт неохваченных E_cap-релевантных путей
полного data+parity слова с parent/registration/post-W связью и вероятностью
её нарушения. Один дополнительный замер не объявляется решением всех пробелов.

Восстановлен transport по неизменённому historical entry point: 192 points,
depth48/survival128. Новый NPZ SHA:
7f006d49c4e469b624db62b84925571c40f0602cfbd0f3b333211521dad60f9e.
Он не совпал с историческим; причина без старых байтов не установлена.
Продолжение — разрешённое source-based reproduction, не historical byte identity.
Selected CSV: 288 строк, SHA
13daa667dcdf0931a477ba6994f3213b345c582b4d6b472031a9454705a60cf8.
NPZ и CSV включены реальными байтами.

Проверки: 21 historical shielding tests; 13 transport gates;
upstream regression по 288 точкам max rel 4.55157e-8 <1e-6;
38 независимых RE checks — прошли. Интегралы подтверждены Decimal/Inexact,
округление наружу, boundary/normalization/missing-input mutations проверены.
Это не назначенный Scientific Review. Environment/serialization failures
сохранены; thresholds и historical science sources не менялись.

Pre-execution: transport 037b9c91f939962a4ca5bb363cda485e89c86b20;
transport-run HEAD 63fbe46c10c41dce24477ab43f7916eb93aa448e;
numerical 9945f3205f6d13b9b378a4e24b8a1efa2c057e94 с pre-run probes
a50952c801901341e0af7f45cf3d652dd1167e68.
Первый rate run при 38ae8a7bcfbc8ee4b1f4b8fb36daf5b4f899cecd.
Фиксации локальные; retrospective publication не является временной аттестацией.

Готово для отдельного Scientific Review: source-based recovery/regression,
DREG/time/нормировка, новая достаточная численная CW upper, независимые проверки
и предел физического переноса. Closed SR-03 proof/executor не переоткрывался;
4096 traces не повторялись. Scientific PASS/RES не присвоены; Issue №15 открыт,
full-device bridge не объявлен завершённым.
