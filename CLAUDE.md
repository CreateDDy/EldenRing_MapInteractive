# EldenRing Interactive Map — контекст проекта

Offline-приложение на PyQt5: интерактивная карта Elden Ring с профилями,
маркерами прогресса, слоями (surface / underground / dlc), waypoints и базой предметов.
Ключевые файлы: `main.py`, `config.py`, `interface.py`, `components.py`.

## ТЕКУЩАЯ ЗАДАЧА: починить load_items_database (main.py)

### Симптом
В списке предметов (ItemsScreen) появились 4 записи «♦ Unknown» в категории «Предметы».

### Причина
`load_items_database()` в `main.py` обходит ВСЮ папку `DATA` и мержит все json
в один `items_vault` через `dict.update()` — включая маркерные файлы
(graces, dungeons, night_boss и т.д.). Их верхние ключи (`surface`,
`underground`, `dlc`, `Hub`) попадают в vault, проходят фильтр
`isinstance(data, dict)` в `populate_tree()` (interface.py), не имеют
`name_ru` → отображаются как Unknown.

Дополнительные риски той же причины:
- `dict.update()` молча перетирает одинаковые ключи между файлами —
  результат зависит от порядка обхода os.walk.
- `_resolve_loot_data()` может ложно найти маркерный ключ вместо предмета.

Заметь асимметрию: `_load_data_vault()` (загрузчик маркеров) сознательно
исключает папку items (`dirs.remove("items")`), а `load_items_database()`
не исключает ничего.

### План фикса
1. В `load_items_database()` читать ТОЛЬКО `DATA/items` (папка уже существует).
2. Добавить предупреждение о пересечении ключей между файлами предметов:
   ```python
   dupes = items_vault.keys() & data.keys()
   if dupes:
       print(f"[WARN] Дубликаты id в {file}: {dupes}")
   ```
3. Опционально: в `_load_data_vault()` убрать костыль `dirs.remove("items")`
   и заменить сканирование дерева на явную загрузку по именам из `DATA_MANIFEST`.

### Проверка
- `len(items_vault)` должен уменьшиться (ушёл маркерный мусор).
- В ItemsScreen исчезают все 4 «Unknown», остальное дерево без изменений.
- Карточки лута у боссов открываются как раньше.

## Бэклог (по code review, полная версия в Notion)

Приоритетные:
1. ✅ (текущая задача) load_items_database сгребает все JSON из DATA.
2. Коллизии marker_id: `wp_{int(x)}_{int(y)}` и `{item_id}_{x}_{y}` —
   близкие координаты дают одинаковый id, прогресс липнет не к тому маркеру.
   Фикс: явные уникальные id в json-данных.
3. Дублирование локализации: резолв `name_{lang}`/`effects`/`description`
   продублирован в `main._resolve_item()` и `interface.on_item_clicked()`.
   Вынести в общую функцию.

Средние:
4. REGISTRY: смесь `label` и `label_ru`/`label_en` — привести к единому формату.
5. Захардкоженный русский в interface.py (кнопки «Создать»/«Удалить»,
   эвристика `"Cancel" if "Enter" in label_text`) — прогнать через LOCALES.
6. Карта грузится одним QPixmap на слой — сотни МБ RAM; рассмотреть
   тайлинг или выгрузку неактивного слоя.

Мелочи: print → logging; сузить широкие `except Exception`;
консолидировать стили (inline vs style.qss).
