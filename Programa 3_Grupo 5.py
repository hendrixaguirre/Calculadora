"""AXION · UAM/FIA · Álgebra Lineal MTM0120 · Programa 3, Grupo 5.

Mantén los módulos axion_*.py junto a este archivo. Solo Python estándar.
"""
import sys


def principal():
    if '--cli' in sys.argv:
        from axion_cli import resolver_interactivamente
        try:
            resolver_interactivamente()
        except (EOFError, KeyboardInterrupt):
            print('\nEntrada cancelada.', file=sys.stderr)
            return 1
        return 0
    try:
        import tkinter as tk
    except ImportError as error:
        print(f'AXION necesita Python con Tcl/Tk: {error}', file=sys.stderr)
        return 1
    try:
        from axion_programa3 import lanzar_aplicacion
        lanzar_aplicacion()
    except (ImportError, tk.TclError) as error:
        print('AXION necesita Python con Tcl/Tk y una sesión gráfica disponible. '
              f'Revisa la instalación de Python. Detalle: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(principal())
