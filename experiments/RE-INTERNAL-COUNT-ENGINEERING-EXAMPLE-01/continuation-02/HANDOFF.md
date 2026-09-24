# HANDOFF — ISSI grouped validation

**From:** Research Engineer (Local). **To:** Research Orchestrator; отдельному Scientific Reviewer после решения Orchestrator.  
**Task:** RE-INTERNAL-COUNT-ENGINEERING-EXAMPLE-01 / continuation-02.  
**Related:** RES-003; RQ-003/004/005/007; положения3 и1/4 DEC-004.  
**Инженерный исход:** **B, законченный смешанный результат**, с явной чувствительностью к реконструкции. PASS/RES не назначены; Reviewer не запускался.

## Идентичность

- Scientific code/results/report commit: **4979ee554fe67796ec5970ad61b41868b9864b59**.
- Его parent и фактический test execution commit: **8ed0035d8b75b43733d9dcce4473835031d21f49**.
- Опубликованная до прогонов preregistration: **c09928f2ad0e483539426ec2c0d20e84adbb3d86**.
- Исходная база/ancestry: **268e0d772aa718226ce7d3c2c18ded96306bdcf2**, далее44b3d599… сохранены.
- Ветка: **research/internal-count-engineering-example-01**. Этот завершающий документ добавляется отдельным documentation-only commit поверх4979ee55…; его SHA возвращается пользователю после push и проверки remote. Научные outputs находятся уже в указанном точном scientific commit.
- Main при проверке старта:7b83f643efb37541547d7d93a65ba2f43acd43fd. Main, DEC/RES, Issue15, manuscripts и прежние пакеты не изменялись.

## Ответ и предел применения

| Случай | Proposed F̂, family-adjusted interval | Основной вывод |
|---|---|---|
| Main XOR groups | .08280 [.07648;.08944] | Вместе с count-disabled удовлетворяетε=.1; G_J=23.36% [23.11;23.61], J17832 |
| Singleton ablation | .08400 [.07764;.09068] | G_J против disabled22.95% [22.70;23.20]; против Fixed1 с только4.96% [4.65;5.28], ниже10% |
| Native-word merged | .80915 [.79980;.81826] | Все5 политик нарушаютε; эффект survivors не делает режим допустимым |

Главная парная ΔF=+.00135 [−.00662;+.00932]; ноль внутри не доказывает равенство. В основном случае относительно выбранного Precomputed=.5/1 с G_J=36.94% [36.73;37.14], но ΔF=+.01245 [.00533;.01955]: компромисс, а не Pareto-domination. Все неблагоприятные исходы, PA-DOM и остальные pairs сохранены в REPORT/CSV.

**Сильный простой comparator ограничен процедурой настройки.** В main Fixed=.5 с прошёл заранее заданный отбор; Fixed1 с имел tuning upper95=.10438 и не прошёл, но не исключён как физически/статистически недопустимый. Оптимум класса не доказан. В singleton выбран1 с, test interval [.08749;.10122] пересекаетε. Нельзя интерпретировать разницу этих настроек как доказательство, что сами группы создают большой выигрыш над оптимальным Fixed.

Цена Proposed:2,784,048 bytes таблиц (2.655 MiB), q208 bytes+скаляры, до676 coefficient multiply-adds/update и12 candidates. Хранение отдельно защищено по условию. Против main Precomputed общая surviving-экономия≈52.29 s/mission,≈2.905 процентного пункта прикладной ёмкости интерфейса; нижняя экономия допускает≈30.54 ms extra cost/update при описательном среднем числе updates. Минимальный причинный idle deadline95.1424 ms. Host≈5.99µs/update — **не WCET**. Полная стоимость/энергия/аппаратная квалификация не установлены. Положительное применение требует соблюдения этих условий; таблицы больше полезных2 MiB буфера.

## Входы и предпосылки

Архив RADECS2025, DOI10.5281/zenodo.17500462, SHA2567c4e05968a8e0adc9733a3ba706a8ed2f751e53162b80b9746c1b8c4ccdb2e88;60 static3.3V14MeV neutron tests. Независимо восстановлены55353 bits/44364 XOR groups, exact equality со всеми60 авторскими group logs. Native merge даёт44355 groups с теми же raw masks, но **не** ту же XOR-гистограмму и не доказанно тот же observational law.

Условия:3 чипа; W524288;39 protected positions; uniform общие XOR shifts; условно независимые чипы с общей CTMC; high scale из3119.5s exposure, low/high=.1;D60s;H1800s;epsilon=.1;чистое численное начало. Latch→commit80ns;полные маски атомарны;счётчик только acknowledged scrub corrections, включая parity;application reads безwriteback/без этого count. Это объявленный генератор, не восстановленная хронология частиц. Наибольшая empirical multiplicity23 не физический предел.

Reference internal backup potential=.06114977424118347, delta=.00033146425961188614, slack=.03851876149920464. SR arithmetic guard пересчитан, а не заимствован более выгодный tally. Reference bound не переносится на grouped/delayed закон. Ядро фильтра/правило управления не заменены. Model mismatch оценивается симуляцией.

## Проверки и общие зависимости

- 8 legacy tests + 12 new tests; explicit scheduled set-of-bits oracle, 100 фиксированных random streams и boundary/toggle/parity/terminal fixtures.
- Содержательный mutant рассеивает два бита одного слова по двум словам: production на неверном входе safe, независимый oracle правильного physical group отвергает. Также rejected rate/association/parity mutations.
- 100 независимых action-expression comparisons; 2000 fsum posterior checks; блоковая moment ODE; doubled quadrature; generator normalization/mark/immutability tests.
- Все 18000 выбранных tuning baseline trial records пересчитаны final executor: 0 отличий; 6000 hashes совпали.
- Ровно 60000 test streams × 5 policies; 0 computational failures; 199 независимых статистических сравнений, 0 ошибок; compileall exit 0. Никакие failing trials не удалены/fallback не подставлен.

Независимый statistics checker использует binomial-tail bisection и scalar reductions вместо beta-quantile/vector helpers. Общие numpy/scipy и опубликованные trial records раскрыты. Oracle не вызывает production mapping/update helpers, но не является независимым доказательством выбранной физики; accepted controller functions/tables сохранены как общая зависимость. Полная независимая регенерация всех test streams другим симулятором не заявляется.

Риск-интервалы finite-sample binomial/Bonferroni; resource intervals асимптотические Student/delta с той же allocation. Общая процедура не объявлена точной finite-sample95% гарантией. В bootstrap60 тестов, не независимые биты. Native direct-path diagnostic остаётся>.1 даже на показанном нижнем source-count масштабе; main физическая robustness не сертифицирована.

## Доступные результаты и воспроизведение

Scientific package: [REPORT.md](REPORT.md), [PREREGISTRATION.md](PREREGISTRATION.md), [MODEL_AND_COST.md](MODEL_AND_COST.md), [REPRODUCE.md](REPRODUCE.md). Все15 policy rows и12 paired rows доступны как CSV/JSON. Иллюстрация использует только заранее назначенный seed2026091606, никакого выбора удачной траектории.

**Trial-level archives в Git**, суммарно9,113,738 bytes:

| Файл | SHA256 |
|---|---|
| outputs/test_xor_groups.npz | b16ccf6b64f21c7b8391818fb19b579133ed5e7db10760429a05f8013be8b1c7 |
| outputs/test_singleton_ablation.npz | 6b39b46b54f6eb3435a1c63d48e6b7106f250097c84d286016ea24b6e0984f25 |
| outputs/test_native_word_merged.npz | 25944e0f0e8275154899d0fba060a30883cf017714a326c6a343397b2017e36d |

Минимальная независимая статистическая проверка: `python check_results.py` из этого каталога (numpy/scipy; h5py/numba/сыройZIP не нужны). Полные команды построения/тестирования/запуска из корня репозитория — REPRODUCE.md. Numerical Python3.12.14, numpy2.3.5, scipy1.18.1, numba0.67.0/llvmlite0.49.0; extract openpyxl3.1.5. Tuning≈1096s,test≈419s/6workers; RSS snapshots≈1.55GB/1.13GB, не peak guarantee. Большие tuning caches не в Git, но576 полных candidate scores, hashes, paths и exact regeneration опубликованы. Новые test outputs не привязаны к недоступному локальному пути.

## Отклонения и решение Orchestrator

Development corrections, исключённый debug stream, multiprocessing permission failure до trials, metadata fallback и LF-serialization раскрыты в DEVELOPMENT_LOG.md. Модель/seed/N/selection после просмотра test не менялись. После pre-test изменялись только представление/упаковка и эффективность независимого checker, не научные формулы. Десять исходных unrelated CSV worktree markers побайтно равны базе и оставлены нетронутыми; они не включены в commits.

**Максимальная формулировка:** условная ценность собственного счётчика в объявленной grouped-модели и сравнение с заранее настроенными конкурентами; предел цены контроллера; сильная чувствительность решения к parent reconstruction. Не заявлять полный физический перенос, оптимальность против класса Fixed, экономию полной стоимости или универсальную marginal insufficiency.

**Фальсифицирующая проверка:** независимо восстановить masks/group membership и timing; пересчитать пары из NPZ; проверить baseline selection в576 строках; проверить нижний direct-hit аргумент для merged-модели и его предпосылки. Ошибка в этих связях меняет соответствующий вывод. Более сильный достаточный Fixed1 с может существенно уменьшить заявляемый выигрыш против простого режима, не отменяя count-disabled comparison.

Orchestrator требуется выбрать допустимое публикационное утверждение и назначить отдельный SR. Автоматическое принятие/PASS/новыйRES/новыйэксперимент не выполнены и не запрашиваются как продолжение по умолчанию.
