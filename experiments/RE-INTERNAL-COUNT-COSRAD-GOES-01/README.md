# RE-INTERNAL-COUNT-COSRAD-GOES-01 — поставка A

Начать с **COSRAD_REQUEST.md**. Научный и временной контракт — **MODEL_AND_INPUTS.md**. Краткий результат и точная граница исполнения — **HANDOFF.md**.

Численные функции в `inputs/`, машинные конфигурации в `config/`, происхождение в `provenance/`, проверяющий код в `src/` и `tests/`, результаты выполненных проверок в `outputs/`. **Новых COSRAD/GOES policy results здесь нет.**

Команды повторения — `REPRODUCE.md`. Поставка публикуется в ветке `research/internal-count-cosrad-goes-01`, только в `experiments/RE-INTERNAL-COUNT-COSRAD-GOES-01/`. Научная база: `0715fd8e17b59a71d731110c53b87b900f8fa304`; сохранённые предшествующие коммиты ветки не переписываются.

Статус публикации и различия с исходным файловым пакетом: **PUBLICATION.md**. Запись об отсутствии публикации в исходном HANDOFF относится к моменту выпуска ZIP, а не к текущей GitHub-поставке.

Ранее опубликованный `inputs/proton_anchors.csv` сохранён как исторический вход, но **не используется** генератором этой поставки. Действующие опоры — `proton_repository_points.csv` и `proton_supplementary_points.csv`; порядок их использования задан в `src/prepare_inputs.py`. Никакой подмены численных данных исходного ZIP при публикации не производится.
