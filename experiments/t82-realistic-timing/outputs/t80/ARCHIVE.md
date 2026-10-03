# Полная таблица T80

Таблица сохранена без потери строк в последовательных бинарных частях
`full_grid.csv.xz.part00` … `part06`: ограничение размера одной загрузки.
Контрольные суммы частей и полного XZ — `full_grid_manifest.json`.
Это упаковка готового результата; численный код и протокол не изменены.

Из корня репозитория восстановить опубликованную таблицу:

```bash
python - <<'PYCODE'
from pathlib import Path
import hashlib, json
p = Path("experiments/t82-realistic-timing/outputs/t80")
m = json.loads((p / "full_grid_manifest.json").read_text())
chunks = []
for item in m["parts"]:
    b = (p / item["file"]).read_bytes()
    assert len(b) == item["bytes"]
    assert hashlib.sha256(b).hexdigest() == item["sha256"]
    chunks.append(b)
b = b"".join(chunks)
assert len(b) == m["bytes"]
assert hashlib.sha256(b).hexdigest() == m["sha256"]
(p / m["file"]).write_bytes(b)
PYCODE
```

Обычная команда `run_t80.py` заново вычисляет этот полный файл напрямую.
Части — транспортная упаковка, для вычисления не нужны.
