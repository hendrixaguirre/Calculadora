"""Medición local reproducible, no forma parte del arranque de AXION."""
import json
import platform
import sys
import tempfile
import time
import tkinter as tk
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from axion_operaciones import calcular_operacion
from axion_programa3 import AplicacionPrograma3
from axion_storage import AlmacenHistorial

a=[[1,2,3],[4,5,6]]
b=[[7,8],[9,10],[11,12]]
inicio=time.perf_counter()
for _ in range(1000):
    resultado=calcular_operacion('matriz_producto',a,b)
motor=(time.perf_counter()-inicio)/1000
with tempfile.TemporaryDirectory() as temp:
    r=tk.Tk()
    app=AplicacionPrograma3(r,AlmacenHistorial(Path(temp)/'historial.json'))
    t=app.espacios['matrices'].actual
    t.resultado=resultado
    r.update()
    inicio=time.perf_counter()
    for _ in range(10):
        t.renderizar()
        r.update_idletasks()
    render=(time.perf_counter()-inicio)/10
    datos={'plataforma':platform.platform(),'python':platform.python_version(),
           'tk':r.tk.call('info','patchlevel'),'caso':'A 2x3 por B 3x2',
           'motor_repeticiones':1000,'motor_ms':motor*1000,
           'render_repeticiones':10,'render_ms':render*1000,
           'nota':'Render de vistas sobre widgets existentes; excluye iniciar app y guardar historial.'}
    r.destroy()
destino = Path(__file__).resolve().parents[1] / 'docs' / 'evidencia' / 'rendimiento.json'
destino.parent.mkdir(parents=True, exist_ok=True)
destino.write_text(json.dumps(datos,indent=2),encoding='utf-8')
