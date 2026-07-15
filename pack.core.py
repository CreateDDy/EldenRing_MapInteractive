import zipfile
import os

files_to_pack = ['main.py', 'interface.py', 'components.py', 'config.py']
output_path = os.path.join('core', 'data.dat')

# Создаем папку core, если её вдруг нет
os.makedirs('core', exist_ok=True)

print("Начинаем сборку стерильного ядра для Nexus...")
with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
    for file in files_to_pack:
        if os.path.exists(file):
            # arcname=file гарантирует, что файл ляжет ровно в корень архива
            zipf.write(file, arcname=file) 
            print(f" [+] Упакован: {file}")
        else:
            print(f" [!] ОШИБКА: {file} не найден в папке!")

print(f"\nГотово! Ядро успешно собрано и лежит тут: {output_path}")