# RE → Research Orchestrator

- Task: RE-INTERNAL-COUNT-ENGINEERING-EXAMPLE-01.
- Base: `7b83f643efb37541547d7d93a65ba2f43acd43fd`.
- Destination branch: `research/internal-count-engineering-example-01`.
- Exact delivery: commit, содержащий этот файл (`git rev-parse HEAD` в
  поставленной версии); точный SHA передаётся пользователю после commit/push.
- Status: **UNFINISHED / DECISION REQUIRED — прикладное основание воздействия**.
- Report: [REPORT.md](REPORT.md); conditional transfer: [applicability.md](applicability.md).

Поставлены не результаты пяти политик, а адресные проверки полного слова
и техническое основание необходимого переноса. 8 unit tests; 1 404 single,
26 676 double, 6 084 trace cases. Data-only count mutant отвергнут;
нулевая задержка как молчаливое приближение опровергнута свидетелем.
Новые production/pilot trials: 0; preregistration не завершена.

Требуется решение о допустимости controlled fault-injection основания
либо конкретный проверяемый радиационный input/основание его диапазона.
Почему это меняет главный вывод и минимальный состав входа — REPORT.
Отсутствие такого входа не доказывает невозможности метода или отсутствия
источников. Не предлагать принимать пакет как завершённый пример статьи.

Независимость: integer syndrome executor против set-oracle; общие fixtures
и семантика перечислены в applicability. Ни один checker не вызывает
прежние production mapping/state/filter helpers. Это локальная проверка,
не независимая валидация пока не существующего полного эксперимента.

Воспроизводимость: `REPRODUCE.md`, `checks.json`, `sources.json`.
Максимально допустимое утверждение: для явно заданного SECDED(39,32)
проверены необходимые count/state свойства, предъявлена цена пропуска
write-delay в виде контрпримера; прикладной эффект RES-003 не установлен.
Опровергать задел следует несовпадающей count/trace позицией или нарушением
условий сопряжения, а не статистикой старого data-only пакета.

Ни RES, ни DEC, ни рукописи, ни main/Issue №15 не изменяются. Старые файлы
сохранены. RADAR/другие исполнители не запускались. Reviewer не запущен,
научный acceptance не присвоен. Публикуется задел для разрешения входной
развилки, не назначается автоматический micro-repair/re-review цикл.
