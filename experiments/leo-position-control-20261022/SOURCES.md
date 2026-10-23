# Источники первого LEO-входа

Прочитаны 23.10.2026. Номера PDF — физические страницы, начиная с 1.
URL, SHA256, размеры трёх сохранённых PDF и версии файлов репозитория —
[sources.json](sources.json). SOURCE относится только к явно указанному
факту; предложенная совместная конфигурация остаётся кандидатом.

## Полученный методический путь #196

[PR232@58a5242, §§1/5/6][method] и [минимальный вход][method-input] прочитаны
по точному коммиту после ответа #206/6358641948. Blob зафиксированы в
`external_repo_references` манифеста; файлы не копируются в эту поставку и
не входят в побайтовую проверку `verify.py`. Применим прежний moment/E-верх
к обязательным окнам, детерминированным при фиксированном внешнем пути;
конкретные физические/временные параметры ещё не подписаны. Это авторское
методическое основание, не независимая приёмка всего PR или данной точки.

## Реальное бортовое положение: Reichert / Meehan / Munson

[Toward Decimeter-Level Real-Time Orbit Determination: A Demonstration Using
the SAC-C and CHAMP Spacecraft, ION GPS 2002][gps]. PDF 1, 4–6.

SOURCE: SAC-C, 707 км; BlackJack/RTG работал на борту. PDF 4 различает
измерения 1 Гц и решение каждые 30 с. PDF 4–5: демонстрация 28.09.2002,
около 4.5 ч, первые 30 минут удалены из оценки; ошибки сравниваются с
последующей обработкой. PDF 5–6 описывают сбои сходимости/перезапуски.

UNKNOWN: гарантированная ошибка/возраст за T, доставка до контроллера памяти,
формат/признаки качества интерфейса, длительность восстановления. Выгрузка
решений на Землю не является задержкой бортового доступа. Дециметровый
результат CHAMP с поправками не переносится на SAC-C. Противоречивую дату
запуска в тексте PDF 3 не используем; дата запуска не входит в расчёт.

## ICARE / SRAM: Ecoffet et al.

[Observations of the dynamics of the radiative environment in polar orbit
in the period 11/2000–11/2001][icare-paper]. PDF 2–6.

SOURCE: PDF 5, табл. 1 — KM684000, 512K×8, Samsung, 3.3 В, шесть устройств
на тестовой плате; это не наш проект из двух корпусов. Карта там объединяет
компоненты; табл. 2 сообщает накопленные перевороты битов, не закон родителей
групп. PDF 4 показывает изменение пояса при магнитном возмущении; PDF 6 —
солнечные эффекты вне SAA. Нельзя принять поток вне SAA нулевым.

PDF 2 задаёт конфигурацию монитора: протоны 8–30 МэВ, период 4–512 с;
GPS-время пакетов не доказывает доставку позиции в ECC. Точный suffix/date code,
межкорпусные группы и численные непрерывные профили здесь не установлены.
Высота PDF 3 — 730 км; не превращаем её в погрешность выбранных 707 км.

## Источник существующей модели, а не выполненный перенос

[Duzellier et al., MUSCA SEP3 to investigate the Single Event Effects for
Space Missions, ONERA/CNES, EEE final presentation, 2011][musca]. PDF 5–9.

SOURCE: PDF 5 — SAC-C 707 км, 98.2°, HM628512/KM684000. PDF 6 показывает
связку обратного анализа, наземных данных, MUSCA/OMERE и неоднородной защиты
(3 см / 3 мм); материал и угловая геометрия не заданы пригодным нам массивом.
PDF 9: вариация параметров устройства ±20% — анализ чувствительности, не
вероятностное покрытие среды. UNKNOWN: численный отклик одной ревизии и
защиты, совместные марки по нашему слову. Новое моделирование переноса не
запускалось. Это адресный маршрут к уже существующим данным.

## Орбита, доступ к данным, резерв

- [WMO OSCAR SAC-C][wmo] даёт номинальные 705 км и GOLPE; отличается от
  двух PDF. [Доклад CNES/ONERA 2017][esa-icare] описывает долгую серию ICARE,
  но не является выгруженным рядом экспозиций/UTC/масок.
- [ONERA ICARE][onera], §3.1/§3.5/§4: прибор, примеры карт, выборочная выгрузка
  и буфер. Общие диапазоны 5–45 МэВ / 4–256 с на странице не подменяют
  конфигурацию 8–30 МэВ / 4–512 с в раннем PDF. Полного ответа памяти эти
  диапазоны монитора не дают. [CEOS-COVE policy][policy] указывает SAC-C ICARE
  как Open-AP с запросом периода в CONAE. Запросы людям не отправлены;
  отсутствие файла у нас не означает отсутствие архива.
- Единственная резервная орбита: [ESA PROBA-1 overview][proba] — 681×561 км,
  97.9°. Напечатанное там «96.97 hours» не используем. [ESA Payloads][payload]
  описывает SREM, но не заменяет отклик SRAM.
- [PSI SREM Data][srem]: V0 — счётчики/эфемериды; L1 — восстановленные спектры
  и признаки качества; L2 — дополнительная нормировка к SEPEM/RBSP. Поэтому
  L2 не независимая проверка SEPEM. Quality 0: рекомендовано; 1: осторожность;
  2/3/5: не использовать, background/5 не означает нулевую физическую
  интенсивность. [Покрытие PROBA-1][coverage] показывает и неполные/нулевые
  дни; каталог не подтверждает непрерывность. [Формат][format] — маршрут к
  разбору файла после получения, не уже проверенная временная шкала.

Две адресные попытки PSI: web-open предполагаемого каталога
`https://srem.psi.ch/datarepo/L2/proba1/` не дал файла; HTTPS GET формы
`https://srem.psi.ch/cgibin/srem_data_sec.pl` из локального Python завершился
TLS EOF. При этом сама форма прочитана веб-инструментом. Не установлен отказ
сервиса или требование авторизации; численного файла и его хэша нет.
Не повторяем тот же доступ циклически: следующий шаг — один штатный выбор
периода через форму либо иной опубликованный прямой адрес, затем проверка
эпохи/координат/маски. До этого PROBA — резерв, не обеспеченная рабочая точка.

[gps]: https://gdgps.jpl.nasa.gov/system-desc/papers/Reichert_IONGPS2002.pdf
[icare-paper]: https://swe.ssa.esa.int/TECEES/spweather/workshops/SPW_W3/PROCEEDINGS_W3/SWWorkshop_Ecoffet2.PDF
[musca]: https://escies.org/download/webDocumentFile?id=49249
[wmo]: https://space.oscar.wmo.int/satellites/view/sac_c
[esa-icare]: https://indico.esa.int/event/213/contributions/1899/
[onera]: https://craterre.onera.fr/radiation_monitors/ICARE.html
[policy]: https://ceos-cove.org/en/data_policy/
[proba]: https://www.esa.int/Applications/Observing_the_Earth/Proba-1_overview
[payload]: https://www.esa.int/Applications/Observing_the_Earth/Proba-1/Payloads
[srem]: https://srem.psi.ch/cgibin/srem_data_sec.pl
[coverage]: https://srem.psi.ch/static/proba1_datacoverage.shtml
[format]: https://srem.psi.ch/static/proba1_dataformat.shtml
[method]: https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/58a5242ca56c7f35f5f15e2071de109906aef1f5/theory/t196-priority-methods-20261023.md
[method-input]: https://github.com/z3tm4n-x/phd-adaptive-memory-ecc/blob/58a5242ca56c7f35f5f15e2071de109906aef1f5/experiments/comparison-foundations-20261018/priority-methods-20261023/HANDOFF.md
