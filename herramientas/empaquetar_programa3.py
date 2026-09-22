"""Construye una entrega mínima y la reemplaza solo después de comprobarla."""
import ast
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANZADOR = 'Programa 3_Grupo 5.py'
ZIP = ROOT / 'entrega' / 'Programa 3_Grupo 5_Velasquez_Aguirre.zip'
EVIDENCIA = ROOT / 'docs' / 'evidencia'


def archivos_entrega():
    return [
        *sorted(ROOT.glob('axion_*.py')),
        ROOT / LANZADOR,
        *sorted((ROOT / 'tests').glob('*.py')),
        ROOT / 'README.md',
        ROOT / 'entrega' / 'Informe_Programa 3_Grupo 5.pdf',
    ]


def comprobar_dependencias(archivos):
    locales = {archivo.stem for archivo in archivos if archivo.suffix == '.py'}
    for archivo in archivos:
        if not archivo.is_file():
            raise FileNotFoundError(archivo)
        if archivo.suffix != '.py':
            continue
        arbol = ast.parse(archivo.read_text(encoding='utf-8-sig'))
        for nodo in ast.walk(arbol):
            modulos = []
            if isinstance(nodo, ast.Import):
                modulos = [nombre.name for nombre in nodo.names]
            elif isinstance(nodo, ast.ImportFrom) and nodo.module:
                modulos = [nodo.module]
            for modulo in modulos:
                base = modulo.split('.')[0]
                if base not in sys.stdlib_module_names and base not in locales:
                    raise RuntimeError(f'Dependencia no incluida: {archivo.name}: {base}')


def main():
    archivos = archivos_entrega()
    comprobar_dependencias(archivos)
    EVIDENCIA.mkdir(parents=True, exist_ok=True)
    ZIP.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='AXION revisión con espacios ') as temporal:
        candidato = Path(temporal) / ZIP.name
        destino = Path(temporal) / 'extracción'
        with zipfile.ZipFile(candidato, 'w', zipfile.ZIP_DEFLATED) as paquete:
            for archivo in archivos:
                relativo = archivo.name if archivo.suffix == '.pdf' else archivo.relative_to(ROOT).as_posix()
                paquete.write(archivo, relativo)
        with zipfile.ZipFile(candidato) as paquete:
            if paquete.testzip() is not None:
                raise RuntimeError('El ZIP contiene un archivo dañado.')
            paquete.extractall(destino)
        pruebas = subprocess.run(
            [sys.executable, '-B', '-m', 'unittest', '-v'], cwd=destino,
            text=True, encoding='utf-8', errors='replace', capture_output=True, timeout=240,
        )
        registro = pruebas.stdout + pruebas.stderr
        (EVIDENCIA / 'pruebas_zip.log').write_text(registro, encoding='utf-8')
        cantidad = re.search(r'Ran (\d+) tests?', registro)
        if pruebas.returncode or not cantidad or int(cantidad.group(1)) == 0:
            raise RuntimeError('No se actualizó el ZIP: revisa docs/evidencia/pruebas_zip.log.')
        # Ejecutar el lanzador real y cerrar la ventana después de entrar al mainloop.
        humo = '''import tkinter as tk, runpy
original = tk.Tk.mainloop
def breve(self, *args, **kwargs):
    self.after(400, self.destroy)
    return original(self, *args, **kwargs)
tk.Tk.mainloop = breve
runpy.run_path('Programa 3_Grupo 5.py', run_name='__main__')
'''
        inicio = subprocess.run(
            [sys.executable, '-B', '-c', humo], cwd=destino, capture_output=True,
            text=True, encoding='utf-8', errors='replace', timeout=30,
        )
        if inicio.returncode:
            raise RuntimeError(f'No se actualizó el ZIP: falló el lanzador.\n{inicio.stderr}')
        contenido = candidato.read_bytes()
        reemplazo = ZIP.with_suffix('.zip.tmp')
        reemplazo.write_bytes(contenido)
        reemplazo.replace(ZIP)
        comprobacion = {
            'zip': ZIP.name,
            'archivos': len(archivos),
            'pruebas': int(cantidad.group(1)),
            'pruebas_exit': pruebas.returncode,
            'lanzador_exit': inicio.returncode,
            'dependencias': 'solo biblioteca estándar',
            'ruta_prueba': str(destino),
            'sha256': hashlib.sha256(contenido).hexdigest(),
        }
    (EVIDENCIA / 'verificacion_zip.json').write_text(
        json.dumps(comprobacion, indent=2, ensure_ascii=False), encoding='utf-8',
    )
    print(json.dumps(comprobacion, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
