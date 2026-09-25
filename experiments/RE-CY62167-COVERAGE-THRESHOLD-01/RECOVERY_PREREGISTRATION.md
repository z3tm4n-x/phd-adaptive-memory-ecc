# Предварительная фиксация разрешённого восстановления

2026-09-15. Дополнительный вход Orchestrator: 7971484c4d054f521cc0086e2df6d4d0f63ed7b7.
История c8ee76b → fa3a550 → e7a4c727 сохраняется. Предыдущая остановка и её
реальные причины не переписываются. Настоящий документ разрешает только объём
уточнения; собственный источник prepare_recovery.py извлекает исторические
Git blobs, не исполняет научные функции. Авторство historical/ принадлежит
прежним RE/RADAR; эта сессия создаёт orchestration и проверки.

Фиксируем до исполнения transport: точный RADAR b032505d4d1b15403b8ad06aef578339f6d1c6b4,
четыре PhD input blob из 96e6d724e8c8d79c63c91a00b753e6d4b1796c92,
их materialized-копии, source_manifest и run_transport.py. Entry point только
historical/radar_converged.py, без изменения исходников и критериев selector.
Ожидаются n=192, geomspace(0.11,390), shields=[0,1,2,3,5,7,10], production
depth_steps=48, survival_steps=128, прямые grid/depth convergence <=0.005.
Три исторических shielding test-файла выполняются снова, старый PASS не наследуется.

Дополнительный контроль: shape primary/secondary=(7,192,192), float64,
finite, nonnegative; 0-mm primary identity и secondary zero <=1e-14;
monoenergetic peak error <= exp(log(390/.11)/191)-1 (один энергетический bin).
Нормализации фиксируются без изменений исходника, в том числе нулевая nuclear
коррекция выше TENDL support и добавленный нулевой range endpoint. Проверяем
historical SHA NPZ af35f22ed333150e5ac46df951989811efdef31ee8e9c517f121e5f0853c9cb6,
JSON c7b01f28d8fd395f62be32b54413d5e38c461d2e18aa779321ea03f6eea3f772.
Несовпадение сохраняется с новой идентичностью; причина по hash не угадывается.

Перед DREG/risk обязателен отдельный pre-execution lock исходников selected
recovery, независимой regression и интегралов. Уже сейчас критерий regression:
все 288 upstream central_mean/main_loglog/10-mm значений совпадают с frozen CSV
в пределах 1e-6 relative, без повышения допуска. Для reference=0 требуется
computed=0; для любого положительного reference, включая малые значения,
используется тот же relative tolerance (без additive floor).

Новый NPZ и selected CSV входят в долговременную поставку реальными байтами.
Восстановление по source не делает transport физической верхней огибающей.
Python 3.12 и реальные package versions фиксируются; полное совпадение с
исторической средой не заявляется. Никаких новых risk/MC сеток или transport моделей.
