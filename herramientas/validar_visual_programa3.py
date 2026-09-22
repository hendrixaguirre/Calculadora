"""Herramienta QA opcional, solo estándar. Abre escenarios reales de AXION.

No se ejecuta al iniciar la calculadora. Cada ejecución usa historial temporal.
"""
import argparse
import json
import platform
import tempfile
import sys
import time
import tkinter as tk
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from axion_programa3 import AplicacionPrograma3
from axion_storage import AlmacenHistorial


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--escenario', default='producto')
    parser.add_argument('--geometria', default='1280x720')
    parser.add_argument('--cerrar', type=int, default=0)
    args = parser.parse_args()
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError, OSError):
        pass
    with tempfile.TemporaryDirectory() as temp:
        root = tk.Tk()
        app = AplicacionPrograma3(root, AlmacenHistorial(Path(temp)/'historial.json'))
        root.title('AXION · QA · '+args.escenario)
        root.geometry(args.geometria+'+0+0')
        t=app.espacios['matrices'].actual
        t.ejemplo()
        if args.escenario == 'incompatible':
            t.transaccion(lambda:t.b.establecer([[1,2],[3,4]]))
        elif args.escenario in ('combinacion','familia','imposible'):
            app.mostrar_modulo('combinacion')
            t=app.espacios['combinacion'].actual
            t.ejemplo()
            if args.escenario=='familia':
                t.transaccion(lambda:t.cargar({'a':[[1,2],[2,4]], 'b':[[3,6]],'escalar':''}))
            if args.escenario=='imposible':
                t.transaccion(lambda:t.b.establecer([[2,3,6]]))
        elif args.escenario=='vectores':
            app.mostrar_modulo('vectores')
            t=app.espacios['vectores'].actual
            t.ejemplo()
        elif args.escenario in ('ocho','fracciones'):
            a = [[str(int(i==j)) for j in range(8)] for i in range(8)]
            if args.escenario=='fracciones':
                a[0][0]='1234567890123456789/999999999999999999'
            t.transaccion(lambda:t.cargar({'a':a,'b':a,'escalar':''}))
        elif args.escenario=='sistema':
            app.mostrar_modulo('sistemas')
            app.editor.establecer_valores([[1,1,2],[2,2,5]])
            app.resolver()
            app.mostrar_etapa('interpretar')
        inicio=time.perf_counter()
        if args.escenario!='sistema':
            t.calcular()
            if t.resultado and args.escenario not in ('inicial','ocho','fracciones'):
                t.notebook.select(2)
                if args.escenario=='producto':
                    t.celda.current(1)
                    t.detalle_seleccionado()
            if args.escenario in ('ocho','fracciones'):
                t.notebook.select(0)
        root.update()
        duracion=time.perf_counter()-inicio
        def geo(w):
            return {'x':w.winfo_rootx()-root.winfo_rootx(),'y':w.winfo_rooty()-root.winfo_rooty(),
                    'width':w.winfo_width(),'height':w.winfo_height(),'reqheight':w.winfo_reqheight()}
        registro={'scenario':args.escenario,'platform':platform.platform(),'python':platform.python_version(),
                  'tk':root.tk.call('info','patchlevel'),'tk_scaling':root.tk.call('tk','scaling'),
                  'screen':[root.winfo_screenwidth(),root.winfo_screenheight()],
                  'client':[root.winfo_width(),root.winfo_height()], 'calculate_render_s':duracion,
                  'taller':geo(t),'notebook':geo(t.notebook),'definir':geo(t.definir),'editores':geo(t.editores)}
        if platform.system() == 'Windows':
            from ctypes import windll
            registro['windows_window_dpi'] = windll.user32.GetDpiForWindow(root.winfo_id())
        evidencia = ROOT / 'docs' / 'evidencia'
        evidencia.mkdir(parents=True, exist_ok=True)
        (evidencia / f'geo_{args.escenario}_{args.geometria}.json').write_text(json.dumps(registro,indent=2),encoding='utf-8')
        if args.cerrar:
            root.after(args.cerrar*1000,root.destroy)
        root.mainloop()


if __name__=='__main__':
    main()
