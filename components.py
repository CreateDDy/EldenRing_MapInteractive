import os
import sys
import json
from PyQt5.QtWidgets import (QGraphicsPixmapItem,QInputDialog, QGraphicsView, QPushButton,
                             QGraphicsScene, QToolTip, QGridLayout, QDialog, QGraphicsItem
                             ,QLineEdit, QVBoxLayout, QHBoxLayout, QLabel)
from PyQt5.QtGui import (QPixmap, QPainter, QBrush, QColor, QIcon)
from PyQt5.QtCore import Qt, QSize, QTimer
from interface import MarkerInfoWindow

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))

class MapMarker(QGraphicsPixmapItem):
    def __init__(self, icon_path, x, y, name, category, map_layer, overlay_path=None, custom_size=None, toggle_callback=None, marker_id=None, initial_completed=False):
        super().__init__()
        self.name_text = name
        self.category = category
        self.map_layer = map_layer
        self.has_overlay = bool(overlay_path)
        self.is_completed = initial_completed
        self.toggle_callback = toggle_callback
        self.marker_id = marker_id

        if custom_size:
            base_size = custom_size
        else:
            base_size = 112 if self.has_overlay else 46

        self.base_pixmap = QPixmap(icon_path).scaled(
            base_size, base_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        )

        if self.has_overlay and overlay_path:
            overlay_size = 28
            self.combined_pixmap = QPixmap(self.base_pixmap)
            painter = QPainter(self.combined_pixmap)
            overlay_pix = QPixmap(overlay_path).scaled(
                overlay_size, overlay_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            x_pos = (self.combined_pixmap.width() - overlay_size) // 2
            y_pos = (self.combined_pixmap.height() - overlay_size) // 2
            
            painter.drawPixmap(x_pos, y_pos, overlay_pix)
            painter.end()
        else:
            self.combined_pixmap = None

        if self.has_overlay:
            self.setPixmap(self.base_pixmap if self.is_completed else self.combined_pixmap)
        else:
            self.setPixmap(self.base_pixmap)
            self.setOpacity(0.4 if self.is_completed else 1.0)

        self.setOffset(-self.base_pixmap.width() / 2, -self.base_pixmap.height() / 2)
        self.setPos(x, y)
        self.setToolTip(name)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsPixmapItem.ItemIgnoresTransformations, True)

        # Click timer
        self.click_timer = QTimer()
        self.click_timer.setSingleShot(True)
        self.click_timer.timeout.connect(self.process_single_click)
        self.last_click_pos = None

    def add_info_mark(self):
        if not getattr(self, "note", "") and not getattr(self, "loot", "") and not getattr(self, "loot_data", []):
            return
        info_path = os.path.join(base_path, "icons", "system_icons", "descr.png")
        if not os.path.exists(info_path):
            return
            
        info_pix = QPixmap(info_path).scaled(20, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        offset_x = self.base_pixmap.width() - info_pix.width()
        offset_y = 0
        
        new_base = self.base_pixmap.copy()
        painter = QPainter(new_base)
        painter.drawPixmap(offset_x, offset_y, info_pix)
        painter.end()
        self.base_pixmap = new_base

        if self.has_overlay and self.combined_pixmap:
            new_comb = self.combined_pixmap.copy()
            painter_comb = QPainter(new_comb)
            painter_comb.drawPixmap(new_comb.width() - info_pix.width(), 0, info_pix)
            painter_comb.end()
            self.combined_pixmap = new_comb

        if self.has_overlay:
            self.setPixmap(self.base_pixmap if self.is_completed else self.combined_pixmap)
        else:
            self.setPixmap(self.base_pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.last_click_pos = event.screenPos()
            self.click_timer.start(200)
            self.ungrabMouse()
            event.accept()
            return
        super().mousePressEvent(event)

    def process_single_click(self):
        title = getattr(self, "name_text", "Unknown object")
        description = getattr(self, "note", "")
        old_text_loot = getattr(self, "loot", "")
        loot_data = getattr(self, "loot_data", []) # Достаем наши новые предметы
        
        final_text = description
        if old_text_loot:
            final_text += f"\n\nЛут:\n{old_text_loot}"

        if not final_text and not loot_data:
            return

        self.info_dialog = MarkerInfoWindow(title, final_text, loot_data)
        self.info_dialog.adjustSize()

        if self.last_click_pos:
            x = self.last_click_pos.x() - (self.info_dialog.width() // 2)
            y = self.last_click_pos.y() - self.info_dialog.height() - 15
            self.info_dialog.move(int(x), int(y))

        self.info_dialog.show()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.click_timer.stop()
            self.is_completed = not self.is_completed

            if self.has_overlay:
                self.setPixmap(self.base_pixmap if self.is_completed else self.combined_pixmap)
            else:
                self.setOpacity(0.4 if self.is_completed else 1.0)

            if self.toggle_callback:
                self.toggle_callback(self.category, self.marker_id, self.is_completed)

            event.accept()
            return
        super().mouseDoubleClickEvent(event)

class RegionMarker(QGraphicsPixmapItem):
    def __init__(self, icon_path, x, y, grace_name, category, map_layer="surface", toggle_callback=None, marker_id=None, initial_completed=False):
        super().__init__()
        self.name_text = grace_name
        self.category = category 
        self.map_layer = map_layer 
        self.is_cleared = initial_completed
        self.toggle_callback = toggle_callback
        self.marker_id = marker_id
        
        icon_size = 46
        original_pixmap = QPixmap(icon_path)
            
        self.setPixmap(original_pixmap.scaled(
            icon_size, icon_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
        ))
        
        if self.is_cleared:
            self.setOpacity(0.3)
            
        self.setOffset(-icon_size / 2, -icon_size / 2)
        self.setPos(x, y)
        self.setToolTip(grace_name)
        self.setAcceptHoverEvents(True)
        self.setFlag(QGraphicsPixmapItem.ItemIgnoresTransformations, True)

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_cleared = not self.is_cleared
            self.setOpacity(0.3 if self.is_cleared else 1.0)
            
            if self.toggle_callback:
                self.toggle_callback(self.category, self.marker_id, self.is_cleared)
            event.accept()

    def hoverLeaveEvent(self, event):
        QToolTip.hideText() 
        super().hoverLeaveEvent(event)

class WaypointSelector(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setStyleSheet("background-color: #1c1c1c; border: 2px solid #8b7355; border-radius: 5px;")
        self.selected_icon = None

        layout = QGridLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        self.icons = [
            "wp_sword.png", "wp_skull.png", "wp_chest.png", "wp_leaf.png",
            "wp_diamond.png", "wp_flag.png", "wp_fire.png",
            "wp_house.png", "wp_beast.png", "wp_npc.png"
        ]

        row, col = 0, 0
        for icon_name in self.icons:
            btn = QPushButton()
            btn.setFixedSize(50, 50)
            btn.setCursor(Qt.PointingHandCursor)
            
            icon_path = os.path.join(base_path, "icons", "waypoint_icons", icon_name)  

            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(32, 32))

            btn.setStyleSheet("""
                QPushButton { background-color: #2d2d2d; border: 1px solid #5a5a5a; } 
                QPushButton:hover { background-color: #555; border-color: #d4a956; }
            """)
            btn.clicked.connect(lambda checked, name=icon_name: self.select_icon(name))

            layout.addWidget(btn, row, col)
            col += 1
            if col > 4: 
                col = 0
                row += 1

    def select_icon(self, icon_name):
        self.selected_icon = icon_name
        self.accept()

class UserWaypoint(QGraphicsPixmapItem):
    def __init__(self, icon_path, x, y, map_layer, remove_callback, marker_id, note=""):
        super().__init__()
        self.icon_path = icon_path 
        self.note = note
        self.base_pixmap = QPixmap(icon_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(self.base_pixmap)
        self.setOffset(-self.base_pixmap.width() / 2, -self.base_pixmap.height() / 2)
        self.setPos(x, y)
        self.setZValue(100)
        self.map_layer = map_layer
        self.remove_callback = remove_callback
        self.marker_id = marker_id
        
        self.setFlag(QGraphicsItem.ItemIgnoresTransformations)
        self.setAcceptedMouseButtons(Qt.RightButton | Qt.LeftButton)
        self.add_info_mark()

    def add_info_mark(self):
        if not self.note:
            return
            
        info_path = os.path.join(base_path, "icons", "descr.png")
        if not os.path.exists(info_path):
            print(f"Icon not found: {info_path}")
            return
        
        info_pix = QPixmap(info_path).scaled(20, 24, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        offset_x = self.base_pixmap.width() - info_pix.width()
        new_base = self.base_pixmap.copy()
        painter = QPainter(new_base)
        painter.drawPixmap(offset_x, 0, info_pix)
        painter.end()
        self.base_pixmap = new_base
        self.setPixmap(self.base_pixmap)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.note:
            self.info_dialog = MarkerInfoWindow("", self.note)
            self.info_dialog.adjustSize()
            global_pos = event.screenPos()
            x = global_pos.x() - (self.info_dialog.width() // 2)
            y = global_pos.y() - self.info_dialog.height() - 15
            self.info_dialog.move(int(x), int(y))
            self.info_dialog.show()
            event.accept()
        super().mousePressEvent(event)

class WaypointInputDialog(QDialog):
    def __init__(self, parent=None, label_text="Текст метки (необязательно):"):
        super().__init__(parent)
        self.setWindowFlags(Qt.Popup | Qt.FramelessWindowHint)
        self.setFixedSize(300, 110)
        self.setStyleSheet("""
            QDialog { background-color: #1c1c1c; border: 2px solid #8b7355; border-radius: 5px; }
            QLabel { color: #d4a956; font-family: 'Georgia', serif; font-size: 14px; border: none; }
            QLineEdit { background-color: #2d2d2d; color: #e8dcc2; border: 1px solid #8b7355; padding: 5px; font-family: 'Georgia', serif; }
            QPushButton { background-color: rgba(40, 40, 40, 200); color: #e8dcc2; border: 1px solid #8b7355; border-radius: 3px; padding: 5px 15px; }
            QPushButton:hover { background-color: rgba(70, 70, 70, 240); border-color: #ffaa00; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        
        self.label = QLabel(label_text)
        layout.addWidget(self.label)
        
        self.input_field = QLineEdit()
        layout.addWidget(self.input_field)
        
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_ok = QPushButton("OK")
        self.btn_ok.setCursor(Qt.PointingHandCursor)
        self.btn_ok.clicked.connect(self.accept)
        btn_layout.addWidget(self.btn_ok)
        
        layout.addLayout(btn_layout)
        
    def get_text(self):
        return self.input_field.text()

class InteractiveMapViewer(QGraphicsView):
    def __init__(self, image_path, default_min_zoom=0.1, default_layer="surface", lang="ru"):
        super().__init__()
        self.lang = lang
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.profile_name = "default"
        self.setBackgroundBrush(QBrush(QColor("#000000")))
        self.bg_item = self.scene.addPixmap(QPixmap())
        self.bg_item.setZValue(-1)
        self.min_scale = default_min_zoom
        self.current_map_layer = default_layer 
        self.change_map(image_path, self.min_scale, default_layer)
        self.setDragMode(QGraphicsView.NoDrag)
        self.is_panning = False
        self.pan_start = None
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def update_marker_visibility(self, current_state, search_text=""):
        search_text = search_text.lower().strip()
        
        for item in self.scene.items():
            if hasattr(item, "category") and hasattr(item, "map_layer"):
                is_checked = current_state.get(item.category, True)
                is_on_current_map = (item.map_layer == self.current_map_layer)
                name_match = True
                if search_text and hasattr(item, "name_text"):
                    name_match = search_text in item.name_text.lower()
                item.setVisible(is_checked and is_on_current_map and name_match)
            elif isinstance(item, UserWaypoint):
                item.setVisible(item.map_layer == self.current_map_layer)

    def change_map(self, image_path, new_min_zoom=0.1, map_layer="surface"):
        new_bg = QPixmap(image_path)
        if not new_bg.isNull():
            self.bg_item.setPixmap(new_bg)
            self.setSceneRect(self.bg_item.boundingRect())
            self.min_scale = new_min_zoom
            self.current_map_layer = map_layer 
            self.resetTransform()
            self.scale(self.min_scale, self.min_scale)

            for item in self.scene.items():
                if isinstance(item, UserWaypoint):
                    item.setVisible(item.map_layer == self.current_map_layer)
        else:
            print(f"Map data {image_path} not found!")

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor
        current_scale = self.transform().m11()
        max_scale = 1.0  
        
        if event.angleDelta().y() > 0:
            proposed_scale = current_scale * zoom_in_factor
            if proposed_scale > max_scale:
                fix_factor = max_scale / current_scale
                self.scale(fix_factor, fix_factor)
            else:
                self.scale(zoom_in_factor, zoom_in_factor)
        else:
            proposed_scale = current_scale * zoom_out_factor
            if proposed_scale < self.min_scale:
                fix_factor = self.min_scale / current_scale
                self.scale(fix_factor, fix_factor)
            else:
                self.scale(zoom_out_factor, zoom_out_factor)

    def mousePressEvent(self, event):
        super().mousePressEvent(event)

        if event.button() == Qt.RightButton and event.modifiers() == Qt.ControlModifier:
            scene_pos = self.mapToScene(event.pos())
            print(f'"x": {round(scene_pos.x(), 1)}, "y": {round(scene_pos.y(), 1)}')
            return
            
        if event.button() == Qt.RightButton:
            clicked_item = self.itemAt(event.pos())
            if isinstance(clicked_item, UserWaypoint):
                self.remove_waypoint(clicked_item)
                return
            
            scene_pos = self.mapToScene(event.pos())
            x, y = scene_pos.x(), scene_pos.y()
            selector = WaypointSelector(self)
            global_pos = self.viewport().mapToGlobal(event.pos())
            selector.move(global_pos)
            
            if selector.exec_() == QDialog.Accepted and selector.selected_icon:
                icon_path = os.path.join(base_path, "icons", "waypoint_icons", selector.selected_icon)                
                current_layer = self.current_map_layer
                marker_id = f"wp_{int(x)}_{int(y)}"
                label_text = "Marker text (optional):" if self.lang == "en" else "Текст метки (необязательно):"
                input_dialog = WaypointInputDialog(self.window(), label_text)
                global_pos = self.viewport().mapToGlobal(event.pos())
                input_dialog.move(global_pos.x() + 20, global_pos.y())
                
                note = ""
                if input_dialog.exec_() == QDialog.Accepted:
                    note = input_dialog.get_text()
                
                waypoint = UserWaypoint(icon_path, x, y, current_layer, self.remove_waypoint, marker_id, note)
                self.scene.addItem(waypoint)
                self.save_waypoints()
                
        elif event.button() == Qt.LeftButton:
            item = self.itemAt(event.pos())
            if item and item != self.bg_item:
                return 
            self.is_panning = True
            self.pan_start = event.pos()

    def focusOutEvent(self, event):
        self.is_panning = False
        super().focusOutEvent(event)
    

    def remove_waypoint(self, waypoint_item):
        if waypoint_item in self.scene.items():
            self.scene.removeItem(waypoint_item)
            self.save_waypoints()

    def mouseMoveEvent(self, event):
        if self.is_panning and self.pan_start is not None:
            delta = event.pos() - self.pan_start
            self.pan_start = event.pos()
            
            h_bar = self.horizontalScrollBar()
            v_bar = self.verticalScrollBar()
            h_bar.setValue(h_bar.value() - delta.x())
            v_bar.setValue(v_bar.value() - delta.y())
            event.accept()
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_panning = False
            event.accept()
        super().mouseReleaseEvent(event)

    def save_waypoints(self):
        if not self.profile_name:
            return
        waypoints_data = []
        for item in self.scene.items():
            if isinstance(item, UserWaypoint):
                waypoints_data.append({
                    "x": item.pos().x(),
                    "y": item.pos().y(),
                    "layer": item.map_layer,
                    "icon": os.path.basename(item.icon_path),
                    "note": getattr(item, "note", "")
                })

        file_path = os.path.join(base_path, "saves", f"waypoints_{self.profile_name}.json")
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(waypoints_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"Data saving error: {e}")

    def load_waypoints(self):
        for item in list(self.scene.items()):
            if isinstance(item, UserWaypoint):
                self.scene.removeItem(item)
                
        file_path = os.path.join(base_path, "saves", f"waypoints_{self.profile_name}.json")
        if os.path.exists(file_path):
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for wp in data:
                        icon_path = os.path.join(base_path, "icons", "waypoint_icons", wp["icon"])
                        marker_id = f"wp_{int(wp['x'])}_{int(wp['y'])}"
                        note = wp.get("note", "")
                        waypoint = UserWaypoint(icon_path, wp["x"], wp["y"], wp["layer"], self.remove_waypoint, marker_id, note)
                        self.scene.addItem(waypoint)
            except Exception as e:
                print(f"Error loading custom labels: {e}")
        
        for item in self.scene.items():
            if isinstance(item, UserWaypoint):
                item.setVisible(item.map_layer == self.current_map_layer)



