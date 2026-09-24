# Воспроизведение адресной входной проверки

Пакет не требует RADAR, Numba, h5py, сырых trial archives или новых прогонов
политик. Все используемые численные строки находятся в `source_rows.json`.
PDF нужны для независимой сверки транскрипции, а не скрыто в расчётном пути.
Публичные URLs/версии/SHA-256 перечислены в `sources.json`; контроль локальных
копий опционален. Закрытый/недоступный документ не обходить.

Из корня репозитория после checkout опубликованного commit:

```powershell
python -m venv .venv-input
.venv-input/Scripts/python.exe -m pip install numpy==2.3.5 scipy==1.18.1
$env:PYTHONIOENCODING='utf-8'
$env:PYTHONDONTWRITEBYTECODE='1'
$p='experiments/RE-INTERNAL-COUNT-ENGINEERING-EXAMPLE-01/continuation-01'
.venv-input/Scripts/python.exe "$p/verify.py"
```

Для явной регенерации одного детерминированного output и повторной проверки:

```powershell
.venv-input/Scripts/python.exe "$p/audit.py"
.venv-input/Scripts/python.exe "$p/verify.py"
```

Для сверки скачанных PDF (имена в manifest):

```powershell
.venv-input/Scripts/python.exe "$p/verify.py" --source-dir C:/path/to/source-cache
```

`verify.py` по умолчанию не переписывает опубликованный `verification.json`.
Для отдельного reviewer run можно добавить `--record C:/path/to/new-checks.json`.
Не запускать родительский `run_checks.py`: он переписывает исторический
`checks.json`, что этому продолжению не нужно.

## Фактическое исполнение

Python 3.12.14; NumPy 2.3.5; SciPy 1.18.1; Windows 11 build 26200.
Использован уже существующий локальный venv `../tmp/goes16-venv/Scripts/python.exe`;
его название не означает использование GOES-данных/пакета.
Для чтения PDF использован pypdf из bundled runtime, для таблиц — Poppler
rendering и визуальная сверка. Основные расчёты не используют PDF parser.

Последний записанный полный check: **9.55 s**, 8 новых + 8 прежних unit tests,
compileall обеих директорий — exit 0, детерминированный JSON воспроизведён
точно, хэши шести скачанных PDF совпали. Полные stdout/stderr/argv и хэши
кода/входов/output находятся в `verification.json`.
Крупных/raw outputs нет. Пиковая RAM не профилировалась; этот расход
проверяющей программы не является online-стоимостью контроллера.

Первая версия byte-check отметила старый `checks.json`: локально CRLF,
в Git LF. Содержимое идентично после единственной нормализации CRLF→LF,
canonical blob не менялся; старый файл не переписывался. Проверка теперь
явно сохраняет оба хэша и оба вида сравнения. Десять прежних CSV в Git status
также сохранены, их raw bytes совпадают с базой; они не входят в commit.
Ни одного scientific output старого пакета не пересчитано/подменено.
Генерация новых JSON явно использует LF, чтобы не терять хэши при commit.

## Независимая проверка и пределы

Основной путь `audit.py`: аналитический генератор по числу грязных слов,
SciPy expm. Независимый `independent_check.py`: явные позиции ошибок,
перебор физических marks и Poisson uniformization; не импортирует audit.
Общие только модельная семантика и fixtures. 24 малых комбинации проверяют
редукцию; 4×39 witness рассчитывается малым редуцированным генератором,
не полномасштабным 40⁴-перебором. Абсолютный допуск 2e-13 плюс Poisson tail.
Нормировка независимо пересчитана рационально, zero-count upper — Decimal
с 50 цифрами. Это независимость вычислительных путей, не независимый SR.

Мутация singleton вместо paired-parent при тех же per-word rates отвергнута
word/bit oracle. Тесты также не допускают 32 вместо 39 и zero count → zero upper.
Транскрипция таблицы — общий ручной вход: её опровержение требует визуальной
сверки исходного PDF. Tests сами не доказывают верность опубликованной физики,
полноту регистрации групп или достаточность физического переноса.

Output `diagnostics.json` SHA-256:
`fff90d49f4a0a58554eb58557ef83ad968103249a30d35b8ed088db83551e816`.
При другой версии math/SciPy побитовое тождество не обещается: сначала
сравнить численные отклонения с указанным допуском; входы не подгонять.
