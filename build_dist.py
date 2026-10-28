import os
import sys

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import shutil
import subprocess

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(ROOT_DIR, "src")
BIN_DIR = os.path.join(ROOT_DIR, "bin")
BUILD_DIR = os.path.join(ROOT_DIR, "build")

def ensure_dependencies():
    print("[*] Comprobando dependencias de compilación...")
    try:
        import PyInstaller
    except ImportError:
        print("[*] Instalando PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def compile_binary(source_file: str, exe_name: str):
    print(f"\n==================================================")
    print(f"[*] Compilando {exe_name}.exe desde {source_file}...")
    print(f"==================================================")
    templates_dir = os.path.join(SRC_DIR, "templates")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--noconfirm",
        "--clean",
        "--onefile",
        "--windowed",
        "--name", exe_name,
        "--distpath", BIN_DIR,
        "--workpath", os.path.join(BUILD_DIR, exe_name),
        "--specpath", BUILD_DIR,
        "--paths", SRC_DIR,
        "--add-data", f"{templates_dir};templates",
        source_file
    ]
    subprocess.check_call(cmd)
    target_exe = os.path.join(BIN_DIR, f"{exe_name}.exe")
    if os.path.exists(target_exe):
        size_mb = os.path.getsize(target_exe) / (1024 * 1024)
        print(f"[OK] {exe_name}.exe generado con éxito ({size_mb:.2f} MB).")
    else:
        raise RuntimeError(f"No se encontró el ejecutable esperado en {target_exe}")

def copy_assets():
    print("\n[*] Copiando archivos de configuración inicial...")
    cfg_src = os.path.join(SRC_DIR, "config.json")
    cfg_dst = os.path.join(BIN_DIR, "config.json")
    if os.path.exists(cfg_src):
        shutil.copy2(cfg_src, cfg_dst)
        print(f"[OK] config.json copiado a {BIN_DIR}")

def main():
    os.makedirs(BIN_DIR, exist_ok=True)
    os.makedirs(BUILD_DIR, exist_ok=True)
    ensure_dependencies()

    reader_py = os.path.join(SRC_DIR, "voice_reader.py")
    widget_py = os.path.join(SRC_DIR, "floating_control.py")

    compile_binary(reader_py, "AntigravityVoiceService")
    compile_binary(widget_py, "AntigravityVoiceWidget")
    copy_assets()

    print("\n==================================================")
    print("[OK] COMPILACION STANDALONE COMPLETADA CON EXITO!")
    print(f"Los ejecutables listos para distribuir estan en:\n  {BIN_DIR}")
    print("==================================================")

if __name__ == "__main__":
    main()
