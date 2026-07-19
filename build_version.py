import os
import json
import re

def get_files_recursive(folder, extension):
    file_list = []
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.endswith(extension):
                rel_path = os.path.relpath(os.path.join(root, file))
                file_list.append(rel_path.replace("\\", "/"))
    return file_list

files = get_files_recursive("DATA", ".json")
files += get_files_recursive("icons", ".png")
try:
    with open("version.json", "r", encoding="utf-8") as f:
        current_version = json.load(f).get("db_version", "1.0.0")
except FileNotFoundError:
    current_version = "1.0.0"

v_parts = list(map(int, str(current_version).split('.')))
v_parts[2] += 1
new_version = f"{v_parts[0]}.{v_parts[1]}.{v_parts[2]}"

with open("version.json", "w", encoding="utf-8") as f:
    json.dump({"db_version": new_version, "files": files}, f, indent=4, ensure_ascii=False)

config_path = "config.py"
if os.path.exists(config_path):
    with open(config_path, "r", encoding="utf-8") as f:
        config_content = f.read()

    config_content = re.sub(r'APP_VERSION\s*=\s*".*"', f'APP_VERSION = "{new_version}"', config_content)

    with open(config_path, "w", encoding="utf-8") as f:
        f.write(config_content)
    print(f"Конфиг обновлен. Текущая версия приложения: {new_version}")
else:
    print("Файл config.py не найден, обновление версии в коде пропущено.")

print(f"Манифест собран. Файлов в базе: {len(files)}")