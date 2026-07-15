import sys
import os
import json
from components import MapMarker, RegionMarker, InteractiveMapViewer as InteractiveMapViewer
from PyQt5.QtWidgets import (QApplication, QMainWindow, QStackedWidget)
from PyQt5.QtGui import QPixmap, QCursor
from PyQt5.QtCore import Qt
from interface import MainMenu, MapScreen 
from config import APP_VERSION, REGISTRY, DATA_MANIFEST, MAP_LAYERS, GAME_TITLE

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))

def get_local_db_version():
    try:
        with open(os.path.join(base_path, "version.json"), "r", encoding="utf-8") as f:
            return json.load(f).get("db_version", APP_VERSION)
    except Exception:
        return APP_VERSION

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(GAME_TITLE)
        self.setGeometry(100, 100, 1200, 800)
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        self.current_db_version = get_local_db_version()
        menu_bg_path = os.path.join(base_path, "icons", "menu_bg.jpg")
        self.menu_screen = MainMenu(self.launch_map, menu_bg_path, self.current_db_version)
        self.stack.addWidget(self.menu_screen)
        
        self.map_screen = None 
        
        cursor_path = os.path.join(base_path, "icons", "cursor.png")
        cursor_img = QPixmap(cursor_path)
        if not cursor_img.isNull():
            scaled_cursor = cursor_img.scaled(48, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.custom_cursor = QCursor(scaled_cursor, 0, 0)
            self.setCursor(self.custom_cursor)
        else:
            self.custom_cursor = None

    def launch_map(self, lang, profile_name="default"):
        
        if self.map_screen:
            self.stack.removeWidget(self.map_screen)
            self.map_screen.deleteLater()

        self.data_vault = {}
        for key, base_name in DATA_MANIFEST.items():
            file_path = os.path.join(base_path, "DATA", f"{base_name}_{lang}.json")
            self.data_vault[key] = self.load_json(file_path)

        first_layer_key = list(MAP_LAYERS.keys())[0]
        first_layer_meta = MAP_LAYERS[first_layer_key]
        start_map_path = first_layer_meta["file"]
        
        self.viewer = InteractiveMapViewer(start_map_path, first_layer_meta["zoom"], default_layer="surface", lang=lang)
        self.viewer.profile_name = profile_name
        self.viewer.load_waypoints()

        if self.custom_cursor:
            self.viewer.viewport().setCursor(self.custom_cursor)

        self.map_screen = MapScreen(self.viewer, lambda: self.stack.setCurrentIndex(0), lang, profile_name)
        self.stack.addWidget(self.map_screen)
        
        for layer_id, meta in MAP_LAYERS.items():
            path = meta["file"]
            btn = getattr(self.map_screen, f"btn_{layer_id}", None)
            if btn:
                btn.clicked.connect(lambda checked=False, p=path, z=meta["zoom"], l=layer_id: self.switch_map_layer(p, z, l))

        for item_id, meta in REGISTRY.items():
            icon_path = os.path.join(base_path, "icons", meta["icon"])
            overlay_file = meta.get("overlay")
            overlay_path = os.path.join(base_path, "icons", overlay_file) if overlay_file else None
            
            custom_size = meta.get("icon_size")
            source_key = meta.get("source")
            data = self.data_vault.get(source_key, {})
            
            is_regional = meta.get("is_regional", False)
            use_grace = (meta.get("marker_type") == "grace")
            
            keys_to_process = meta.get("json_keys") or [None]
            
            for json_key in keys_to_process:
                target_data = data.get(json_key, []) if json_key else data
                points = [] 
                if is_regional and isinstance(target_data, dict):
                    if json_key:
                        for region_name, region_list in target_data.items():
                            if isinstance(region_list, list):
                                for pt in region_list:
                                    if "map_layer" not in pt:
                                        pt["map_layer"] = json_key
                                    points.append(pt)
                    else:
                        for layer_id, regions_dict in target_data.items():
                            if isinstance(regions_dict, dict):
                                for region_name, region_list in regions_dict.items():
                                    if isinstance(region_list, list):
                                        for pt in region_list:
                                            if "map_layer" not in pt:
                                                pt["map_layer"] = layer_id
                                            points.append(pt)
                                            
                elif isinstance(target_data, list):
                    points.extend(target_data)
                    
                elif isinstance(target_data, dict):
                    for cat_name, pt_list in target_data.items():
                        if isinstance(pt_list, list):
                            points.extend(pt_list)
                
                if points and item_id in self.map_screen.progress:
                    self.map_screen.add_category_total(item_id, len(points))
                
                for pt in points:
                    fallback_label = meta.get(f"label_{lang}", meta.get("label_ru", "Unknown"))
                    name = pt.get("title", pt.get("name", fallback_label))
                    layer = pt.get("map_layer", "surface") 
                    
                    marker_id = str(pt.get("id", f"{item_id}_{int(pt.get('x', 0))}_{int(pt.get('y', 0))}"))
                    initial_completed = marker_id in self.map_screen.save_data
                    
                    if initial_completed and item_id in self.map_screen.progress:
                        self.map_screen.progress[item_id]["current"] += 1
                    
                    if use_grace:
                        marker = RegionMarker(icon_path, pt.get("x", 0), pt.get("y", 0), name, item_id, layer, self.map_screen.on_marker_toggled, marker_id, initial_completed)
                    else:
                        marker = MapMarker(icon_path, pt.get("x", 0), pt.get("y", 0), name, item_id, layer, overlay_path, custom_size, self.map_screen.on_marker_toggled, marker_id, initial_completed)
                        
                        marker.note = pt.get("description", "")
                        marker.loot = pt.get("loot", "")
                        marker.add_info_mark() 
                    
                    self.viewer.scene.addItem(marker)
                
                if points and item_id in self.map_screen.progress:
                    self.map_screen._update_checkbox_text(item_id)
        
        self.map_screen.update_filters()
        self.stack.setCurrentIndex(1)

            
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    style_path = os.path.join(base_path, "style.qss")
    if os.path.exists(style_path):
        with open(style_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())
    
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())