import zipfile
import os

files_to_pack = ['main.py', 'interface.py', 'components.py', 'config.py']
output_path = os.path.join('core', 'data.dat')

os.makedirs('core', exist_ok=True)

print("Собираем ядро...")
with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in files_to_pack:
        if os.path.exists(file):
            zipf.write(file)
            print(f" [+] Добавлен {file}")
        else:
            print(f" [!] ОШИБКА: {file} не найден!")

print(f"Готово! Ядро обновлено: {output_path}")