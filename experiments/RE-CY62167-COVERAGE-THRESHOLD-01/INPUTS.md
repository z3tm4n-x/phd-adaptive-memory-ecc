# INPUTS — итоговая поставка

Исходная база: 64a7a1f436b2abd6997d37d14e6ce571e3a480c8.
Дополнительный вход: 7971484c4d054f521cc0086e2df6d4d0f63ed7b7.
**Прежний вычислительный блокер устранён разрешённым source-based восстановлением.**
Исторические SHA ниже сохранены для сравнения, а не как идентичности новых байтов.

| Артефакт | Состояние / SHA-256 |
| --- | --- |
| Historical full direct_rate_5min.csv | Недоступен; c10a68e721716c8c9b96bf99a9e2d1de0bd3b179ebcc747b3fd149ff0741ff83; 53420841 bytes / 237888 data rows |
| Historical radar_transport.npz | Expired Actions artifact; af35f22ed333150e5ac46df951989811efdef31ee8e9c517f121e5f0853c9cb6 |
| New recovery/outputs/radar_transport.npz | 296715 bytes; 7f006d49c4e469b624db62b84925571c40f0602cfbd0f3b333211521dad60f9e |
| New selected_rate.csv | 44436 bytes / 288 data rows; 13daa667dcdf0931a477ba6994f3213b345c582b4d6b472031a9454705a60cf8 |
| Frozen goes010226.zip | 5969999 bytes; 7b5e2f62e8a3b235ae1956505742253bb7d7633dfaa4be6e0350e37e5d8ab581 |
| Frozen registered_direct_by_energy.csv | 1473 bytes; 74e0fac4bb0847625b50bdf1aef7cd2215a881f471529953dbc72e8eeddc1ff2 |
| Frozen upstream proton_rate_5min.csv | 13002858 bytes; 9f8a43a00780a0853db6e4a03263eb87672065be5a93edfcc79f544c78f7593d; regression reference only |

Frozen GOES archive найден в сохранённой поставке. В этой сессии копия:
`/workspace/scratch/adf34e406362/inputs/goes010226.zip`.
Путь временный и не заменяет identity. Для нового восстановления передаётся
путь к exact-SHA архиву. Selected NetCDF members:
- sci_sgps-l2-avg5m_g19_d20260119_v3-0-3.nc:
  ac282f4e96f903f0c0ffa6f11a25f6b8463af0d13f68e69246301b0f7332fcce.
- sci_sgps-l2-avg5m_g19_d20260120_v3-0-3.nc:
  56c88dbd07005617e69571d6e26c00217d799eeb7396768dab88257423470d3a.

Все 59 members сверены с frozen manifest; source member SHA сохранены в
recovery/outputs/selected_recovery.json. Полный архив требуется прежнему
fallback-median правилу, rates вычисляются только внутри H.
Публичные пересмотренные NOAA bytes не подставлены.

Четыре transport входа из PhD 96e6d724e8c8d79c63c91a00b753e6d4b1796c92:
radar_converged.py blob3302ab0648988a42f6a1892f52f844f20aee22b9;
radar_adapter.py blob8e706e5f2475542f1a6b7fd31e96df9752aa1f42;
sigma_model.py blob7988bea35dbcb106d4b178deb7dab2c7df03862a;
sigma_bit_experimental.csv blob624c3e50526a6c9dbf5d534e6d600c56802df036.
Точные копии и остальные source identities — recovery/source_manifest.json.

RADAR code/data из точного b032505d4d1b15403b8ad06aef578339f6d1c6b4.
Новая NPZ identity не совпала с исторической; старых байтов для сравнения массивов
нет. Source-based continuation разрешено addendum, подтверждено gates и upstream
regression. Никакого утверждения historical full-byte recovery нет.

Для CW и независимых проверок достаточно committed selected_rate.csv,
selected_energy_contributions.npz и cw_bounds.json: transport пересчитывать
не требуется. Для отдельной проверки восстановления нужны frozen upstream-источники.
Исходные raw CY для этой работы не нужны и заново не разбирались.
