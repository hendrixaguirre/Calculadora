"""Persistencia local y exportación autocontenida de AXION Programa 2.

El historial usa JSON validado y escritura atómica. Nunca ejecuta el contenido
guardado. Los racionales se conservan como texto numerador/denominador.
"""

from __future__ import annotations

import html
import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from axion_core import ResultadoCalculo, construir_reporte, numero_compacto, a_fraccion

VERSION_ESQUEMA = 1
VERSION_MOTOR = "2.0"
MAX_HISTORIAL = 50
MAX_BYTES_HISTORIAL = 2_000_000


def ruta_historial_predeterminada() -> Path:
    base = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    return base / "AXION" / "historial.json"


def _datos_matriz(matriz):
    return [[str(valor) for valor in fila] for fila in matriz]


class AlmacenHistorial:
    """Mantiene hasta ``limite`` ejercicios sin modificar registros anteriores."""

    def __init__(self, ruta: str | Path | None = None, limite: int = MAX_HISTORIAL):
        self.ruta = Path(ruta) if ruta is not None else ruta_historial_predeterminada()
        self.limite = max(1, int(limite))
        self.entradas: list[dict] = []
        self.ultimo_error = ""
        self.load()

    def load(self) -> list[dict]:
        self.ultimo_error = ""
        if not self.ruta.exists():
            self.entradas = []
            return self.entradas
        entradas_anteriores = self.entradas[:]
        try:
            if self.ruta.stat().st_size > MAX_BYTES_HISTORIAL:
                raise ValueError("el archivo excede el límite de 2 MB")
            datos = json.loads(self.ruta.read_text(encoding="utf-8"))
            if not isinstance(datos, dict) or datos.get("schema_version") != VERSION_ESQUEMA:
                raise ValueError("versión de esquema no compatible")
            registros = datos.get("entries")
            if not isinstance(registros, list):
                raise ValueError("la lista de ejercicios no es válida")
            validados = []
            for registro in registros[: self.limite]:
                if isinstance(registro, dict) and registro.get('kind') == 'operacion':
                    from axion_operaciones import validar_operacion
                    if registro.get('schema_version') != 1 or not isinstance(registro.get('created_at'), str):
                        raise ValueError('registro de operación no válido')
                    validar_operacion(registro.get('operation'), registro.get('a'), registro.get('b'), registro.get('scalar'))
                    validados.append(registro)
                    continue
                matriz = registro.get("matrix") if isinstance(registro, dict) else None
                if not matriz or not isinstance(matriz, list) or not all(isinstance(fila, list) for fila in matriz):
                    raise ValueError("un registro no contiene una matriz válida")
                ancho = len(matriz[0])
                if ancho < 2 or any(len(fila) != ancho for fila in matriz):
                    raise ValueError("un registro contiene filas incompatibles")
                filas, variables = len(matriz), ancho - 1
                if not (1 <= filas <= 8 and 1 <= variables <= 8):
                    raise ValueError("un registro excede las dimensiones admitidas")
                if registro.get("rows") != filas or registro.get("variables") != variables:
                    raise ValueError("las dimensiones declaradas no coinciden con la matriz")
                if registro.get("classification") not in {"unica", "infinitas", "inconsistente"}:
                    raise ValueError("un registro contiene una clasificación no válida")
                if registro.get("method") not in {"gauss", "gauss-jordan"}:
                    raise ValueError("un registro contiene un método no válido")
                if not isinstance(registro.get("engine_version"), str):
                    raise ValueError("un registro no identifica la versión del motor")
                if not isinstance(registro.get("created_at"), str) or not isinstance(registro.get("id"), str):
                    raise ValueError("un registro no contiene identidad y fecha válidas")
                for fila in matriz:
                    for valor in fila:
                        a_fraccion(str(valor))
                validados.append(registro)
            self.entradas = validados
        except (OSError, ValueError, TypeError, json.JSONDecodeError, ZeroDivisionError) as error:
            self.entradas = entradas_anteriores
            self.ultimo_error = f"No se pudo cargar el historial: {error}"
        return self.entradas

    def add(self, resultado: ResultadoCalculo) -> bool:
        registro = {
            "id": datetime.now().strftime("%Y%m%dT%H%M%S%f"),
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "rows": len(resultado.original),
            "variables": resultado.variables,
            "matrix": _datos_matriz(resultado.original),
            "classification": resultado.clasificacion,
            "method": resultado.metodo_usado,
            "engine_version": VERSION_MOTOR,
        }
        self.entradas.insert(0, registro)
        self.entradas = self.entradas[: self.limite]
        return self.save()

    def save(self) -> bool:
        datos = {"schema_version": VERSION_ESQUEMA, "entries": self.entradas}
        temporal = None
        try:
            self.ruta.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                "w", encoding="utf-8", delete=False, dir=self.ruta.parent,
                prefix="historial_", suffix=".tmp",
            ) as archivo:
                json.dump(datos, archivo, ensure_ascii=False, indent=2)
                archivo.flush()
                os.fsync(archivo.fileno())
                temporal = Path(archivo.name)
            os.replace(temporal, self.ruta)
            self.ultimo_error = ""
            return True
        except OSError as error:
            self.ultimo_error = f"No se pudo guardar el historial: {error}"
            if temporal is not None:
                try:
                    temporal.unlink(missing_ok=True)
                except OSError:
                    pass
            return False

    def add_operacion(self, resultado) -> bool:
        """Guarda operandos racionales exactos y operación; reabrir crea una copia."""
        registro = {
            'kind': 'operacion', 'schema_version': 1, 'engine_version': '3.0',
            'id': datetime.now().strftime('%Y%m%dT%H%M%S%f'),
            'created_at': datetime.now().astimezone().isoformat(timespec='seconds'),
            'operation': resultado.operacion, 'a': _datos_matriz(resultado.a),
            'b': _datos_matriz(resultado.b) if resultado.b is not None else None,
            'scalar': str(resultado.escalar) if resultado.escalar is not None else None,
        }
        self.entradas.insert(0, registro)
        self.entradas = self.entradas[:self.limite]
        return self.save()


def _tabla(matriz, modo, precision, titulo):
    filas = []
    variables = len(matriz[0]) - 1
    for fila in matriz:
        celdas = []
        for indice, valor in enumerate(fila):
            css = ' class="b"' if indice == variables else ""
            celdas.append(f"<td{css}>{html.escape(numero_compacto(valor, modo, precision))}</td>")
        filas.append("<tr>" + "".join(celdas) + "</tr>")
    return f"<figure><figcaption>{html.escape(titulo)}</figcaption><table>{''.join(filas)}</table></figure>"


def construir_reporte_html(resultado: ResultadoCalculo, modo="fracciones", precision=4) -> str:
    """Genera un informe HTML imprimible, sin scripts ni recursos de red."""
    etiqueta_metodo = "Gauss-Jordan" if resultado.metodo_usado == "gauss-jordan" else "Eliminación de Gauss"
    encabezado_procedimiento = (
        "Procedimiento de Gauss-Jordan"
        if resultado.metodo_usado == "gauss-jordan"
        else "Procedimiento de eliminación de Gauss"
    )
    encabezado_final = "RREF e interpretación" if resultado.metodo_usado == "gauss-jordan" else "Forma escalonada e interpretación"
    titulo_final = "Forma escalonada reducida por filas" if resultado.metodo_usado == "gauss-jordan" else "Forma escalonada final"
    representacion = (
        "fracciones exactas"
        if modo == "fracciones"
        else f"decimales aproximados (≈), {precision} cifras; cálculo interno exacto"
    )
    pasos = []
    for paso in resultado.pasos:
        pasos.append(
            f"<section class='step'><h3>Paso {paso.indice:02d}: {html.escape(paso.titulo)}</h3>"
            f"<p class='operation'>{html.escape(paso.notacion_operacion)}</p>"
            f"<p>{html.escape(paso.explicacion_breve)}</p>"
            f"{_tabla(paso.matriz_despues, modo, precision, 'Matriz después del paso')}</section>"
        )
    pivotes_a = ", ".join(str(columna + 1) for columna in resultado.columnas_pivote) or "ninguno"
    pivotes_aumentada = ", ".join(
        "b" if columna == resultado.variables else str(columna + 1)
        for columna in resultado.columnas_pivote_aumentada
    ) or "ninguno"
    texto_plano = html.escape(construir_reporte(resultado, modo, precision))
    return f"""<!doctype html>
<html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Reporte AXION — Programa 2</title>
<style>
:root{{--ink:#172033;--blue:#1D4ED8;--copper:#9A3412;--paper:#fff;--canvas:#F6F5F0;}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--canvas);color:var(--ink);font:16px/1.5 Arial,sans-serif}}
main{{max-width:980px;margin:32px auto;background:var(--paper);padding:48px}} h1{{font-size:34px;margin:0;color:var(--blue)}}
h2{{margin-top:34px;border-bottom:2px solid #d9dee8;padding-bottom:8px}} h3{{color:var(--copper)}}
table{{border-collapse:collapse;margin:12px 0}} td{{border:1px solid #c9d0db;padding:8px 14px;text-align:center;font-family:Consolas,monospace}}
td.b{{border-left:3px solid var(--blue)}} figcaption{{font-weight:bold}} .meta{{background:#eef3ff;padding:16px}}
.operation{{font:700 16px Consolas,monospace;color:var(--blue)}} pre{{white-space:pre-wrap;background:#f8f9fb;padding:20px}}
@media print{{body{{background:white}}main{{margin:0;max-width:none;padding:20mm}}.step{{break-inside:avoid}}}}
</style></head><body><main>
<h1>AXION — Programa 2</h1><p>Álgebra lineal, paso a paso</p>
<section class="meta"><strong>Clasificación:</strong> {html.escape(resultado.clasificacion)}<br>
  <strong>Método:</strong> {html.escape(etiqueta_metodo)} · <strong>Aritmética:</strong> racional exacta<br>
  <strong>Representación:</strong> {html.escape(representacion)}<br>
<strong>rango(A):</strong> {resultado.rango_a} · <strong>rango([A|b]):</strong> {resultado.rango_aumentada}<br>
<strong>Pivotes de A:</strong> {pivotes_a} · <strong>Pivotes de [A|b]:</strong> {pivotes_aumentada}</section>
<h2>Entrada original</h2>{_tabla(resultado.original, modo, precision, '[A|b]')}
  <h2>{html.escape(encabezado_procedimiento)}</h2>{''.join(pasos)}
  <h2>{html.escape(encabezado_final)}</h2>{_tabla(resultado.matriz_final, modo, precision, titulo_final)}
<h2>Reporte textual completo</h2><pre>{texto_plano}</pre>
</main></body></html>"""
