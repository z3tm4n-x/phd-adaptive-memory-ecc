# Execution / provenance record — Stage 0

Research Engineer, 2026-09-15 UTC. Документальный аудит и source inspection;
не запуск научной модели или аппаратного исполнителя.

## Среда и источник данных

- Git 2.53.0.windows.1; PowerShell 7.6.5 Core.
- Microsoft Windows 10.0.26200 (Win32NT).
- Рабочая копия: `C:/Users/Иван/.codex/.chatgpt-projects/g-p-6a8f0744f95081919477f597a4962b6b/phd-adaptive-memory-ecc`.
- Source-only clone: соседний `executor-reference`, создан `git clone --no-checkout`.
  HEAD этого clone не является научным входом: читается только cf7ab706.
- Все версии научных источников и SHA256 их точных Git bytes: timing_input_gate.json.
- Python, simulators, Vivado, transport, MC, bound calculator не запускались.
  Исторический Vivado report содержит свою среду; это не runtime текущей сессии.
- Чтение Issue №15 подтвердило state=open. Состояние опубликованного main
  перед поставкой: be6b447e1c2ee7b70e68604fd135b379a800e62f.
- Общее время интерактивной работы и peak memory не измерялись и не выдаются за
  scientific runtime/WCET. Ресурсоёмкого расчёта не было.

## Фактически выполнено

1. Чистая предыдущая ветка проверена; origin fetched; создана назначенная ветка
   непосредственно от be6b447e1c2ee7b70e68604fd135b379a800e62f.
2. Exact handoff/bootstrap/DEC-004/концепция и источники REPORT прочитаны.
   Выполнено чтение исходного RTL, config, OOC report/адресного timing report.
3. Проверены **27/27** source Git blobs, sizes и SHA256 из бинарного вывода
   `git cat-file blob`. Значения не зависят от PowerShell text encoding/CRLF.
   Selected CSV S16: 44436 bytes,
   SHA256 13daa667dcdf0931a477ba6994f3213b345c582b4d6b472031a9454705a60cf8.
4. Проверены точное совпадение переписанного threshold с S15, ancestry
   a8b04eff→be6b447, null для невычисленного upper/comparison, ссылки ID входов.
   Проверка статуса/порога завершена 2026-09-15T19:10:07Z;
   source hashes дополнительно проверены после добавления в JSON.
5. Никаких данных для квалифицированного full backend/start не добавлялось.
   Stage 1 остановлен до реализации. Проверки исходников — инженерная QA,
   не Scientific PASS и не тесты полного timing/start контракта.

## Неуспешные действия и исправление процедуры

- Первое сетевое ls-remote в ограниченной среде не установило соединение.
  Повтор с разрешённым сетевым доступом успешен; main SHA приведён выше.
- Первая совмещённая QA-команда проверила source blobs/sizes и threshold,
  затем ошибочно искала pinned selected_rate.csv в текущем checkout.
  В этой базе файл отсутствует; команда завершилась ошибкой до финальной
  проверки ancestry/status. Процедура исправлена на бинарное чтение exact
  Git object a9d9b74b:path. Последующая проверка успешна. Это ошибка
  пути проверяющего, не изменение CSV и не новый input blocker.
- Первое добавление SHA256 в JSON одним patch с delete/add одного пути
  было отклонено инструментом до изменения файла. Применён обычный update,
  затем все 27 hashes заново сопоставлены. Научные входы не менялись.
- Старые outputs не перегенерировались; отсутствующие аппаратные тесты
  не обозначены как пройденные.

## Особенность checkout: четыре ложные отметки изменений

Сразу после переключения ветки Git показал четыре tracked CSV modified:
их committed CRLF конфликтуют с `*.csv text eol=lf`.
Для каждого `git hash-object --no-filters` дискового файла совпал с base blob.
`git diff --ignore-space-at-eol --stat` пуст. Файлы не правились, не
нормализовались и не включаются в commit. Не заявляется пустой обычный
`git status`; исходные bytes сохранены.

| Старый файл в experiments/RE-CY62167-PAPER-COMPLETION-01/ | Диск = base Git blob |
| --- | --- |
| cosrad_member_manifest.csv | a1d91845a9265998e5adf1aad9159f91704b549c |
| cosrad_operator_closure.csv | e13ee5087e1c97b48d16d3745969dc0c512a491f |
| legacy_article_regression.csv | 43ef4321b12843545919d7529de2a962f00d695a |
| shielding_boundary_summary.csv | 90411f54bb9ab2b90c6f2c9c4ba49bd0845e72c3 |

## Точное повторение входной проверки

PowerShell 7, запуск из PhD repo; соседний executor-reference должен содержать
закреплённый cf7ab706. Сначала получить exact commits без изменения старых
checkout. Нужные commits перечислены в JSON; Git fetch доступных опубликованных
веток или конкретных SHA допустим для чтения.

```powershell
git clone --no-checkout https://github.com/z3tm4n-x/chapter4-risk-limited-scrubber.git ../executor-reference
git merge-base --is-ancestor a8b04eff258401233a1aa038862c71daa4f01072 be6b447e1c2ee7b70e68604fd135b379a800e62f
git show be6b447e1c2ee7b70e68604fd135b379a800e62f:docs/research_gates/RE-CY62167-EXECUTOR-TIMING-GATE-01.md
git -C ../executor-reference show cf7ab706224f7872fdafcf34febda70e3f6c8dd1:rtl/scrubber/scrub_pass_engine.sv
```

Clone команду пропустить, если такая копия уже существует.
Следующий read-only блок проверяет происхождение всех входов, а не вычисляет
временную границу:

```powershell
$ErrorActionPreference='Stop'
$taskGate=Get-Content -Raw 'experiments/RE-CY62167-EXECUTOR-TIMING-GATE-01/timing_input_gate.json' | ConvertFrom-Json
$taskRecords=foreach ($s in $taskGate.sources) {
 $taskRepo=if ($s.repository -eq 'z3tm4n-x/chapter4-risk-limited-scrubber') { (Resolve-Path '../executor-reference').Path } else { (Get-Location).Path }
 $taskBlob=git -C $taskRepo rev-parse ($s.commit+':'+$s.path)
 if ($LASTEXITCODE -ne 0 -or $taskBlob -ne $s.git_blob) { throw ('blob mismatch '+$s.id) }
 $taskInfo=[Diagnostics.ProcessStartInfo]::new('git')
 $taskInfo.WorkingDirectory=$taskRepo
 $taskInfo.UseShellExecute=$false
 $taskInfo.RedirectStandardOutput=$true
 $taskInfo.RedirectStandardError=$true
 $taskInfo.ArgumentList.Add('cat-file')
 $taskInfo.ArgumentList.Add('blob')
 $taskInfo.ArgumentList.Add($s.commit+':'+$s.path)
 $taskProcess=[Diagnostics.Process]::Start($taskInfo)
 $taskBytes=[IO.MemoryStream]::new()
 $taskProcess.StandardOutput.BaseStream.CopyTo($taskBytes)
 $taskError=$taskProcess.StandardError.ReadToEnd()
 $taskProcess.WaitForExit()
 if ($taskProcess.ExitCode -ne 0) { throw $taskError }
 $taskSha=[Convert]::ToHexString([Security.Cryptography.SHA256]::HashData($taskBytes.ToArray())).ToLower()
 if ($taskBytes.Length -ne $s.bytes) { throw ('size mismatch '+$s.id) }
 if ($taskSha -ne $s.sha256) { throw ('source SHA256 mismatch '+$s.id) }
 if ($s.id -eq 'S16' -and $taskSha -ne $taskGate.frozen_numerical_input.selected_rate_sha256) { throw 'pinned CSV SHA256 mismatch' }
 [PSCustomObject]@{id=$s.id;sha256=$taskSha;bytes=$taskBytes.Length}
}
$taskRecords | ConvertTo-Json
```

Успех: 27 записей без исключений; включая blob/size/SHA256 S16.
Численный threshold проверяется только как переписанный input:

```powershell
$taskFixed = git show a9d9b74b9ac03a4eb20b209eb14552d5b914e21a:experiments/RE-CY62167-COVERAGE-THRESHOLD-01/recovery/outputs/cw_bounds.json | ConvertFrom-Json
$taskExpected = $taskGate.frozen_numerical_input.delta_star_s.numerator + '/' + $taskGate.frozen_numerical_input.delta_star_s.denominator
if ($taskFixed.domain.delta_limit_s.exact -ne $taskExpected) { throw 'Threshold mismatch' }
if ($taskGate.stage_1_started -or $null -ne $taskGate.results.delta_upper_s -or $null -ne $taskGate.results.delta_le_exact_threshold) { throw 'Stage mismatch' }
```

Проверка четырёх новых payload files по MANIFEST (сам MANIFEST не хэширует себя):

```powershell
$taskPackage = 'experiments/RE-CY62167-EXECUTOR-TIMING-GATE-01'
$taskManifest = Get-Content -Raw ($taskPackage+'/MANIFEST.json') | ConvertFrom-Json
foreach ($f in $taskManifest.files) {
  $p = Join-Path $taskPackage $f.path
  if ((Get-FileHash -Algorithm SHA256 -LiteralPath $p).Hash.ToLower() -ne $f.sha256) { throw ('Delivery mismatch '+$f.path) }
  if ((Get-Item -LiteralPath $p).Length -ne $f.bytes) { throw ('Size mismatch '+$f.path) }
}
```

## Публикационная проверка

Delivery SHA определяется Git commit, содержащим эти пять файлов, и передаётся
в Issue №15/итоговом сообщении. SHA не встраивается циклически в manifest.
После commit/push проверяются remote head, родитель=base и каждый published
blob относительно локальных bytes. Итоги этой посткоммитной проверки передаются
в Issue и пользователю, не записываются задним числом в исходный commit.

```powershell
git push -u origin research/cy62167-executor-timing-gate-01
git ls-remote --heads origin main research/cy62167-executor-timing-gate-01
git diff-tree --no-commit-id --name-status -r HEAD
git diff --check be6b447e1c2ee7b70e68604fd135b379a800e62f HEAD
git log -1 --format='%H %P'
```

Published bytes читаются обратно по exact delivery SHA через GitHub;
local/remote SHA и все пять blob IDs должны совпасть. Разрешённый diff —
только новый каталог задания. Никакой push/merge в main, PR или закрытие
Issue не выполняются.
