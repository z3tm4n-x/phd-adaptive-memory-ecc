# Проверки поставки T95

04.10.2026, самопроверка автора доказательства; независимая инженерная
проверка и научная рецензия ещё не выполнены.

- Python 3.12.14: verify.py --write, затем verify.py без записи.
- 71/71 проверок; report.json совпадает точно, 7 исходных git-blob SHA
  соответствуют принятому main. Полный список — report.json / checks.
- Никаких float, симуляций, новых кривых или изменения исходной сетки.
- Основной текст: 6 страниц A4, 11 pt, поля 18 мм; все страницы
  просмотрены после рендера. Длинная формула (2) разбита на строки,
  таблицы/формулы не обрезаны. Приложение не включено в этот объём.

Команда контроля объёма (Pandoc, XeLaTeX, DejaVu Serif; временный PDF,
не дополнительный научный файл):

~~~bash
pandoc theory/t95-method-regime-selection.md \
  -f markdown+tex_math_dollars --pdf-engine=xelatex \
  -V mainfont='DejaVu Serif' -V sansfont='DejaVu Sans' \
  -V monofont='DejaVu Sans Mono' -V papersize=a4 \
  -V geometry:margin=18mm -V fontsize=11pt -V colorlinks=true \
  -o /tmp/t95-main.pdf
pdfinfo /tmp/t95-main.pdf
~~~

Числа источников переиспользованы адресно. Полный протокол старых
T88/T90 заново не запускался и ему не приписывается новый вердикт.
Материалы независимой проверки: ENGINEER_REQUEST.md, точный SHA
поставки в комментарии PR #100 / Issue #95. #96 не начата.
