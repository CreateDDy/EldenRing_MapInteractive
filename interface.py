import os
import sys
import json
import glob
import webbrowser

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
                             QLineEdit, QApplication, QStackedWidget, QCheckBox, 
                             QLabel,QFrame, QToolButton, QGridLayout, QComboBox,
                             QDialog, QSplitter, QTreeWidget, QScrollArea,QTreeWidgetItem)
from PyQt5.QtGui import QPixmap, QPainter, QCursor, QIcon, QColor
from PyQt5.QtCore import Qt, QTimer, QSize
from config import LOCALES, CATEGORIES_BASE, CATEGORIES_DLC, get_img

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
    def __init__(self, switch_to_map_callback, bg_path):
        super().__init__()

        self.switch_callback = switch_to_map_callback
        self.bg_image = QPixmap(bg_path)
        self.current_lang = self.load_app_settings()
        self.base_profile = "New profile"

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
        
        top_layout = QHBoxLayout()
        top_layout.addLayout(profile_container)
        top_layout.addStretch()

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
        self.btn_items = QPushButton("Предметы")
        self.btn_items.clicked.connect(self.on_items_clicked)
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

        # Размеры для всех нижних кнопок
        icon_size = 64   
        button_size = 64 
        
        # Общий стиль для круглых/квадратных прозрачных кнопок
        transparent_btn_style = """
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 20);
                border-radius: 5px;
            }
        """

        self.btn_github = QPushButton()
        self.btn_github.setFixedSize(button_size, button_size)
        self.btn_github.setCursor(Qt.PointingHandCursor)
        self.btn_github.setStyleSheet(transparent_btn_style)
        github_icon_path = os.path.join(base_path, "icons", "system_icons", "github.png") 
        if os.path.exists(github_icon_path):
            self.btn_github.setIcon(QIcon(github_icon_path))
            self.btn_github.setIconSize(QSize(icon_size, icon_size))
        self.btn_github.clicked.connect(lambda: webbrowser.open("https://github.com/CreateDDy"))

        self.btn_itch = QPushButton()
        self.btn_itch.setFixedSize(button_size, button_size)
        self.btn_itch.setCursor(Qt.PointingHandCursor)
        self.btn_itch.setStyleSheet(transparent_btn_style)
        itch_icon_path = os.path.join(base_path, "icons", "system_icons", "itch.png") 
        if os.path.exists(itch_icon_path):
            self.btn_itch.setIcon(QIcon(itch_icon_path))
            self.btn_itch.setIconSize(QSize(icon_size, icon_size))
        self.btn_itch.clicked.connect(lambda: webbrowser.open("https://createdd.itch.io/elden-ring-interactive-map"))

        self.btn_nexus = QPushButton()
        self.btn_nexus.setFixedSize(button_size, button_size)
        self.btn_nexus.setCursor(Qt.PointingHandCursor)
        self.btn_nexus.setStyleSheet(transparent_btn_style)
        nexus_icon_path = os.path.join(base_path, "icons", "system_icons", "nexus.png")
        if os.path.exists(nexus_icon_path):
            self.btn_nexus.setIcon(QIcon(nexus_icon_path))
            self.btn_nexus.setIconSize(QSize(icon_size, icon_size))
        self.btn_nexus.clicked.connect(lambda: webbrowser.open("https://www.nexusmods.com/eldenring/mods/10354"))

        bottom_corner_layout = QHBoxLayout()
        bottom_corner_layout.addStretch() 
        bottom_corner_layout.addWidget(self.btn_itch)
        bottom_corner_layout.addWidget(self.btn_nexus)
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
        
        icon_path = os.path.join(base_path, "icons", "system_icons", "MENU_Loading_02.png")
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
            except Exception:
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
                "items": "Предметы",
                "npc": "База NPC (В разработке)",
                "create": "Создать",
                "delete": "Удалить"
            },
            "en": {
                "map": "Interactive Map",
                "items": "Items",
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

    def on_items_clicked(self):
        if hasattr(self, "switch_to_items_callback"):
            self.switch_to_items_callback(self.current_lang)

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
            except Exception:
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
    def __init__(self, title, description, loot_data=None, image_name=None, resistances=None, phases=None, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Popup)
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.lang = "ru"
        if loot_data and isinstance(loot_data[0], dict):
            self.lang = loot_data[0].get("lang", "ru")

        cursor_path = os.path.join(base_path, "icons", "system_icons", "cursor.png")
        if os.path.exists(cursor_path):
            cursor_img = QPixmap(cursor_path).scaled(48, 36, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setCursor(QCursor(cursor_img, 0, 0))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(8)
        main_layout.setSizeConstraint(QVBoxLayout.SetFixedSize)

        self.setStyleSheet("""
            QDialog { background-color: rgba(20, 20, 20, 245); border: 2px solid #8b7355; border-radius: 5px; }
            QLabel { font-family: "Georgia", serif; color: #e8dcc2; }
        """)

        # --- ОТРИСОВКА БОССОВ ---
        if phases:
            # Если есть фазы - делаем две колонки
            phases_layout = QHBoxLayout()
            phases_layout.setSpacing(15)

            for phase in phases:
                phase_widget = QWidget()
                p_layout = QVBoxLayout(phase_widget)
                p_layout.setContentsMargins(0, 0, 0, 0)

                # Картинка фазы
                p_img = phase.get("image")
                if p_img:
                    img_path = get_img(p_img)
                    if os.path.exists(img_path):
                        img_label = QLabel()
                        pix = QPixmap(img_path).scaledToWidth(260, Qt.SmoothTransformation)
                        img_label.setPixmap(pix)
                        img_label.setAlignment(Qt.AlignCenter)
                        img_label.setStyleSheet("border: 1px solid #5a5a5a; border-radius: 4px; margin-bottom: 5px;")
                        p_layout.addWidget(img_label)

                # Имя фазы
                p_title = phase.get(f"title_{self.lang}", phase.get("title_ru", "Босс"))
                t_lbl = QLabel(p_title)
                t_lbl.setStyleSheet("font-size: 13pt; font-weight: bold; color: #ffaa00;")
                t_lbl.setAlignment(Qt.AlignCenter)
                t_lbl.setWordWrap(True)
                p_layout.addWidget(t_lbl)

                # Резисты фазы
                p_res = phase.get("resistances", {})
                if p_res:
                    self.render_boss_resistances(p_layout, p_res, self.lang)

                phases_layout.addWidget(phase_widget)

            main_layout.addLayout(phases_layout)

        else:
            # Обычный босс (одна колонка)
            if image_name:
                img_path = get_img(image_name)
                if os.path.exists(img_path):
                    img_label = QLabel()
                    pix = QPixmap(img_path).scaledToWidth(290, Qt.SmoothTransformation)
                    img_label.setPixmap(pix)
                    img_label.setAlignment(Qt.AlignCenter)
                    img_label.setStyleSheet("border: 1px solid #5a5a5a; border-radius: 4px; margin-bottom: 5px;")
                    main_layout.addWidget(img_label)

            if title:
                title_label = QLabel(title)
                title_label.setStyleSheet("font-size: 14pt; font-weight: bold; color: #ffaa00;")
                title_label.setWordWrap(True)
                main_layout.addWidget(title_label)

            if resistances:
                self.render_boss_resistances(main_layout, resistances, self.lang)

        # 3. Общее описание (ложится под фазами или обычным боссом)
        if description:
            desc_label = QLabel(description)
            desc_label.setStyleSheet("font-size: 11pt; color: #cbd5e1;")
            desc_label.setWordWrap(True)
            main_layout.addWidget(desc_label)

        # 5. Общий Лут
        if loot_data:
            loot_text = "Награды / Лут:" if self.lang == "ru" else "Rewards / Loot:"
            loot_title = QLabel(loot_text)
            loot_title.setStyleSheet("color: #888888; font-size: 11px; margin-top: 5px;")
            main_layout.addWidget(loot_title)

            for item in loot_data:
                item_label = LootLabel(item)
                main_layout.addWidget(item_label)

        self.setMinimumWidth(280)

    def render_boss_resistances(self, layout, res_data, lang):
        title_text = "Сопротивления:" if lang == "ru" else "Resistances:"
        res_title = QLabel(title_text)
        res_title.setStyleSheet("color: #d4a956; font-weight: bold; font-size: 12px; margin-top: 5px;")
        layout.addWidget(res_title)
        
        grid = QGridLayout()
        grid.setSpacing(4)
        
        dmg_keys = ["phys", "strike", "slash", "pierce", "magic", "fire", "lightning", "holy"]
        if lang == "ru":
            dmg_labels = ["Физ", "Дроб", "Руб", "Кол", "Маг", "Огн", "Мол", "Свят"]
        else:
            dmg_labels = ["Phy", "Str", "Sla", "Pie", "Mag", "Fir", "Lit", "Hol"]
        
        for i, (key, lbl) in enumerate(zip(dmg_keys, dmg_labels)):
            h_lbl = QLabel(lbl)
            h_lbl.setStyleSheet("color: #888; font-size: 10px; background: rgba(30,30,30,150); padding: 2px;")
            h_lbl.setAlignment(Qt.AlignCenter)
            
            v_lbl = QLabel(str(res_data.get(key, "-")))
            v_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
            v_lbl.setAlignment(Qt.AlignCenter)
            
            grid.addWidget(h_lbl, 0, i)
            grid.addWidget(v_lbl, 1, i)
            
        stat_keys = ["poison", "rot", "bleed", "frost", "sleep", "madness", "death", "poise"]
        if lang == "ru":
            stat_labels = ["Яд", "Гниль", "Кровь", "Обмор", "Сон", "Безм", "Смерт", "Баланс"]
        else:
            stat_labels = ["Psn", "Rot", "Bld", "Fro", "Slp", "Mad", "Dth", "Poi"]
        
        for i, (key, lbl) in enumerate(zip(stat_keys, stat_labels)):
            h_lbl = QLabel(lbl)
            h_lbl.setStyleSheet("color: #888; font-size: 10px; background: rgba(30,30,30,150); padding: 2px; margin-top: 5px;")
            h_lbl.setAlignment(Qt.AlignCenter)
            
            val = res_data.get(key, "-")
            if str(val) == "999" or val == "inf": val = "∞"
            
            v_lbl = QLabel(str(val))
            v_lbl.setStyleSheet("color: #cbd5e1; font-size: 11px;")
            v_lbl.setAlignment(Qt.AlignCenter)
            
            grid.addWidget(h_lbl, 2, i)
            grid.addWidget(v_lbl, 3, i)
            
        layout.addLayout(grid)

class ItemTooltip(QWidget):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setWindowFlags(Qt.ToolTip | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_ShowWithoutActivating)
        
        self.setStyleSheet("""
            QWidget { background-color: #2b2b2b; border: 1px solid #4a4a4a; border-radius: 4px; }
            QLabel { border: none; background: transparent; font-family: 'Georgia', serif; }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(6)
        
        lang = item_data.get("lang", "ru")
        
        # --- 1. ЗАГОЛОВОК ---
        title = QLabel(item_data.get("name", "Unknown Item"))
        title.setStyleSheet("color: #e8dcc2; font-size: 16px; font-weight: bold;")
        title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(title)
        
        main_layout.addWidget(self.create_divider())
        
        # --- 2. ИКОНКА ---
        icon_name = item_data.get("icon", "default.png")
        icon_path = get_img(icon_name)
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignCenter)
        if os.path.exists(icon_path):
            pix = QPixmap(icon_path).scaled(200, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(pix)
        else:
            icon_label.setFixedSize(200, 100)
        main_layout.addWidget(icon_label)
        main_layout.addWidget(self.create_divider())

        # --- 2.5 ОПИСАНИЕ ---
        desc = item_data.get("description", "")
        if desc and desc != "-":
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("color: #a89f91; font-style: italic; font-size: 12px;")
            desc_lbl.setAlignment(Qt.AlignCenter)
            desc_lbl.setWordWrap(True)
            main_layout.addWidget(desc_lbl)
            main_layout.addWidget(self.create_divider())
        
        # --- 3. ТИП И НАВЫК ---
        type_str = item_data.get("type", "")
        if type_str and type_str != "-":
            lbl = "Тип" if lang == "ru" else "Type"
            main_layout.addWidget(self.create_centered_block(lbl, type_str))
            main_layout.addWidget(self.create_divider())
            
        dmg_type = item_data.get("damage_type", "")
        if dmg_type and dmg_type != "-":
            lbl = "Тип урона" if lang == "ru" else "Damage Type"
            main_layout.addWidget(self.create_centered_block(lbl, dmg_type))
            main_layout.addWidget(self.create_divider())
            
        skill_name = item_data.get("skill_name", "")
        if skill_name and skill_name != "-":
            lbl = "Навык" if lang == "ru" else "Skill"
            skill_cost = item_data.get("skill_cost", "-")
            main_layout.addWidget(self.create_centered_block(lbl, f"{skill_name}   |   {skill_cost}"))
            main_layout.addWidget(self.create_divider())
        summon_params = item_data.get("summon_params", {})
        if summon_params:
            self.render_summon_params(main_layout, summon_params, lang)
            main_layout.addWidget(self.create_divider())

        # --- 4. ТАБЛИЦА СТАТОВ ИЛИ БРОНИ ---
        attack_data = item_data.get("attack", {})
        defense_data = item_data.get("defense", {})
        resistances = item_data.get("resistances", {})
        is_armor = "Броня" in type_str or "Сет" in type_str or "Armor" in type_str
        if is_armor:
            if defense_data or resistances:
                self.render_armor_stats(main_layout, defense_data, resistances, item_data.get("weight", 0.0), lang)
                main_layout.addWidget(self.create_divider())
        else:
            has_stats = False
            if attack_data and any(v != 0 for v in attack_data.values()):
                has_stats = True
            if defense_data and any(v != 0 for v in defense_data.values()):
                has_stats = True
                
            if has_stats:
                self.render_stats_table(main_layout, attack_data, defense_data, item_data.get("weight", 0.0), lang)
                main_layout.addWidget(self.create_divider())
            
        # --- 5. БОНУСЫ И ТРЕБОВАНИЯ ---
        scaling = item_data.get("scaling", {})
        reqs = item_data.get("requirements", {})
        
        has_scaling = any(v not in ["-", "", 0] for v in scaling.values())
        has_reqs = any(v != 0 and v != "-" for v in reqs.values())
        
        if has_scaling or has_reqs:
            self.render_scaling_block(main_layout, scaling, reqs, lang)
            main_layout.addWidget(self.create_divider())

        # --- 6. ПАРАМЕТРЫ МАГИИ (НОВЫЙ БЛОК) ---
        magic_params = item_data.get("magic_params", {})
        if magic_params:
            self.render_magic_params(main_layout, magic_params, lang)
            main_layout.addWidget(self.create_divider())

        # --- 7. ЭФФЕКТЫ ---
        effects = item_data.get("effects", "")
        if effects and effects != "-":
            eff_title = QLabel("Эффекты" if lang == "ru" else "Passive Effects")
            eff_title.setStyleSheet("color: #e8dcc2; font-weight: bold; font-size: 12px;")
            eff_title.setAlignment(Qt.AlignCenter)
            main_layout.addWidget(eff_title)
            
            eff_lbl = QLabel(effects)
            eff_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
            eff_lbl.setAlignment(Qt.AlignCenter)
            eff_lbl.setWordWrap(True)
            main_layout.addWidget(eff_lbl)

    def create_divider(self):
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: #4a4a4a;")
        return line
        
    def create_centered_block(self, title_text, value_text):
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        
        title = QLabel(title_text)
        title.setStyleSheet("color: #e8dcc2; font-weight: bold; font-size: 12px;")
        title.setAlignment(Qt.AlignCenter)
        
        value = QLabel(value_text)
        value.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        value.setAlignment(Qt.AlignCenter)
        
        layout.addWidget(title)
        layout.addWidget(value)
        return widget
    
    def render_summon_params(self, main_layout, summon_params, lang):
        lbl_title = QLabel("Параметры призыва" if lang == "ru" else "Summon Parameters")
        lbl_title.setStyleSheet("color: #e8dcc2; font-weight: bold; font-size: 12px;")
        lbl_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(lbl_title)
        
        grid = QGridLayout()
        grid.setSpacing(4)
        
        fp_cost = summon_params.get("fp_cost", 0)
        hp_cost = summon_params.get("hp_cost", 0)
        
        col = 0
        if fp_cost > 0:
            lbl_fp = QLabel("Расход ОК" if lang == "ru" else "FP Cost")
            lbl_fp.setStyleSheet("color: #888; font-size: 11px;")
            val_fp = QLabel(str(fp_cost))
            val_fp.setStyleSheet("color: #cbd5e1; font-size: 12px;")
            val_fp.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            grid.addWidget(lbl_fp, 0, col)
            grid.addWidget(val_fp, 0, col + 1)
            col += 2
            
        if hp_cost > 0:
            lbl_hp = QLabel("Расход ОЗ" if lang == "ru" else "HP Cost")
            lbl_hp.setStyleSheet("color: #888; font-size: 11px;")
            val_hp = QLabel(str(hp_cost))
            val_hp.setStyleSheet("color: #ff4a4a; font-size: 12px;") 
            val_hp.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            grid.addWidget(lbl_hp, 0, col)
            grid.addWidget(val_hp, 0, col + 1)
            
        main_layout.addLayout(grid)

    def render_magic_params(self, main_layout, magic_params, lang):
        lbl_title = QLabel("Параметры" if lang == "ru" else "Parameters")
        lbl_title.setStyleSheet("color: #e8dcc2; font-weight: bold; font-size: 12px;")
        lbl_title.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(lbl_title)
        
        grid = QGridLayout()
        grid.setSpacing(4)
        
        lbl_fp = QLabel("Расход ОК" if lang == "ru" else "FP Cost")
        lbl_slots = QLabel("Ячейки" if lang == "ru" else "Slots")
        lbl_dur = QLabel("Длительность" if lang == "ru" else "Duration")
        lbl_price = QLabel("Цена" if lang == "ru" else "Sell Value")
        
        val_fp = QLabel(str(magic_params.get("fp_cost", "-")))
        val_slots = QLabel(str(magic_params.get("slots", "-")))
        val_dur = QLabel(str(magic_params.get("duration", "-")))
        val_price = QLabel(str(magic_params.get("price", "-")))
        
        for lbl in [lbl_fp, lbl_slots, lbl_dur, lbl_price]:
            lbl.setStyleSheet("color: #888; font-size: 11px;")
        for val in [val_fp, val_slots, val_dur, val_price]:
            val.setStyleSheet("color: #cbd5e1; font-size: 12px;")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
        grid.addWidget(lbl_fp, 0, 0)
        grid.addWidget(val_fp, 0, 1)
        grid.addWidget(lbl_slots, 0, 2)
        grid.addWidget(val_slots, 0, 3)
        
        grid.addWidget(lbl_dur, 1, 0)
        grid.addWidget(val_dur, 1, 1)
        grid.addWidget(lbl_price, 1, 2)
        grid.addWidget(val_price, 1, 3)
        
        main_layout.addLayout(grid)
    
    def render_armor_stats(self, main_layout, defense_data, resistances, weight, lang):
        stats_layout = QGridLayout()
        stats_layout.setSpacing(4)

        if lang == "ru":
            def_labels = ["Физич.", "Дробящий", "Рубящий", "Колющий", "Магия", "Огонь", "Молния", "Святое"]
            res_labels = ["Иммунитет", "Живучесть", "Концент.", "Физ. мощь", "Баланс"]
            header_def = "🛡 Защита"
            header_res = "🛡 Сопротивляемость"
            weight_text = "Вес"
        else:
            def_labels = ["Physical", "Strike", "Slash", "Pierce", "Magic", "Fire", "Lightning", "Holy"]
            res_labels = ["Immunity", "Robustness", "Focus", "Vitality", "Poise"]
            header_def = "🛡 Damage Negation"
            header_res = "🛡 Resistance"
            weight_text = "Weight"

        def_keys = ["physical", "strike", "slash", "pierce", "magic", "fire", "lightning", "holy"]
        def_colors = ["#cbd5e1", "#cbd5e1", "#cbd5e1", "#cbd5e1", "#5c92ff", "#ff6b4a", "#e6cc45", "#b388ff"]
        res_keys = ["immunity", "robustness", "focus", "vitality", "poise"]

        lbl_def_head = QLabel(header_def)
        lbl_def_head.setStyleSheet("color: #d4a956; font-weight: bold; font-size: 13px;")
        lbl_def_head.setAlignment(Qt.AlignCenter)
        
        lbl_res_head = QLabel(header_res)
        lbl_res_head.setStyleSheet("color: #d4a956; font-weight: bold; font-size: 13px;")
        lbl_res_head.setAlignment(Qt.AlignCenter)

        stats_layout.addWidget(lbl_def_head, 0, 0, 1, 2)
        stats_layout.addWidget(lbl_res_head, 0, 2, 1, 2)

        for i in range(8):
            lbl = QLabel(def_labels[i])
            lbl.setStyleSheet(f"color: {def_colors[i]}; font-size: 12px;")
            val = QLabel(str(defense_data.get(def_keys[i], 0)))
            val.setStyleSheet("color: #cbd5e1; font-size: 12px;")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            stats_layout.addWidget(lbl, i + 1, 0)
            stats_layout.addWidget(val, i + 1, 1)
        for i in range(5):
            lbl = QLabel(res_labels[i])
            lbl.setStyleSheet("color: #a89f91; font-size: 12px;")
            val = QLabel(str(resistances.get(res_keys[i], 0)))
            val.setStyleSheet("color: #cbd5e1; font-size: 12px;")
            val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            
            stats_layout.addWidget(lbl, i + 1, 2)
            stats_layout.addWidget(val, i + 1, 3)

        lbl_w = QLabel(weight_text)
        lbl_w.setStyleSheet("color: #888; font-size: 12px; margin-top: 5px;")
        val_w = QLabel(str(weight))
        val_w.setStyleSheet("color: #cbd5e1; font-size: 12px; margin-top: 5px;")
        val_w.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        stats_layout.addWidget(lbl_w, 8, 2)
        stats_layout.addWidget(val_w, 8, 3)

        main_layout.addLayout(stats_layout)

    def render_stats_table(self, main_layout, attack_data, defense_data, weight, lang):
        stats_layout = QGridLayout()
        stats_layout.setSpacing(4)
        
        lbl_atk = QLabel("⚔ Атака" if lang == "ru" else "⚔ Attack")
        lbl_atk.setStyleSheet("color: #d4a956; font-weight: bold; font-size: 13px;")
        lbl_atk.setAlignment(Qt.AlignCenter)
        
        lbl_def = QLabel("🛡 Защита" if lang == "ru" else "🛡 Defense")
        lbl_def.setStyleSheet("color: #d4a956; font-weight: bold; font-size: 13px;")
        lbl_def.setAlignment(Qt.AlignCenter)
        
        stats_layout.addWidget(lbl_atk, 0, 0, 1, 2)
        stats_layout.addWidget(lbl_def, 0, 2, 1, 2)
        
        if lang == "ru":
            rows = [
                ("Физическ.", attack_data.get("physical", 0), defense_data.get("physical", 0), "#cbd5e1"),
                ("Магия", attack_data.get("magic", 0), defense_data.get("magic", 0), "#5c92ff"),
                ("Огонь", attack_data.get("fire", 0), defense_data.get("fire", 0), "#ff6b4a"),
                ("Молния", attack_data.get("lightning", 0), defense_data.get("lightning", 0), "#e6cc45"),
                ("Святое", attack_data.get("holy", 0), defense_data.get("holy", 0), "#b388ff"),
            ]
            crit_text, guard_text, weight_text = "Крит. удар", "Усил. блок", "Вес"
        else:
            rows = [
                ("Physical", attack_data.get("physical", 0), defense_data.get("physical", 0), "#cbd5e1"),
                ("Magic", attack_data.get("magic", 0), defense_data.get("magic", 0), "#5c92ff"),
                ("Fire", attack_data.get("fire", 0), defense_data.get("fire", 0), "#ff6b4a"),
                ("Lightning", attack_data.get("lightning", 0), defense_data.get("lightning", 0), "#e6cc45"),
                ("Holy", attack_data.get("holy", 0), defense_data.get("holy", 0), "#b388ff"),
            ]
            crit_text, guard_text, weight_text = "Critical", "Guard Boost", "Weight"
        
        for i, (name, atk_val, def_val, color) in enumerate(rows, start=1):
            self.add_stat_row(stats_layout, i, name, atk_val, def_val, color)
            
        self.add_single_stat(stats_layout, 6, 0, crit_text, attack_data.get("crit", 100), "#ff4a4a")
        self.add_single_stat(stats_layout, 6, 2, guard_text, defense_data.get("guard_boost", 0), "#63d471")
        self.add_single_stat(stats_layout, 7, 2, weight_text, weight, "#cbd5e1")
        
        main_layout.addLayout(stats_layout)

    def render_scaling_block(self, main_layout, scaling, reqs, lang):
        attr_layout = QGridLayout()
        attr_layout.setSpacing(4)
        
        headers = ["Сил", "Лов", "Муд", "Вер", "Кол"] if lang == "ru" else ["Str", "Dex", "Int", "Fai", "Arc"]
        keys = ["str", "dex", "int", "fth", "arc"]
        
        lbl_scale = QLabel("Бонусы" if lang == "ru" else "Attribute Scaling")
        lbl_scale.setStyleSheet("color: #e8dcc2; font-weight: bold; font-size: 12px;")
        lbl_scale.setAlignment(Qt.AlignCenter)
        attr_layout.addWidget(lbl_scale, 0, 0, 1, 5)
        
        for col, (head, key) in enumerate(zip(headers, keys)):
            h_lbl = QLabel(head)
            h_lbl.setStyleSheet("color: #888; font-size: 11px;")
            h_lbl.setAlignment(Qt.AlignCenter)
            
            v_lbl = QLabel(str(scaling.get(key, "-")))
            v_lbl.setStyleSheet("color: #cbd5e1; font-size: 12px;")
            v_lbl.setAlignment(Qt.AlignCenter)
            
            attr_layout.addWidget(h_lbl, 1, col)
            attr_layout.addWidget(v_lbl, 2, col)
        
        lbl_req = QLabel("Требования" if lang == "ru" else "Attributes Required")
        lbl_req.setStyleSheet("color: #e8dcc2; font-weight: bold; font-size: 12px; margin-top: 8px;")
        lbl_req.setAlignment(Qt.AlignCenter)
        attr_layout.addWidget(lbl_req, 3, 0, 1, 5)
        
        for col, key in enumerate(keys):
            val = reqs.get(key, 0)
            r_lbl = QLabel(str(val) if val > 0 else "-")
            r_color = "#e8dcc2" if val > 0 else "#555"
            r_lbl.setStyleSheet(f"color: {r_color}; font-size: 12px;")
            r_lbl.setAlignment(Qt.AlignCenter)
            attr_layout.addWidget(r_lbl, 4, col)
            
        main_layout.addLayout(attr_layout)

    def add_stat_row(self, layout, row, name, atk_val, def_val, color):
        self.add_single_stat(layout, row, 0, name, atk_val, color)
        self.add_single_stat(layout, row, 2, name, def_val, color)
        
    def add_single_stat(self, layout, row, col_start, name, val, color):
        lbl_name = QLabel(name)
        lbl_name.setStyleSheet(f"color: {color}; font-size: 12px;")
        
        lbl_val = QLabel(str(val))
        lbl_val.setStyleSheet("color: #cbd5e1; font-size: 12px;")
        lbl_val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addWidget(lbl_name, row, col_start)
        layout.addWidget(lbl_val, row, col_start + 1)

class LootLabel(QLabel):
    def __init__(self, item_data, parent=None):
        super().__init__(parent)
        self.item_data = item_data
        self.is_raw = item_data.get("is_raw", False)
        
        name = item_data.get("name", "Предмет")
        self.setText(f"♦ {name}")
        
        if self.is_raw:
            self.setStyleSheet("""
                QLabel {
                    color: #cbd5e1; font-size: 13px; padding: 6px;
                    background-color: rgba(40, 40, 40, 100);
                    border: 1px solid #4a4a4a; border-radius: 3px;
                    font-family: 'Georgia', serif;
                }
            """)
        else:
            self.setStyleSheet("""
                QLabel {
                    color: #e8dcc2; font-size: 13px; padding: 6px;
                    background-color: rgba(40, 40, 40, 150);
                    border: 1px solid #5a5a5a; border-radius: 3px;
                    font-family: 'Georgia', serif;
                }
                QLabel:hover { background-color: rgba(70, 70, 70, 200); border-color: #d4a956; color: #d4a956; }
            """)
            self.setCursor(Qt.PointingHandCursor)
            
        self.tooltip_window = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.is_raw: return 
            if not self.tooltip_window:
                self.tooltip_window = ItemTooltip(self.item_data, parent=self.window())
            
            if self.tooltip_window.isVisible():
                self.tooltip_window.hide()
            else:
                self.tooltip_window.adjustSize()
                
                main_rect = self.window().geometry()
                screen_rect = QApplication.desktop().availableGeometry(main_rect.center())
                
                w = self.tooltip_window.width()
                h = self.tooltip_window.height()
                x = main_rect.right() + 5
                y = main_rect.top()
                if x + w > screen_rect.right():
                    x = main_rect.left() - w - 5
                if y + h > screen_rect.bottom():
                    y = screen_rect.bottom() - h - 5
                    
                self.tooltip_window.move(x, y)
                self.tooltip_window.show()
                
        super().mousePressEvent(event)

class ItemsScreen(QWidget):
    def __init__(self, items_data, back_callback, lang="ru"):
        super().__init__()
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet("""
            ItemsScreen { background-color: #2b2b2b; }
            QTreeWidget { background-color: #1a1a1a; color: #c4bca2; border: 1px solid #4a4a4a; font-size: 14px; }
            QScrollArea { background-color: #2b2b2b; border: none; }
            QWidget#DetailsContainer { background-color: #2b2b2b; }
            QLabel { color: #c4bca2; font-family: 'Georgia', serif; }
            QLineEdit { background-color: #1a1a1a; color: #cbd5e1; border: 1px solid #4a4a4a; border-radius: 4px; padding: 8px; }
        """)
        self.items_data = items_data
        self.lang = lang
        self.back_callback = back_callback
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # --- ШАПКА ---
        header_layout = QHBoxLayout()
        title_text = "БАЗА ПРЕДМЕТОВ" if lang == "ru" else "ITEM DATABASE"
        title = QLabel(title_text)
        title.setStyleSheet("color: #d4a956; font-size: 24px; font-weight: bold; font-family: 'Georgia', serif;")
        
        btn_back = QPushButton("В главное меню" if lang == "ru" else "Back to Menu")
        btn_back.setFixedSize(160, 40)
        btn_back.setCursor(Qt.PointingHandCursor)
        btn_back.setStyleSheet("""
            QPushButton { background-color: #2d2d2d; color: #e8dcc2; border: 1px solid #8b7355; border-radius: 4px; font-size: 14px; }
            QPushButton:hover { background-color: #3d3d3d; border-color: #ffaa00; }
        """)
        btn_back.clicked.connect(self.back_callback)
        
        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(btn_back)
        main_layout.addLayout(header_layout)
        
        # --- РАЗДЕЛИТЕЛЬ (Слева дерево, справа карточка) ---
        splitter = QSplitter(Qt.Horizontal)
        
        # ЛЕВАЯ ПАНЕЛЬ: Поиск + Деревья
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # Живой поиск
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("Поиск предметов..." if lang == "ru" else "Search items...")
        self.search_bar.setStyleSheet("""
            QLineEdit { 
                background-color: #2d2d2d; color: #cbd5e1; 
                border: 1px solid #4a4a4a; border-radius: 4px; 
                padding: 8px; font-size: 14px; 
            }
            QLineEdit:focus { border-color: #d4a956; }
        """)
        self.search_bar.textChanged.connect(self.filter_tree)
        left_layout.addWidget(self.search_bar)
        
        # --- КОНТЕЙНЕР ДЛЯ ДВУХ ДЕРЕВЬЕВ ---
        trees_layout = QHBoxLayout()
        trees_layout.setSpacing(10)
        
        tree_style = """
            QTreeWidget { background-color: #1c1c1c; color: #cbd5e1; border: 1px solid #4a4a4a; font-size: 14px; }
            QTreeWidget::item:hover { background-color: #2a2a2a; }
            QTreeWidget::item:selected { background-color: #3d3d3d; color: #d4a956; }
        """
        
        self.tree_left = QTreeWidget()
        self.tree_left.setHeaderHidden(True)
        self.tree_left.setStyleSheet(tree_style)
        self.tree_left.itemClicked.connect(self.on_item_clicked)
        
        self.tree_right = QTreeWidget()
        self.tree_right.setHeaderHidden(True)
        self.tree_right.setStyleSheet(tree_style)
        self.tree_right.itemClicked.connect(self.on_item_clicked)
        
        trees_layout.addWidget(self.tree_left)
        trees_layout.addWidget(self.tree_right)
        left_layout.addLayout(trees_layout)
        # -----------------------------------
        
        splitter.addWidget(left_panel)
        
        # ПРАВАЯ ПАНЕЛЬ: Место под карточку предмета
        self.details_scroll = QScrollArea()
        self.details_scroll.setWidgetResizable(True)
        self.details_scroll.setStyleSheet("QScrollArea { border: none; background-color: transparent; }")
        
        self.details_container = QWidget()
        self.details_container.setObjectName("DetailsContainer")
        self.details_layout = QVBoxLayout(self.details_container)
        self.details_layout.setAlignment(Qt.AlignTop)
        self.details_scroll.setWidget(self.details_container)

        splitter.setHandleWidth(0) 
        splitter.setStyleSheet("QSplitter::handle { background: transparent; }")
        splitter.setCollapsible(0, False) 
        left_panel.setFixedWidth(800)
        
        splitter.addWidget(self.details_scroll)
        splitter.setSizes([800, 400])
        main_layout.addWidget(splitter)
        
        self.populate_tree()

    def populate_tree(self):
        categories = {}
        for item_id, data in self.items_data.items():
            # Игнорируем массивы маркеров и прочий не-предметный мусор
            if not isinstance(data, dict):
                continue

            data["item_id"] = item_id

            # Добавили or "", чтобы скрипт не отваливался на .lower(), если в json где-то прописан null
            item_type = data.get(f"type_{self.lang}", data.get("type_ru", data.get("type", ""))) or ""
            weapon_type = data.get(f"weapon_type_{self.lang}", data.get("weapon_type_ru", "-")) or "-"

            # Приводим к нижнему регистру для надежности
            w_type_lower = weapon_type.lower()
            
            if "Талисман" in item_type or "Talisman" in item_type:
                cat_name = "Талисманы" if self.lang == "ru" else "Talismans"
                sub_name = ""
            # ...
            elif "Ключев" in item_type or "Key" in item_type:
                cat_name = "Ключевые предметы" if self.lang == "ru" else "Key Items"
                sub_name = weapon_type if weapon_type and weapon_type != "-" else ""    
            # ...   
            elif item_type in ["Молитва", "Incantation", "Чары", "Sorcery"]:
                cat_name = "Магия" if self.lang == "ru" else "Magic"
                sub_name = item_type
            elif "shield" in w_type_lower or "щит" in w_type_lower:
                cat_name = "Щиты" if self.lang == "ru" else "Shields"
                sub_name = "" 
            elif weapon_type and weapon_type != "-":
                cat_name = "Оружие" if self.lang == "ru" else "Weapons"
                sub_name = weapon_type
            elif "Прах" in item_type or "Ashes" in item_type:
                cat_name = "Прах" if self.lang == "ru" else "Ashes"
                sub_name = ""
            elif "Сет" in item_type or "Броня" in item_type or "Armor" in item_type:
                cat_name = "Броня" if self.lang == "ru" else "Armor"
                sub_name = ""
            else:
                cat_name = "Предметы" if self.lang == "ru" else "Items"
                sub_name = item_type if item_type and item_type != "-" else "Разное"

            if cat_name not in categories:
                categories[cat_name] = {}
            if sub_name not in categories[cat_name]:
                categories[cat_name][sub_name] = []
                
            categories[cat_name][sub_name].append(data)

        self.tree_left.clear()
        self.tree_right.clear()
        
        # Не забудь добавить Щиты в левый список, если хочешь их слева
        left_categories = ["Оружие", "Щиты", "Броня", "Талисманы", "Weapons", "Shields", "Armor", "Talismans"]
        
        for cat_name, subcategories in categories.items():
            target_tree = self.tree_left if cat_name in left_categories else self.tree_right
            
            cat_item = QTreeWidgetItem(target_tree, [cat_name])
            cat_item.setForeground(0, QColor("#d4a956"))
            
            for sub_name, items in subcategories.items():
                parent_for_items = cat_item
                
                if sub_name:
                    sub_item = QTreeWidgetItem(cat_item, [sub_name])
                    sub_item.setForeground(0, QColor("#a89f91"))
                    parent_for_items = sub_item
                    
                for item_data in items:
                    name = item_data.get(f"name_{self.lang}", item_data.get("name_ru", "Unknown"))
                    leaf_item = QTreeWidgetItem(parent_for_items, [f"♦ {name}"])
                    leaf_item.setData(0, Qt.UserRole, item_data)
                    
        self.tree_left.collapseAll()
        self.tree_right.collapseAll()
    #ПОИСК
    def filter_tree(self, text):
        search_text = text.lower()
        
        def filter_node(item):
            match = search_text in item.text(0).lower()
            child_match = False
            
            for i in range(item.childCount()):
                child = item.child(i)
                if filter_node(child):
                    child_match = True
            if item.childCount() == 0:
                item.setHidden(not match)
                return match
            else:
                show_folder = match or child_match
                item.setHidden(not show_folder)
                if show_folder and search_text: 
                    item.setExpanded(True)
                return show_folder
        for i in range(self.tree_left.topLevelItemCount()):
            filter_node(self.tree_left.topLevelItem(i))
            
        for i in range(self.tree_right.topLevelItemCount()):
            filter_node(self.tree_right.topLevelItem(i))

    def on_item_clicked(self, item, column):
        item_data = item.data(0, Qt.UserRole)
        if not item_data: return
            
        for i in reversed(range(self.details_layout.count())): 
            widget = self.details_layout.itemAt(i).widget()
            if widget: widget.setParent(None)
                
        display_data = item_data.copy()
        display_data["lang"] = self.lang
        display_data["name"] = item_data.get(f"name_{self.lang}", item_data.get("name_ru", ""))

        w_type = item_data.get(f"weapon_type_{self.lang}", "-")
        display_data["type"] = w_type if w_type != "-" else item_data.get(f"type_{self.lang}", "")
        
        display_data["damage_type"] = item_data.get(f"damage_type_{self.lang}", "")
        display_data["skill_name"] = item_data.get(f"skill_name_{self.lang}", "")

        # Забираем эффекты (учитываем и effect, и effects)
        display_data["effects"] = item_data.get(f"effects_{self.lang}",
                                  item_data.get("effects_ru",
                                  item_data.get(f"effect_{self.lang}",
                                  item_data.get("effect_ru", ""))))

        # Забираем лорное описание
        display_data["description"] = item_data.get(f"description_{self.lang}", item_data.get("description_ru", ""))


        card = ItemTooltip(display_data, self)
        card.setWindowFlags(Qt.Widget) 
        card.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.details_layout.addWidget(card)
        
        target_id = item_data.get("item_id")
        
        if target_id:
            self.btn_location = QPushButton("Местонахождение" if self.lang == "ru" else "Location")
            self.btn_location.setStyleSheet("""
                QPushButton { background-color: #2d2d2d; color: #e8dcc2; border: 1px solid #8b7355; border-radius: 4px; padding: 10px; font-size: 14px; margin-top: 10px; }
                QPushButton:hover { background-color: #3d3d3d; border-color: #ffaa00; }
            """)
            self.btn_location.setCursor(Qt.PointingHandCursor)
            self.btn_location.clicked.connect(lambda checked, i=target_id: self.jump_to_map(i))
            self.details_layout.addWidget(self.btn_location)
    def jump_to_map(self, item_id):
        if hasattr(self, 'jump_callback') and self.jump_callback:
            self.jump_callback(item_id)