import os
import sys
import json
import glob
import webbrowser

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QApplication, QStackedWidget, QCheckBox, 
                             QLabel,QFrame, QToolButton, QGridLayout, QComboBox,
                             QDialog)
from PyQt5.QtGui import QPixmap, QPainter, QCursor, QIcon
from PyQt5.QtCore import Qt, QTimer, QSize
from config import APP_VERSION, LOCALES, CATEGORIES_BASE, CATEGORIES_DLC

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))


class CollapsibleSection(QWidget):
    def __init__(self, title):
        super().__init__()
        self.section_layout = QVBoxLayout(self)
        self.section_layout.setContentsMargins(0, 0, 0, 0)
        self.section_layout.setSpacing(0)
        self.toggle_btn = QToolButton(self)
        self.toggle_btn.setText(f"▼ {title}")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.setChecked(False) 
        self.toggle_btn.setStyleSheet("""
            QToolButton { 
                border: none; 
                font-weight: bold; 
                color: #d4a956; 
                text-align: left; 
                padding: 10px 0px 5px 0px;
                font-size: 14px;
            }
            QToolButton:hover {
                color: #ffffff;
            }
        """)
        self.toggle_btn.clicked.connect(self.on_toggle)
        self.section_layout.addWidget(self.toggle_btn)
        self.content_area = QWidget()
        self.content_layout = QGridLayout(self.content_area)
        self.content_layout.setVerticalSpacing(6)
        self.content_layout.setHorizontalSpacing(10)
        self.content_layout.setContentsMargins(10, 5, 0, 5) 
        self.content_layout.setColumnStretch(0, 1)
        self.content_layout.setColumnStretch(1, 1)

        self.section_layout.addWidget(self.content_area)
        
        self.row = 0
        self.col = 0

    def add_widget(self, widget):
        self.content_layout.addWidget(widget, self.row, self.col, Qt.AlignLeft)
        self.col += 1
        if self.col > 1:
            self.col = 0
            self.row += 1

    def on_toggle(self):
        checked = self.toggle_btn.isChecked()
        arrow = "▶" if checked else "▼"
        title_text = self.toggle_btn.text().split(' ', 1)[1]
        self.toggle_btn.setText(f"{arrow} {title_text}")
        self.content_area.setVisible(not checked)


        
class CustomInputDialog(QDialog):
    def __init__(self, parent=None, title="Новый профиль", label_text="Введите имя:"):
        super().__init__(parent)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        self.setFixedSize(350, 170)
        self.setStyleSheet("""
            QDialog {
                background-color: #1c1c1c;
                border: 2px solid #8b7355;
            }
            QLabel {
                color: #d4a956;
                font-family: 'Georgia', serif;
                font-size: 15px;
                border: none;
            }
            QLineEdit {
                background-color: #2d2d2d;
                color: #e8dcc2;
                border: 1px solid #8b7355;
                padding: 6px;
                font-size: 16px;
                font-family: 'Georgia', serif;
            }
            QPushButton {
                background-color: rgba(40, 40, 40, 200);
                color: #e8dcc2;
                border: 1px solid #8b7355;
                border-radius: 3px;
                padding: 6px 15px;
                font-family: 'Georgia', serif;
                font-size: 14px;
            }
            QPushButton:hover { 
                background-color: rgba(70, 70, 70, 240); 
                border-color: #ffaa00; 
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(10)
        self.title_label = QLabel(title.upper())
        self.title_label.setStyleSheet("color: #ffaa00; font-size: 18px; font-weight: bold; margin-bottom: 5px;")
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)

        self.label = QLabel(label_text)
        layout.addWidget(self.label)
        
        self.input_field = QLineEdit()
        layout.addWidget(self.input_field)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.clicked.connect(self.accept)
        
        cancel_text = "Cancel" if "Enter" in label_text else "Отмена"
        self.btn_cancel = QPushButton(cancel_text)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.clicked.connect(self.reject)
        
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(btn_layout)
        
    def get_text(self):
        return self.input_field.text()

class MainMenu(QWidget):
    def __init__(self, switch_to_map_callback, bg_path, current_version=APP_VERSION):
        super().__init__()
        
        self.switch_callback = switch_to_map_callback
        self.bg_image = QPixmap(bg_path)
        self.current_lang = self.load_app_settings()
        self.base_profile = "New profile"
        self.current_version = current_version
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.addSpacing(40)

        # Profile + Version
        profile_container = QVBoxLayout()
        profile_container.setSpacing(8)
        profile_buttons_layout = QHBoxLayout()
        self.btn_create_profile = QPushButton("Создать")
        self.btn_create_profile.setFixedSize(146, 38)
        self.btn_create_profile.clicked.connect(self.create_new_profile)
        self.btn_delete_profile = QPushButton("Удалить")
        self.btn_delete_profile.setFixedSize(146, 38)
        self.btn_delete_profile.clicked.connect(self.delete_current_profile)
        
        btn_mini_style = """
            QPushButton {
                background-color: rgba(40, 40, 40, 200);
                color: #e8dcc2;
                border: 1px solid #8b7355;
                border-radius: 3px;
                font-family: "Georgia", serif;
                font-size: 15px;
                padding: 4px;
            }
            QPushButton:hover { background-color: rgba(70, 70, 70, 240); border-color: #ffaa00; }
        """
        self.btn_create_profile.setStyleSheet(btn_mini_style)
        self.btn_delete_profile.setStyleSheet(btn_mini_style.replace("rgba(40, 40, 40, 200)", "rgba(140, 40, 40, 200)"))
        
        profile_buttons_layout.addWidget(self.btn_create_profile)
        profile_buttons_layout.addWidget(self.btn_delete_profile)
        profile_buttons_layout.addStretch()
        
        self.profile_combo = QComboBox()
        self.profile_combo.setFixedWidth(300)
        self.profile_combo.addItem(self.base_profile)
        self.load_existing_profiles()
        
        profile_container.addLayout(profile_buttons_layout)
        profile_container.addWidget(self.profile_combo)
        
        # Current verison
        self.version_label = QLabel(f"v{self.current_version}")
        self.version_label.setStyleSheet("""
            color: rgba(200, 200, 200, 150); 
            font-family: "Georgia", serif;
            font-size: 16px; 
            font-weight: bold;
            background: transparent;
        """)
        
        top_layout = QHBoxLayout()
        top_layout.addLayout(profile_container)
        top_layout.addStretch()
        top_layout.addWidget(self.version_label, alignment=Qt.AlignTop | Qt.AlignRight)
        
        main_layout.addLayout(top_layout)
        main_layout.addStretch()

        btn_container = QWidget()
        btn_container.setFixedWidth(500)
        btn_layout = QVBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        
        map_btn_container = QHBoxLayout()
        
        self.btn_lang = QPushButton(self.current_lang.upper())
        self.btn_lang.setFixedSize(60, 55) 
        self.btn_lang.clicked.connect(self.toggle_language)
        self.btn_map = QPushButton("Интерактивная карта")
        self.btn_map.clicked.connect(self.on_map_clicked)
        map_btn_container.addWidget(self.btn_lang)
        map_btn_container.addWidget(self.btn_map)
        self.btn_items = QPushButton("Предметы (В разработке)")
        self.btn_items.setEnabled(False) 
        self.btn_npc = QPushButton("База NPC (В разработке)")
        self.btn_npc.setEnabled(False)
        
        btn_layout.addLayout(map_btn_container)
        btn_layout.addWidget(self.btn_items)
        btn_layout.addWidget(self.btn_npc)
        
        center_h_layout = QHBoxLayout()
        center_h_layout.addStretch()
        center_h_layout.addWidget(btn_container)
        center_h_layout.addStretch()
        
        main_layout.addLayout(center_h_layout)
        main_layout.addStretch()

        github_icon_path = os.path.join(base_path, "icons", "github.png") 
        icon_size = 48    # Icon size
        button_size = 56  # Zone sizd
        
        self.btn_github = QPushButton()
        self.btn_github.setFixedSize(button_size, button_size)
        self.btn_github.setCursor(Qt.PointingHandCursor)
        
        if os.path.exists(github_icon_path):
            self.btn_github.setIcon(QIcon(github_icon_path))
            self.btn_github.setIconSize(QSize(icon_size, icon_size))
        else:
            self.btn_github.setText("Git")
        self.btn_github.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20);
                border-radius: 5px;
            }
        """)

        self.btn_github.clicked.connect(lambda: webbrowser.open("https://github.com/CreateDDy"))
        bottom_corner_layout = QHBoxLayout()
        bottom_corner_layout.addStretch() 
        bottom_corner_layout.addWidget(self.btn_github)
        
        main_layout.addLayout(bottom_corner_layout)

        widget_style = """
            QPushButton {
                font-family: "Georgia", serif;
                font-size: 16pt;
                color: #e8dcc2;
                background-color: rgba(26, 26, 26, 220);
                border: 2px solid #8b7355;
                padding: 10px;
                border-radius: 5px;
            }
            QPushButton:hover { 
                background-color: rgba(42, 42, 42, 240); 
                border-color: #ffaa00; 
            }
            QPushButton:disabled { 
                color: #555; 
                border-color: #333; 
                background-color: rgba(26, 26, 26, 150); 
            }
            QComboBox {
                background-color: rgba(26, 26, 26, 220);
                color: #e8dcc2;
                border: 2px solid #8b7355;
                padding: 5px;
                border-radius: 5px;
                font-size: 14pt;
                font-family: "Georgia", serif;
            }
            QComboBox QAbstractItemView {
                background-color: #1a1a1a;
                color: #e8dcc2;
                selection-background-color: #3d3d3d;
            }
        """
        self.setStyleSheet(widget_style)
        
        self.loading_overlay = QWidget(self)
        self.loading_overlay.setStyleSheet("background-color: rgba(0, 0, 0, 150);") 
        self.loading_overlay.hide()
        overlay_layout = QVBoxLayout(self.loading_overlay)
        overlay_layout.setContentsMargins(0, 0, 40, 40) 
        bottom_h_layout = QHBoxLayout()
        self.loading_icon = QLabel()
        
        icon_path = os.path.join(".", "icons", "MENU_Loading_02.png")
        pixmap = QPixmap(icon_path)
        
        if pixmap.isNull():
            print(f"Error loading icon: {icon_path}")
            
        self.loading_icon.setPixmap(pixmap)
        self.loading_icon.setStyleSheet("background-color: transparent;") 
        
        bottom_h_layout.addStretch()
        bottom_h_layout.addWidget(self.loading_icon)
        
        overlay_layout.addStretch()
        overlay_layout.addLayout(bottom_h_layout)
        
        self.update_texts()

    def load_app_settings(self):
        settings_path = os.path.join(base_path, "saves", "settings.json")
        if os.path.exists(settings_path):
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    return data.get("lang", "ru")
            except:
                return "ru"
        return "ru"

    def save_app_settings(self):
        saves_dir = os.path.join(base_path, "saves")
        if not os.path.exists(saves_dir):
            os.makedirs(saves_dir)
            
        settings_path = os.path.join(saves_dir, "settings.json")
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump({"lang": self.current_lang}, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_existing_profiles(self):
        saves_dir = os.path.join(base_path, "saves")
        if not os.path.exists(saves_dir):
            os.makedirs(saves_dir)
            
        search_pattern = os.path.join(saves_dir, "save_*.json")
        for file_path in glob.glob(search_pattern):
            filename = os.path.basename(file_path)
            profile_name = filename.replace("save_", "").replace(".json", "")
            if profile_name not in [self.base_profile, "data", "default"]:
                self.profile_combo.addItem(profile_name)

    def create_new_profile(self):
        title = "Новый профиль" if self.current_lang == "ru" else "New Profile"
        label = "Введите имя:" if self.current_lang == "ru" else "Enter profile name:"
        dialog = CustomInputDialog(self, title, label)
        global_pos = self.profile_combo.mapToGlobal(self.profile_combo.rect().topRight())
        dialog.move(global_pos.x() + 20, global_pos.y() - 60)
        
        if dialog.exec_() == QDialog.Accepted:
            text = dialog.get_text()
            if text.strip():
                safe_name = "".join(c for c in text.strip() if c.isalnum() or c in ('_', '-'))
                if safe_name and safe_name != self.base_profile:
                    if self.profile_combo.findText(safe_name) == -1:
                        self.profile_combo.addItem(safe_name)
                    self.profile_combo.setCurrentText(safe_name)

    def delete_current_profile(self):
        profile_name = self.profile_combo.currentText()
        if not profile_name or profile_name == self.base_profile:
            return    
        safe_profile_name = "".join(c for c in profile_name if c.isalnum() or c in ('_', '-'))
        file_path = os.path.join(base_path, "saves", f"save_{safe_profile_name}.json")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                print(f"Error deleting {safe_profile_name}: {e}")
                
        index = self.profile_combo.findText(profile_name)
        if index >= 0:
            self.profile_combo.removeItem(index)
            
        self.profile_combo.setCurrentText(self.base_profile)

    def toggle_language(self):
        self.current_lang = "en" if self.current_lang == "ru" else "ru"
        self.btn_lang.setText(self.current_lang.upper())
        self.update_texts()
        self.save_app_settings()

    def update_texts(self):
        menu_texts = {
            "ru": {
                "map": "Интерактивная карта",
                "items": "Предметы (В разработке)",
                "npc": "База NPC (В разработке)",
                "create": "Создать",
                "delete": "Удалить"
            },
            "en": {
                "map": "Interactive Map",
                "items": "Items (WIP)",
                "npc": "NPC Database (WIP)",
                "create": "New Profile",
                "delete": "Delete"
            }
        }
        lang_data = menu_texts[self.current_lang]
        self.btn_map.setText(lang_data["map"])
        self.btn_items.setText(lang_data["items"])
        self.btn_npc.setText(lang_data["npc"])
        self.btn_create_profile.setText(lang_data["create"])
        self.btn_delete_profile.setText(lang_data["delete"])

    def on_map_clicked(self):
        self.btn_map.setEnabled(False)
        self.btn_lang.setEnabled(False)
        self.profile_combo.setEnabled(False)
        self.btn_create_profile.setEnabled(False)
        self.btn_delete_profile.setEnabled(False)
        
        loading_text = "Loading map..." if self.current_lang == "en" else "Загрузка карты..."
        self.btn_map.setText(loading_text)
        
        self.loading_overlay.resize(self.size())
        self.loading_overlay.show()
        QApplication.processEvents()
        
        QTimer.singleShot(50, self.launch_heavy_map)

    def launch_heavy_map(self):
        profile_name = self.profile_combo.currentText()
        if not profile_name:
            profile_name = self.base_profile
            
        safe_profile_name = "".join(c for c in profile_name if c.isalnum() or c in ('_', '-'))

        self.switch_callback(self.current_lang, safe_profile_name)
        
        self.loading_overlay.hide()
        self.btn_map.setEnabled(True)
        self.btn_lang.setEnabled(True)
        self.profile_combo.setEnabled(True)
        self.btn_create_profile.setEnabled(True)
        self.btn_delete_profile.setEnabled(True)
        self.update_texts()

    def paintEvent(self, event):
        painter = QPainter(self)
        if not self.bg_image.isNull():
            painter.drawPixmap(self.rect(), self.bg_image)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.loading_overlay.isVisible():
            self.loading_overlay.resize(self.size())

class MapScreen(QWidget):
    def __init__(self, viewer, back_callback, lang="ru", profile_name="default"):
        super().__init__()
        self.viewer = viewer
        self.lang = lang
        self.profile_name = profile_name
        self.texts = LOCALES.get(self.lang, LOCALES.get("ru", {}))
        saves_dir = os.path.join(base_path, "saves")
        if not os.path.exists(saves_dir):
            os.makedirs(saves_dir)
            
        self.save_path = os.path.join(saves_dir, f"save_{self.profile_name}.json")
        self.save_data = self.load_save_data()
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        self.sidebar = QWidget()
        self.sidebar.setFixedWidth(450)
        self.sidebar.setStyleSheet("""
            QWidget { background-color: #1c1c1c; color: #c4bca2; font-family: 'Segoe UI', serif; }
            QLineEdit { background-color: #2d2d2d; border: 1px solid #c4bca2; padding: 5px; color: white; }
            QPushButton { background-color: #2d2d2d; border: 1px solid #5a5a5a; padding: 8px; }
            QPushButton:hover { background-color: #3d3d3d; }
            QCheckBox { font-size: 14px; margin-top: 0px; margin-bottom: 0px; }
        """)
        
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(15, 20, 15, 20)
        sidebar_layout.setSpacing(15)
        
        title = QLabel("ELDEN RING MAP")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #d4a956; text-align: center;")
        title.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(title)
        
        map_btn_layout = QVBoxLayout()
        map_btn_layout.setSpacing(5) 
        
        self.btn_surface = QPushButton(self.texts.get("btn_surface", "Междуземье"))
        self.btn_underground = QPushButton(self.texts.get("btn_underground", "Подземная карта"))
        self.btn_dlc = QPushButton(self.texts.get("btn_dlc", "Realm of Shadow"))
        
        self.btn_surface.clicked.connect(lambda: self.switch_map_layer("surface"))
        self.btn_underground.clicked.connect(lambda: self.switch_map_layer("underground"))
        self.btn_dlc.clicked.connect(lambda: self.switch_map_layer("dlc"))
        
        map_btn_layout.addWidget(self.btn_surface)
        map_btn_layout.addWidget(self.btn_underground)
        map_btn_layout.addWidget(self.btn_dlc)
        
        sidebar_layout.addLayout(map_btn_layout)
        
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #5a5a5a;")
        sidebar_layout.addWidget(line)
        
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText(self.texts.get("search_placeholder", "Поиск"))
        sidebar_layout.addWidget(self.search_bar)

        filter_btn_layout = QHBoxLayout()
        
        self.btn_show_all = QPushButton(self.texts.get("btn_show_all", "Показать всё"))
        self.btn_hide_all = QPushButton(self.texts.get("btn_hide_all", "Скрыть всё"))
        
        self.btn_show_all.setFixedHeight(30)
        self.btn_hide_all.setFixedHeight(30)
        
        self.btn_show_all.clicked.connect(lambda: self.toggle_all_filters(True))
        self.btn_hide_all.clicked.connect(lambda: self.toggle_all_filters(False))
        
        filter_btn_layout.addWidget(self.btn_show_all)
        filter_btn_layout.addWidget(self.btn_hide_all)
        
        sidebar_layout.addLayout(filter_btn_layout)
        
        self.checkboxes = {}
        self.state = {}
        self.base_labels = {} 
        self.progress = {}    

        self.categories_stack = QStackedWidget()
        
        self.base_cat_widget = QWidget()
        base_cat_layout = QVBoxLayout(self.base_cat_widget)
        base_cat_layout.setContentsMargins(0, 0, 0, 0)
        
        self.dlc_cat_widget = QWidget()
        dlc_cat_layout = QVBoxLayout(self.dlc_cat_widget)
        dlc_cat_layout.setContentsMargins(0, 0, 0, 0)
        
        def build_category_panel(cat_dict, target_layout):
            for group_name, items in cat_dict.items():
                translated_group_name = self.texts.get(group_name, group_name)
                section = CollapsibleSection(translated_group_name)
                
                for key, label_text in items.items():
                    locale_key = f"lbl_{key}"
                    display_name = self.texts.get(locale_key, label_text)
                    
                    cb = QCheckBox(f"{display_name} (0/0)")
                    cb.setChecked(True)
                    cb.stateChanged.connect(self.update_filters)
                    
                    self.checkboxes[key] = cb
                    self.state[key] = True 
                    self.base_labels[key] = display_name
                    self.progress[key] = {"current": 0, "total": 0}
                    
                    section.add_widget(cb)
                    
                target_layout.addWidget(section)
            target_layout.addStretch()

        build_category_panel(CATEGORIES_BASE, base_cat_layout)
        build_category_panel(CATEGORIES_DLC, dlc_cat_layout)
        
        self.categories_stack.addWidget(self.base_cat_widget)
        self.categories_stack.addWidget(self.dlc_cat_widget)
        
        sidebar_layout.addWidget(self.categories_stack)
            
        self.search_bar.textChanged.connect(self.update_filters)
        
        self.btn_back = QPushButton(self.texts.get("btn_back", "В главное меню"))
        self.btn_back.clicked.connect(back_callback)
        sidebar_layout.addWidget(self.btn_back)
        
        main_layout.addWidget(self.sidebar)
        main_layout.addWidget(self.viewer)
        
        self.btn_toggle_sidebar = QPushButton("☰", self)
        self.btn_toggle_sidebar.setFixedSize(40, 40)
        self.btn_toggle_sidebar.move(10, 10) 
        self.btn_toggle_sidebar.setStyleSheet("""
            QPushButton { 
                background-color: #1c1c1c; 
                color: #d4a956; 
                font-size: 22px; 
                border: 2px solid #5a5a5a; 
                border-radius: 5px; 
                font-weight: bold;
            }
            QPushButton:hover { background-color: #3d3d3d; border-color: #d4a956; }
        """)
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)

    def switch_map_layer(self, layer):

        if layer == "dlc":
            self.categories_stack.setCurrentWidget(self.dlc_cat_widget)
        else:
            self.categories_stack.setCurrentWidget(self.base_cat_widget)
            

        for key, cb in self.checkboxes.items():
            cb.blockSignals(True)
            cb.setChecked(True)
            self.state[key] = True
            cb.blockSignals(False)
            
        search_text = self.search_bar.text()
        
        if hasattr(self.viewer, 'change_map_layer'):
            self.viewer.change_map_layer(layer)
            
        self.viewer.update_marker_visibility(self.state, search_text)

    def toggle_all_filters(self, state):
        for key, cb in self.checkboxes.items():
            cb.blockSignals(True)
            cb.setChecked(state)
            self.state[key] = state
            cb.blockSignals(False)
            
        search_text = self.search_bar.text()
        self.viewer.update_marker_visibility(self.state, search_text)

    def update_filters(self):
        for key, cb in self.checkboxes.items():
            self.state[key] = cb.isChecked()
        search_text = self.search_bar.text()
        self.viewer.update_marker_visibility(self.state, search_text)

    def toggle_sidebar(self):
        if self.sidebar.isVisible():
            self.sidebar.setVisible(False)
            self.btn_toggle_sidebar.setText("▶") 
        else:
            self.sidebar.setVisible(True)
            self.btn_toggle_sidebar.setText("☰")

    def add_category_total(self, key, amount):
        if key in self.progress:
            self.progress[key]["total"] += amount
            self._update_checkbox_text(key)

    def _update_checkbox_text(self, key):
        data = self.progress.get(key)
        
        if not isinstance(data, dict):
            print(f"[DEBUG] Ключ '{key}' сломан! Тип: {type(data)}, Значение: {data}")
            self.progress[key] = {"current": 0, "total": 0}
            data = self.progress[key]
            
        cur = data.get("current", 0)
        tot = data.get("total", 0)
        base = self.base_labels.get(key, key)
        
        try:
            self.checkboxes[key].setText(f"{base} ({int(cur)}/{int(tot)})")
        except Exception as e:
            print(f"[DEBUG] Ошибка отрисовки {key}: {e}")

    def load_save_data(self):
        if os.path.exists(self.save_path):
            try:
                with open(self.save_path, "r", encoding="utf-8") as f:
                    return set(json.load(f))
            except:
                return set()
        return set()

    def save_to_json(self):
        try:
            with open(self.save_path, "w", encoding="utf-8") as f:
                json.dump(list(self.save_data), f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Ошибка записи сохранения: {e}")

    def on_marker_toggled(self, key, marker_id, is_completed):
        if key in self.progress and isinstance(self.progress[key], dict):
            if is_completed:
                self.progress[key]["current"] = self.progress[key].get("current", 0) + 1
                self.save_data.add(marker_id)
            else:
                self.progress[key]["current"] = max(0, self.progress[key].get("current", 0) - 1)
                self.save_data.discard(marker_id)
            
            self._update_checkbox_text(key)
            self.save_to_json()

class MarkerInfoWindow(QDialog):
    def __init__(self, title, description, parent=None):
        super().__init__(parent)
        
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_DeleteOnClose)
        
        cursor_path = os.path.join(base_path, "icons", "cursor.png")
        if os.path.exists(cursor_path):
            cursor_img = QPixmap(cursor_path).scaled(48, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setCursor(QCursor(cursor_img, 0, 0))
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(8)
        layout.setSizeConstraint(QVBoxLayout.SetFixedSize)
        
        self.setStyleSheet("""
            QDialog {
                background-color: rgba(20, 20, 20, 245);
                border: 2px solid #8b7355;
                border-radius: 5px;
            }
            QLabel {
                font-family: "Georgia", serif;
                color: #e8dcc2;
            }
        """)
        
        if title:
            title_label = QLabel(title)
            title_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #ffaa00;")
            title_label.setWordWrap(True)
            layout.addWidget(title_label)
        
        desc_label = QLabel(description)
        desc_label.setStyleSheet("font-size: 11pt; color: #cbd5e1;")
        desc_label.setWordWrap(True)
        
        layout.addWidget(desc_label)
        
        self.setMinimumWidth(280)
        self.setMaximumWidth(320)