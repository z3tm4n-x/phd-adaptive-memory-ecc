# Воспроизведение предварительных проверок

Из корня checkout этой ветки, Python 3.12+; только стандартная библиотека:

```powershell
$env:PYTHONDONTWRITEBYTECODE = '1'
python experiments/RE-INTERNAL-COUNT-ENGINEERING-EXAMPLE-01/run_checks.py
python -m unittest discover -s experiments/RE-INTERNAL-COUNT-ENGINEERING-EXAMPLE-01 -p 'test_*.py' -v
python -m compileall -b -q experiments/RE-INTERNAL-COUNT-ENGINEERING-EXAMPLE-01
```

Ожидается 8 успешных тестов. Первый шаг заново создаёт `checks.json`:
время, OS и checkout-EOL сведения могут отличаться; научные детерминированные
счётчики должны совпадать. Обычный запуск занимает несколько секунд.
Локально Python 3.12.14; зависимости h5py/numba/RADAR не нужны.
Compileall может создавать только Python cache; удаление файлов не требуется.
Проверено: compileall с `-b` завершился с кодом 0. Первая попытка с
отдельным `pycache_prefix` не прошла из-за длины вложенного Windows-пути
(`FileNotFoundError` для cache), после изменения места cache компиляция
успешна; исходный Python-код для этого не изменялся.

Проверки не генерируют потоков и не запускают сравнение политик.
Мониторинг максимальной памяти не выполнялся; аппаратная стоимость из
локального времени тестов не выводится. Перечисление ошибок использует
одну 39-разрядную маску; fixture потоки не хранят большой trial dataset.

В Windows checkout десять старых CSV отмечались Git как modified из-за
несогласованного CRLF/text атрибута. `checks.json` сравнивает их **сырые
байты** с base: все byte-identical. Они не переписаны/не включены в commit.
Чистота собственного изменения проверяется списком файлов commit, а не
скрытием этих записей через assume-unchanged.

Для проверки внешних первоисточников скачать два URL из `sources.json`
и сопоставить SHA-256. Локальный путь автора не нужен. Эти документы
не требуются для выполнения tests и не включены в Git как сторонние PDF.
