import sys
import os
import json
from components import MapMarker, RegionMarker, InteractiveMapViewer as InteractiveMapViewer
from PyQt5.QtWidgets import (QApplication, QMainWindow, QStackedWidget)
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtCore import Qt, QTimer
from interface import MainMenu, MapScreen, ItemsScreen
from config import REGISTRY, DATA_MANIFEST, MAP_LAYERS, GAME_TITLE, get_img, sanitize_profile_name

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(GAME_TITLE)
        self.setGeometry(100, 100, 1200, 800)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        self.items_vault = self.load_items_database()

        self.map_screen = None
        self.items_screen = None
        self.viewer = None
        self.data_vault = {}
        self.current_loaded_lang = None
        self.current_loaded_profile = None

        menu_bg_path = os.path.join(base_path, "icons", "system_icons", "menu_bg.jpg")
        self.menu_screen = MainMenu(self.launch_map, menu_bg_path)
        self.menu_screen.switch_to_items_callback = self.launch_items
        self.stack.addWidget(self.menu_screen)

        self.custom_cursor = self._load_custom_cursor()
        if self.custom_cursor:
            self.setCursor(self.custom_cursor)

        self.menu_screen.loading_overlay.resize(1200, 800)
        self.menu_screen.loading_overlay.show()
        QTimer.singleShot(500, self.execute_preload)

    def _load_custom_cursor(self):
        cursor_path = os.path.join(base_path, "icons", "system_icons", "cursor.png")
        cursor_img = QPixmap(cursor_path)
        if cursor_img.isNull():
            return None
        scaled_cursor = cursor_img.scaled(48, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        return QCursor(scaled_cursor, 0, 0)

    def _current_safe_profile(self):
        profile = self.menu_screen.profile_combo.currentText()
        if not profile:
            profile = self.menu_screen.base_profile
        return sanitize_profile_name(profile)

    def execute_preload(self):
        safe_profile = self._current_safe_profile()
        self.launch_map(self.menu_screen.current_lang, safe_profile, switch_to_it=False)
        self.menu_screen.loading_overlay.hide()

    # ------------------------------------------------------------------
    # Map loading
    # ------------------------------------------------------------------

    def launch_map(self, lang, profile_name="default", switch_to_it=True):
        already_loaded = (
            self.map_screen is not None
            and self.current_loaded_lang == lang
            and self.current_loaded_profile == profile_name
        )
        if already_loaded:
            if switch_to_it:
                self.stack.setCurrentWidget(self.map_screen)
            return

        if self.map_screen is not None:
            self.stack.removeWidget(self.map_screen)
            self.map_screen.deleteLater()

        self.current_loaded_lang = lang
        self.current_loaded_profile = profile_name

        self.data_vault = self._load_data_vault(lang)
        self.viewer = self._create_viewer(lang, profile_name)
        self.map_screen = MapScreen(self.viewer, lambda: self.stack.setCurrentIndex(0), lang, profile_name)
        self.stack.addWidget(self.map_screen)

        self._connect_layer_buttons()
        self._populate_markers(lang)

        self.map_screen.update_filters()
        if switch_to_it:
            self.stack.setCurrentWidget(self.map_screen)

    def _load_data_vault(self, lang):
        data_vault = {}
        data_dir = os.path.join(base_path, "DATA")
        all_jsons = {}
        if os.path.exists(data_dir):
            for root, dirs, files in os.walk(data_dir):
                if "items" in dirs:
                    dirs.remove("items")
                for file in files:
                    if file.endswith(".json"):
                        all_jsons[file[:-5]] = os.path.join(root, file)

        for key, base_name in DATA_MANIFEST.items():
            if base_name in all_jsons:
                data_vault[key] = self.load_json(all_jsons[base_name])
            elif f"{base_name}_{lang}" in all_jsons:
                data_vault[key] = self.load_json(all_jsons[f"{base_name}_{lang}"])
            else:
                data_vault[key] = {}
                print(f"[DEBUG] Файл {base_name}.json не найден ни в одной папке!")
        return data_vault

    def _create_viewer(self, lang, profile_name):
        first_layer_key = list(MAP_LAYERS.keys())[0]
        first_layer_meta = MAP_LAYERS[first_layer_key]

        viewer = InteractiveMapViewer(first_layer_meta["file"], first_layer_meta["zoom"], default_layer="surface", lang=lang)
        viewer.profile_name = profile_name
        viewer.load_waypoints()

        if self.custom_cursor:
            viewer.viewport().setCursor(self.custom_cursor)
        return viewer

    def _connect_layer_buttons(self):
        for layer_id, meta in MAP_LAYERS.items():
            path = meta["file"]
            btn = getattr(self.map_screen, f"btn_{layer_id}", None)
            if btn:
                btn.clicked.connect(lambda checked=False, p=path, z=meta["zoom"], l=layer_id: self.switch_map_layer(p, z, l))

    def _populate_markers(self, lang):
        for item_id, meta in REGISTRY.items():
            self._add_markers_for_item(item_id, meta, lang)

    def _add_markers_for_item(self, item_id, meta, lang):
        icon_path = get_img(meta["icon"])
        overlay_file = meta.get("overlay")
        overlay_path = get_img(overlay_file) if overlay_file else None
        custom_size = meta.get("icon_size")
        source_key = meta.get("source")
        data = self.data_vault.get(source_key, {})

        is_regional = meta.get("is_regional", False)
        use_grace = (meta.get("marker_type") == "grace")
        keys_to_process = meta.get("json_keys") or [None]

        for json_key in keys_to_process:
            target_data = data.get(json_key, []) if json_key else data
            points = self._collect_points(target_data, is_regional, json_key)

            if points and item_id in self.map_screen.progress:
                self.map_screen.add_category_total(item_id, len(points))

            for pt in points:
                self._add_marker(item_id, meta, pt, lang, icon_path, overlay_path, custom_size, use_grace)

            if points and item_id in self.map_screen.progress:
                self.map_screen._update_checkbox_text(item_id)

    def _collect_points(self, target_data, is_regional, json_key):
        points = []
        if is_regional and isinstance(target_data, dict):
            if json_key:
                for _, region_list in target_data.items():
                    if isinstance(region_list, list):
                        for pt in region_list:
                            if "map_layer" not in pt:
                                pt["map_layer"] = json_key
                            points.append(pt)
            else:
                for layer_id, regions_dict in target_data.items():
                    if isinstance(regions_dict, dict):
                        for _, region_list in regions_dict.items():
                            if isinstance(region_list, list):
                                for pt in region_list:
                                    if "map_layer" not in pt:
                                        pt["map_layer"] = layer_id
                                    points.append(pt)
        elif isinstance(target_data, list):
            if json_key in MAP_LAYERS:
                for pt in target_data:
                    if "map_layer" not in pt:
                        pt["map_layer"] = json_key
            points.extend(target_data)
        elif isinstance(target_data, dict):
            # Идем по ключам (layer_id) и значениям (pt_list)
            for layer_id, pt_list in target_data.items():
                if isinstance(pt_list, list):
                    for pt in pt_list:
                        # Насильно прописываем слой, если его нет в самом маркере
                        if "map_layer" not in pt:
                            pt["map_layer"] = layer_id
                    points.extend(pt_list)
        return points

    def _add_marker(self, item_id, meta, pt, lang, icon_path, overlay_path, custom_size, use_grace):
        fallback_label = meta.get(f"label_{lang}", meta.get("label_ru", "Unknown"))
        name = pt.get(f"name_{lang}", pt.get("title", pt.get("name", fallback_label)))
        layer = pt.get("map_layer", "surface")

        marker_id = str(pt.get("id", f"{item_id}_{int(pt.get('x', 0))}_{int(pt.get('y', 0))}"))
        initial_completed = marker_id in self.map_screen.save_data

        if initial_completed and item_id in self.map_screen.progress:
            self.map_screen.progress[item_id]["current"] += 1

        if use_grace:
            marker = RegionMarker(icon_path, pt.get("x", 0), pt.get("y", 0), name, item_id, layer,
                                   self.map_screen.on_marker_toggled, marker_id, initial_completed)
        else:
            marker = MapMarker(icon_path, pt.get("x", 0), pt.get("y", 0), name, item_id, layer,
                                overlay_path, custom_size, self.map_screen.on_marker_toggled, marker_id, initial_completed)
            marker.note = pt.get(f"description_{lang}", pt.get("description", ""))
            marker.loot = pt.get(f"loot_{lang}", pt.get("loot", ""))
            marker.image_name = pt.get("image")
            marker.resistances = pt.get("resistances", {})
            marker.phases = pt.get("phases")
            loot_ids = pt.get("loot_items", [])
            marker.loot_data = self._resolve_loot_data(loot_ids, lang)
            marker.loot_ids_list = loot_ids
            marker.add_info_mark()

        self.viewer.scene.addItem(marker)

    def _resolve_loot_data(self, loot_ids, lang):
        loot_data_list = []
        for loot_item in loot_ids:
            if isinstance(loot_item, dict):
                raw_text = loot_item.get(lang, loot_item.get("ru", "Предмет"))
                loot_data_list.append({"name": raw_text, "lang": lang, "is_raw": True})
            elif loot_item in self.items_vault:
                loot_data_list.append(self._resolve_item(loot_item, lang))
            else:
                loot_data_list.append({"name": str(loot_item), "lang": lang, "is_raw": True})
        return loot_data_list

    def _resolve_item(self, loot_item, lang):
        db_item = self.items_vault[loot_item]
        resolved_item = db_item.copy()
        resolved_item["name"] = db_item.get(f"name_{lang}", db_item.get("name_ru", "Предмет"))

        w_type = db_item.get(f"weapon_type_{lang}", "-")
        resolved_item["type"] = w_type if w_type != "-" else db_item.get(f"type_{lang}", "")

        resolved_item["damage_type"] = db_item.get(f"damage_type_{lang}", db_item.get("damage_type_ru", ""))
        resolved_item["skill_name"] = db_item.get(f"skill_name_{lang}", db_item.get("skill_name_ru", ""))

        # Умный сбор эффектов (ищет и effects, и effect)
        resolved_item["effects"] = db_item.get(
            f"effects_{lang}",
            db_item.get("effects_ru",
                db_item.get(f"effect_{lang}",
                    db_item.get("effect_ru",
                        db_item.get(f"stats_{lang}", db_item.get("stats_ru", ""))
                    )
                )
            )
        )

        # Достаем лорное описание
        resolved_item["description"] = db_item.get(f"description_{lang}", db_item.get("description_ru", ""))

        resolved_item["lang"] = lang
        resolved_item["icon"] = db_item.get("icon", "default.png")
        return resolved_item

    # ------------------------------------------------------------------
    # Items screen
    # ------------------------------------------------------------------

    def launch_items(self, lang):
        if self.items_screen is not None:
            self.stack.removeWidget(self.items_screen)
            self.items_screen.deleteLater()
        self.items_screen = ItemsScreen(self.items_vault, lambda: self.stack.setCurrentIndex(0), lang)
        self.items_screen.jump_callback = self.find_and_jump_to_marker
        self.stack.addWidget(self.items_screen)
        self.stack.setCurrentWidget(self.items_screen)

    def load_items_database(self):
        items_vault = {}
        data_dir = os.path.join(base_path, "DATA")

        for root, _, files in os.walk(data_dir):
            for file in files:
                if file.endswith(".json"):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            items_vault.update(data)
                    except (OSError, json.JSONDecodeError) as e:
                        print(f"Ошибка чтения {file_path}: {e}")

        return items_vault

    def load_json(self, path):
        try:
            with open(path, "r", encoding="utf-8") as file:
                return json.load(file)
        except (FileNotFoundError, json.JSONDecodeError):
            print(f"Error loading file: {path}")
            return {}

    def switch_map_layer(self, path, zoom, layer):
        self.viewer.change_map(path, zoom, layer)
        self.map_screen.update_filters()

    def find_and_jump_to_marker(self, target_item_id):
        safe_profile = self._current_safe_profile()
        self.launch_map(self.menu_screen.current_lang, safe_profile, switch_to_it=True)

        target_marker = None
        if self.viewer is not None and self.viewer.scene:
            for item in self.viewer.scene.items():
                if hasattr(item, 'loot_ids_list') and target_item_id in item.loot_ids_list:
                    target_marker = item
                    break

        if target_marker:
            marker_layer = getattr(target_marker, 'layer', getattr(target_marker, 'map_layer', 'surface'))
            self.viewer.setUpdatesEnabled(False)
            if marker_layer == "dlc":
                self.map_screen.btn_dlc.click()
            elif marker_layer == "underground":
                self.map_screen.btn_underground.click()
            else:
                self.map_screen.btn_surface.click()
            self.map_screen.btn_hide_all.click()
            target_marker.setVisible(True)
            self.viewer.centerOn(target_marker.pos())
            self.viewer.setUpdatesEnabled(True)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    style_path = os.path.join(base_path, "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
