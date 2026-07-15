import os
import sys

if getattr(sys, 'frozen', False):
    base_path = os.path.dirname(sys.executable)
else:
    base_path = os.path.dirname(os.path.abspath(sys.argv[0]))

GAME_TITLE = "ELDEN RING MAP"

APP_VERSION = "1.2.5"

#Структура меню (Сайдбар)
# Ключи категорий и элементов должны строго совпадать с LOCALES и REGISTRY
CATEGORIES_BASE = {
    "cat_locations": {
        "grace": "Благодати",
        "dungeon": "Подземелья",
        "hub_with_grace": "Крепость Круглого стола"
    },
    "cat_merchants": {
        "nomadic_merchant": "Торговцы"
    },
    "cat_enemies": {
        "bird": "Птицы",
        "cavalry": "Всадники",
        "hunter": "Охотники"
    },
    "cat_upgrades": {
        "golden_seed": "Золотое семечко",
        "sacred_tear": "Священная слеза"
    }
}

CATEGORIES_DLC = {
    "cat_locations": {
        "grace_dlc": "Благодати",
        "dungeon_dlc": "Подземелья"
        
    },
    "cat_upgrades_dlc": {
        "scadutree_dlc": "Осколки Древа Упадка",
        "rspirit_ash_dlc": "Прах славного духа"
    }
}

#Манифест файлов (Базовые имена без расширений и языковых суффиксов)
DATA_MANIFEST = {
    "boss_data": "night_boss",
    "grace_data": "graces",
    "merchant_data": "merchant",
    "dungeon_data": "dungeons",
    "seeds_data": "golden_seeds",
    "tears_data": "sacred_tears",
    "scadutree_data": "scadutree",
    "rspirit_ash_data": "rspirit_ash"
}

#Слои карты (Файлы подложек и стартовый масштаб с правильными путями)
MAP_LAYERS = {
    "surface":     {"file": os.path.join(base_path, "maps", "map_surface.jpg"),     "zoom": 0.2},
    "underground": {"file": os.path.join(base_path, "maps", "map_underground.jpg"), "zoom": 0.2},
    "dlc":         {"file": os.path.join(base_path, "maps", "map_dlc.jpg"),         "zoom": 0.35}
}

REGISTRY = {
    # --- БАЗОВАЯ ИГРА ---
    "bird": {
        "label_ru": "Ночная птица",
        "label_en": "Death Bird",
        "icon": "death_bird.png",
        "source": "boss_data",
        "json_keys": ["death_birds", "death_rite_birds"]
    },
    "cavalry": {
        "label_ru": "Ночной всадник",
        "label_en": "Night's Cavalry",
        "icon": "night_cavalry.png",
        "source": "boss_data",
        "json_keys": ["night_cavalry"]
    },
    "hunter": {
        "label_ru": "Охотник за сферами",
        "label_en": "Bell Bearing Hunter",
        "icon": "BB_hunter.png",
        "source": "boss_data",
        "json_keys": ["BB_hunter"]
    },
    "grace": {
        "label": "Благодати",
        "icon": "grace.png",
        "source": "grace_data",
        "json_keys": ["surface", "underground"], 
        "is_regional": True,
        "marker_type": "grace" 
    },
    "hub_with_grace": {
        "label": "Крепость Круглого стола",
        "icon": "hub.png",        
        "overlay": "grace.png",   
        "source": "grace_data",    
        "json_keys": ["Hub"],
        "is_regional": False 
    },
    "nomadic_merchant": {
        "label": "Торговец-кочевник",
        "icon": "merchant.png",
        "source": "merchant_data",
        "json_keys": None,
        "is_regional": True,
        "icon_size": 32
    },
    "dungeon": {
        "label": "Подземелье",
        "icon": "grace_base.png",  
        "source": "dungeon_data",  
        "json_keys": ["surface", "underground"],         
        "is_regional": True        
    },
    "golden_seed": {
        "label": "Золотое семечко",
        "icon": "golden_seed.png",
        "source": "seeds_data",
        "json_keys": None,
        "is_regional": True
    },
    "sacred_tear": {
        "label": "Священная слеза",
        "icon": "sacred_tear.png",
        "source": "tears_data",
        "json_keys": None,
        "is_regional": True,
        "icon_size": 60
    },
    
    # --- DLC РЕГИОН ---
    "grace_dlc": {
        "label": "Благодати",
        "icon": "grace.png",
        "source": "grace_data",
        "json_keys": ["dlc"], 
        "is_regional": True,
        "marker_type": "grace"
    },
    "dungeon_dlc": {
        "label": "Подземелье",
        "icon": "grace_base.png",
        "source": "dungeon_data",
        "json_keys": ["dlc"], 
        "is_regional": True
    },
    "scadutree_dlc": {
        "label": "Осколок Древа Упадка",
        "icon": "scadutree.png",
        "source": "scadutree_data",
        "json_keys": ["dlc"],
        "is_regional": True,
        "icon_size": 64
        
    },
    "rspirit_ash_dlc": {
        "label": "Прах славного духа",
        "icon": "rspirit_ash.png",
        "source": "rspirit_ash_data",
        "json_keys": ["dlc"],
        "is_regional": True,
        "icon_size": 64
    }
    
    
}

#Локализация статичного интерфейса и динамических чекбоксов
LOCALES = {
    "ru": {
        "btn_show_all": "Показать всё",
        "btn_hide_all": "Скрыть всё",
        "btn_back": "В Главное меню",
        "search_placeholder": "Поиск...",
        "btn_surface": "Междуземье",
        "btn_underground": "Подземная карта",
        "btn_dlc": "Realm of Shadow",
        
        "cat_locations": "ЛОКАЦИИ",
        "cat_merchants": "ТОРГОВЦЫ",
        "cat_enemies": "НОЧНЫЕ БОССЫ",
        "cat_upgrades": "Улучшение фляг",
        "cat_upgrades_dlc": "Улучшения",
        
        "lbl_grace": "Благодати",
        "lbl_dungeon": "Подземелья",
        "lbl_nomadic_merchant": "Торговцы-кочевники",
        "lbl_bird": "Ночные птицы",
        "lbl_cavalry": "Ночные всадники",
        "lbl_hunter": "Охотники за сферами",
        "lbl_hub_with_grace": "Крепость Круглого стола",
        "lbl_golden_seed": "Золотое семечко",
        "lbl_sacred_tear": "Священная слеза",
        
        "lbl_grace_dlc": "Благодати",
        "lbl_dungeon_dlc": "Подземелья",
        "lbl_scadutree_dlc": "Осколок Древа Упадка",
        "lbl_rspirit_ash_dlc": "Прах славного духа"
    },
    "en": {
        "btn_show_all": "Show all",
        "btn_hide_all": "Hide all",
        "btn_back": "Main Menu",
        "search_placeholder": "Search ...",
        "btn_surface": "The Lands Between",
        "btn_underground": "Underground",
        "btn_dlc": "Realm of Shadow",
        
        "cat_locations": "LOCATIONS",
        "cat_merchants": "MERCHANTS",
        "cat_enemies": "NIGHT BOSSES",
        "cat_upgrades": "Flask upgrade",
        "cat_upgrades_dlc": "Upgrades",
        
        "lbl_grace": "Graces",
        "lbl_dungeon": "Dungeons",
        "lbl_nomadic_merchant": "Nomadic Merchants",
        "lbl_bird": "Death Birds",
        "lbl_cavalry": "Night's Cavalry",
        "lbl_hunter": "Bell Bearing Hunters",
        "lbl_hub_with_grace": "Roundtable Hold",
        "lbl_golden_seed": "Golden Seed",
        "lbl_sacred_tear": "Sacred Tear",
        
        "lbl_grace_dlc": "Graces",
        "lbl_dungeon_dlc": "Dungeons",
        "lbl_scadutree_dlc": "Scadutree Fragment",
        "lbl_rspirit_ash_dlc": "Revered Spirit Ash"
    }
}