# Первичные источники и нерешённые оговорки

Проверены 01.10.2026. Основной вход — [официальная страница NCEI SEISS](https://www.ncei.noaa.gov/products/goes-r-space-environment-in-situ).
URL каждого NetCDF и SHA-256 фактически использованных байтов —
`outputs/source_manifest.json`; все шесть ежедневных архивов —
`https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes{16,18,19}/l2/data/sgps-l2-avg{1,5}m/`.
Это схема адресов, не обещание наличия всех лет у каждого прибора.

1. [Специальный сентябрь 2017](https://www.ngdc.noaa.gov/stp/space-weather/satellite-data/satellite-systems/goesr/solar_proton_events/sgps_sep2017_event_data/)
   и [readme](https://www.ngdc.noaa.gov/stp/space-weather/satellite-data/satellite-systems/goesr/solar_proton_events/sgps_sep2017_event_data/sgps_sep2017_event_data_readme.txt).
   Отдельный переобработанный **пятиминутный** месяц исправляет известные
   проблемы +X P5/P7 и температурные эффекты. Это основание включить данные
   2017, несмотря на отсутствие их в обычном ежедневном L2 архиве. Минутного
   аналога в этом каталоге не найдено. Для него не переносится вслепую запрет
   использования неисправленного L1b P7 из старого maturity readme.
2. [GOES-16 SGPS provisional readme, 11.07.2018](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes16/l1b/docs/GOES-16_SEISS_SGPS_L1b_Provisional_Maturity_ReadMe.pdf).
   Ориентация, различия E/W, температурные ступени, фон каналов, калибровочные
   ограничения. Упомянутые будущие L2-исправления нельзя считать доказанными
   для каждого файла без его происхождения/метаданных.
3. [GOES-18 SGPS provisional readme](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes18/l1b/docs/GOES-18_SEISS_SGPS_L1b_Provisional_Maturity_ReadMe.pdf).
   Начальная квалификация T3 на ограниченных событиях, температурная
   зависимость +X T3, электронное загрязнение P5, неверная трактовка
   межвспышечного P1–P9 как чистого ГКЛ.
4. [GOES-19 SGPS provisional readme](https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes/goes19/l1b/docs/GOES-19_SEISS_SGPS_L1b_Provisional_Maturity_ReadMe.pdf).
   Квалификация 06.12.2024; P8C может быть завышен примерно вдвое в
   октябре–ноябре 2024; тестирование коррекции загрязнения P7/P8C до
   02.04.2025 давало ступени порядка двух. В screened/strict эти каналы до
   03.04.2025 исключены, а в reported видны для диагностики.
   Здесь же опубликованы поправки 2024 к P1–P5 для всех блоков; документ
   не доказывает, что каждый исторический L2 уже содержит их.
5. [GOES-R PUG, volume 4](https://www.ospo.noaa.gov/resources/documents/PUG/GS%20Series%20416-R-PUG-GRB-0348%20Vol%204%20Rev%202.3.pdf), §7.5.4:
   различать пороги dead-time, out-of-band и относительной динамической
   ошибки. Последний сам по себе не является насыщением. Подробные
   агрегированные определения считываются из каждого NetCDF.
6. [NOAA/CIRES пример чтения SEISS](https://cires-stp.github.io/goesr-spwx-examples/examples/seiss/seiss_example.html)
   и [Unidata C API](https://docs.unidata.ucar.edu/netcdf-c/current/group__datasets.html).
   `nc_reader.py` читает стандартным NetCDF API; установленный в среде
   экземпляр библиотеки VTK используется без установки новых зависимостей.

Не отправляемые внешним адресатам вопросы для автора:

- Подтвердить у NOAA, соответствует ли значение `ExpectedLUTNotFound=0`
  в ежедневных старых SGPS описанию «1 = все LUT совпали» либо это ошибка
  метаданных; указать затронутые версии и рекомендуемую маску. Нужен ответ
  по **версиям/датам**, а не разрешение игнорировать все флаги.
- Нужны ли дополнительная температурная/геометрическая коррекция E/W и
  маска насыщения именно для использованных L2; сохраняются ли caveats
  provisional L1b после данной версии L2? Уточнить обработку P7/P8C G19.
- Каков контракт оперативной выдачи 1-min продукта: конец усреднения,
  максимальная задержка, пропуски/переключение датчиков/исправления задним
  числом? Архивный продукт сам такого контракта не предоставляет.
- Для физического Λ: совместно покрывающие область/срок/вероятность
  границы пика, флюенса и роста спектра за защитой; предел роста между
  минутными бинами. COSRAD/физическую модель не заменяем выборочным
  максимумом GOES. Взаимодействие с COSRAD ведёт автор.

Ранее закреплённые 59 файлов GOES-19 и семь изменённых NOAA файлов из
RE-GOES19-PROTON-RATE-01 не переписываются; T67 использует актуальные
скачанные байты со своими SHA-256, без исторического semantic patch.
