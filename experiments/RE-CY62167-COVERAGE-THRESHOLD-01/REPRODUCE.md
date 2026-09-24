# Воспроизведение и сохранность

Все команды из корня PhD репозитория. Активные config/источники перечислены
в REPORT; прежние extract_selected_rate.py / compute_bounds.py /
independent_check.py отключены и являются историей ошибки, не этими командами.

Быстрая проверка численной поставки по сохранённому срезу:

```bash
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/cw_calculate.py calculate --input experiments/RE-CY62167-COVERAGE-THRESHOLD-01/selected_rate.csv --output /absolute/path/cw_bounds_recheck.json
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/independent_validation.py
```

Второй checker сохраняет новый independent_validation.json; для SR исполнять
в отдельной копии, сохраняя исходные опубликованные bytes. Исходный checker
не импортирует главный калькулятор. Проверены 38 assertions/checks; это RE QA,
не независимый назначенный Scientific Review.

Полное ограниченное воспроизведение с внешним exact-SHA GOES archive и
RADAR checkout на b032505d4d1b15403b8ad06aef578339f6d1c6b4:

```bash
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/run_transport.py --radar-root /absolute/path/RADAR
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/upstream_regression.py --archive /absolute/path/goes010226.zip --repo .
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/selected_recovery.py --archive /absolute/path/goes010226.zip --repo .
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/cw_calculate.py calculate --input experiments/RE-CY62167-COVERAGE-THRESHOLD-01/selected_rate.csv --output experiments/RE-CY62167-COVERAGE-THRESHOLD-01/recovery/outputs/cw_bounds.json
python3 -B experiments/RE-CY62167-COVERAGE-THRESHOLD-01/independent_validation.py
```

В этой сессии h5py 3.14.0 и pytest 8.4.2 установлены в task-specific directory
и предоставлялись через PYTHONPATH=/workspace/scratch/adf34e406362/recovery-deps.
Остальные фактические версии: Python3.12.14 / NumPy2.3.5 / SciPy1.17.0 /
pandas2.2.3 / pydantic2.13.5. Историческая среда не полностью зафиксирована;
совпадение runtime не заявляется. Для готового NPZ run_transport --validate-only
повторяет только checks, без нового transport. Два исторических failure JSON
содержат реальные причины/исправления; это не скрытые успешные исполнения.

Transport wrapper сохраняет stdout historical entry point, 21-test log, среду,
матрицу/validation и независимый qualification. Полная scientific pipeline/MC
не вызывается. Первичный transport исполнялся один раз; последующий validate-only
исправил JSON serialization NumPy bool, не матрицу/пороги.

MANIFEST.json содержит размеры, SHA-256 и Git blob IDs файлов source delivery,
кроме самого MANIFEST.json. Self identity задаётся source Git commit. Публикационный
контейнер PUBLISHED_DELIVERY.json и delivery.bundle создаются после source commit
и описываются отдельно, чтобы не создавать циклические самохеши.

GitHub snapshot и source delivery имеют разные SHA. Авторизованный connector
не принимает author/time исходных commits; он используется для публикации
byte-identical файлов и bundle. Bundle сохраняет исходные Git-объекты и родителей,
включая e7a4c727…, без пересоздания их SHA. PUBLISHED_DELIVERY.json содержит
source_delivery_sha, bundle SHA-256, prerequisites и mirror semantics.

В копии репозитория с доступным prerequisite 64a7a1f… восстановление истории:

```bash
git bundle verify experiments/RE-CY62167-COVERAGE-THRESHOLD-01/delivery.bundle
git fetch experiments/RE-CY62167-COVERAGE-THRESHOLD-01/delivery.bundle refs/heads/research/cy62167-coverage-threshold-01
git checkout --detach FETCH_HEAD
```

Последняя команда предназначена для отдельной reviewer-копии. Она не меняет main
и не требует force-push. Published snapshot уже содержит NPZ/selected CSV;
bundle дополнительно обеспечивает исходную историю. После публикации проверяются
exact remote HEAD и все bytes опубликованных файлов, включая оба NPZ и bundle.

Первоначально старые CSV в рабочем clone отображались изменёнными из-за CRLF
normalization. Они не редактировались/не индексировались. В source commits только
experiments/RE-CY62167-COVERAGE-THRESHOLD-01/. Локальная .gitattributes сохраняет
точные historical CSV bytes в собственном каталоге.
