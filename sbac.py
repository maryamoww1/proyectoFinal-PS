import argparse
import os
import json
import shutil
import difflib
from datetime import datetime

REPO_DIR = ".sbac"
METADATA_FILE = os.path.join(REPO_DIR, "metadata.json")
SNAPSHOTS_DIR = os.path.join(REPO_DIR, "snapshots")

def load_metadata():
    if not os.path.exists(METADATA_FILE):
        return {"tracked_files": [], "commits": {}, "baselines": {}, "head": None}
    with open(METADATA_FILE, "r") as f:
        return json.load(f)

def save_metadata(metadata):
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=4)

def init_repo():
    if os.path.exists(REPO_DIR):
        print("SBAC: El repositorio ya está inicializado aquí.")
        return
    os.makedirs(REPO_DIR)
    os.makedirs(SNAPSHOTS_DIR)
    save_metadata({"tracked_files": [], "commits": {}, "baselines": {}, "head": None})
    print("SBAC: ¡Repositorio inicializado con éxito en .sbac/!")

def add_file(filename):
    if not os.path.exists(REPO_DIR):
        print("SBAC: Error. No hay un repositorio inicializado. Ejecuta 'sbac start' o 'sbac init'.")
        return
    if not os.path.exists(filename):
        print(f"SBAC: Error. El archivo '{filename}' no existe.")
        return
    
    metadata = load_metadata()
    if filename not in metadata["tracked_files"]:
        metadata["tracked_files"].append(filename)
        save_metadata(metadata)
        print(f"SBAC: Se añadió '{filename}' al seguimiento.")
    else:
        print(f"SBAC: '{filename}' ya está bajo seguimiento.")

def show_status():
    if not os.path.exists(REPO_DIR):
        print("SBAC: Repositorio no inicializado.")
        return
    metadata = load_metadata()
    print("=== Estado del Repositorio ===")
    print(f"Última versión (HEAD): {metadata['head']}")
    print("Archivos bajo seguimiento:")
    for f in metadata["tracked_files"]:
        print(f"  - {f}")

def create_commit(message):
    if not os.path.exists(REPO_DIR):
        print("SBAC: Repositorio no inicializado.")
        return
    metadata = load_metadata()
    if not metadata["tracked_files"]:
        print("SBAC: No hay archivos bajo seguimiento para guardar. Usa 'sbac add'.")
        return

    version_id = f"v{len(metadata['commits']) + 1}"
    version_dir = os.path.join(SNAPSHOTS_DIR, version_id)
    os.makedirs(version_dir, exist_ok=True)

    for filename in metadata["tracked_files"]:
        if os.path.exists(filename):
            os.makedirs(os.path.dirname(os.path.join(version_dir, filename)), exist_ok=True)
            shutil.copy(filename, os.path.join(version_dir, filename))
        else:
            print(f"SBAC: Advertencia, el archivo '{filename}' no se encontró físicamente.")

    metadata["commits"][version_id] = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "message": message,
        "files": metadata["tracked_files"].copy()
    }
    metadata["head"] = version_id
    save_metadata(metadata)
    print(f"SBAC: Versión '{version_id}' guardada exitosamente.")

def show_history():
    if not os.path.exists(REPO_DIR):
        print("SBAC: Repositorio no inicializado.")
        return
    metadata = load_metadata()
    if not metadata["commits"]:
        print("SBAC: No hay historial de versiones aún.")
        return
    print("=== Historial de Versiones ===")
    for vid, info in metadata["commits"].items():
        print(f"[{vid}] - {info['timestamp']} | Mensaje: {info['message']}")

def mark_baseline(name):
    if not os.path.exists(REPO_DIR):
        print("SBAC: Repositorio no inicializado.")
        return
    metadata = load_metadata()
    head = metadata["head"]
    if not head:
        print("SBAC: No hay ninguna versión registrada para marcar como línea base.")
        return
    metadata["baselines"][name] = head
    save_metadata(metadata)
    print(f"SBAC: Línea base '{name}' asignada a la versión {head}.")

def list_baselines():
    if not os.path.exists(REPO_DIR):
        print("SBAC: Repositorio no inicializado.")
        return
    metadata = load_metadata()
    if not metadata["baselines"]:
        print("SBAC: No hay líneas base registradas.")
        return
    print("=== Líneas Base Registradas ===")
    for name, vid in metadata["baselines"].items():
        print(f"  - {name} -> [{vid}]")

def show_diff(v1, v2):
    if not os.path.exists(REPO_DIR):
        print("SBAC: Repositorio no inicializado.")
        return
    metadata = load_metadata()
    
    if v1 in metadata.get("baselines", {}):
        v1 = metadata["baselines"][v1]
    if v2 in metadata.get("baselines", {}):
        v2 = metadata["baselines"][v2]

    if v1 not in metadata["commits"] or v2 not in metadata["commits"]:
        print("SBAC: Una o ambas versiones/líneas base especificadas no existen.")
        return

    print(f"=== Diferencias entre {v1} y {v2} ===")
    files_v1 = metadata["commits"][v1]["files"]
    files_v2 = metadata["commits"][v2]["files"]
    all_files = set(files_v1 + files_v2)

    for filename in all_files:
        path_v1 = os.path.join(SNAPSHOTS_DIR, v1, filename)
        path_v2 = os.path.join(SNAPSHOTS_DIR, v2, filename)

        lines_v1 = []
        if os.path.exists(path_v1):
            with open(path_v1, 'r', encoding='utf-8') as f:
                lines_v1 = f.readlines()

        lines_v2 = []
        if os.path.exists(path_v2):
            with open(path_v2, 'r', encoding='utf-8') as f:
                lines_v2 = f.readlines()

        diff = list(difflib.unified_diff(lines_v1, lines_v2, fromfile=f"{filename} ({v1})", tofile=f"{filename} ({v2})"))
        if diff:
            print(f"\n--- Cambios en: {filename} ---")
            for line in diff:
                print(line, end="")
        else:
            print(f"\n--- {filename}: Sin cambios ---")
    print("\n")
def checkout_version(version):
    if not os.path.exists(REPO_DIR):
        print("SBAC: Repositorio no inicializado.")
        return
    metadata = load_metadata()
    if version not in metadata["commits"]:
        print(f"SBAC: La versión '{version}' no existe en el historial.")
        return
    
    version_dir = os.path.join(SNAPSHOTS_DIR, version)
    for filename in metadata["commits"][version]["files"]:
        src = os.path.join(version_dir, filename)
        if os.path.exists(src):
            shutil.copy(src, filename)
    
    metadata["head"] = version
    save_metadata(metadata)
    print(f"SBAC: Has regresado a la versión '{version}'. Los archivos en tu directorio han sido sobrescritos.")

def main():# pragma: no cover
    parser = argparse.ArgumentParser(description="SBAC: Sistema Básico de Administración de Configuración")
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponibles")

    subparsers.add_parser("init", help="Inicializar el repositorio")
    subparsers.add_parser("start", help="Inicializar el repositorio (Alias)")
    
    parser_add = subparsers.add_parser("add", help="Añadir un archivo al seguimiento")
    parser_add.add_argument("archivo", type=str, help="Ruta del archivo")

    subparsers.add_parser("status", help="Ver el estado actual del repositorio")

    parser_commit = subparsers.add_parser("commit", help="Crear una nueva versión")
    parser_commit.add_argument("mensaje", type=str, help="Mensaje descriptivo")

    subparsers.add_parser("history", help="Ver historial de versiones")

    parser_baseline = subparsers.add_parser("baseline", help="Marcar línea base en la versión actual (HEAD)")
    parser_baseline.add_argument("nombre", type=str, help="Nombre de la línea base")

    subparsers.add_parser("list-baselines", help="Listar líneas base")

    parser_diff = subparsers.add_parser("diff", help="Ver diferencias entre versiones")
    parser_diff.add_argument("v1", type=str, help="Versión 1")
    parser_diff.add_argument("v2", type=str, help="Versión 2")

    parser_checkout = subparsers.add_parser("checkout", help="Regresar a una versión específica")
    parser_checkout.add_argument("version", type=str, help="ID de la versión")

    args = parser.parse_args()

    if args.command in ["init", "start"]:
        init_repo()
    elif args.command == "add":
        add_file(args.archivo)
    elif args.command == "status":
        show_status()
    elif args.command == "commit":
        create_commit(args.mensaje)
    elif args.command == "history":
        show_history()
    elif args.command == "baseline":
        mark_baseline(args.nombre)
    elif args.command == "list-baselines":
        list_baselines()
    elif args.command == "diff":
        show_diff(args.v1, args.v2)
    elif args.command == "checkout":
        checkout_version(args.version)
    else:
        parser.print_help()

if __name__ == "__main__":# pragma: no cover
    main()