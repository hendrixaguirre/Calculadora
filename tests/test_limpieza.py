"""Regresión de arranque, consola e historial tras simplificar el proyecto."""
import contextlib
import io
from pathlib import Path
import runpy
import tempfile
import unittest
from unittest.mock import patch

from axion_cli import leer_dimension
from axion_operaciones import calcular_operacion
from axion_storage import AlmacenHistorial


class PruebasLimpieza(unittest.TestCase):
    def test_historial_valida_sin_recalcular(self):
        with tempfile.TemporaryDirectory() as temp:
            ruta = Path(temp) / 'historial.json'
            almacen = AlmacenHistorial(ruta)
            almacen.add_operacion(calcular_operacion('combinacion', [[1, 2], [2, 4]], [[3, 6]]))
            with patch('axion_operaciones.combinacion_lineal', side_effect=AssertionError('Recalculó al cargar')):
                restaurado = AlmacenHistorial(ruta)
            self.assertEqual(len(restaurado.entradas), 1)
            self.assertFalse(restaurado.ultimo_error)

    def test_lanzador_cli_conserva_el_modo_consola(self):
        ruta = Path(__file__).resolve().parents[1] / 'Programa 3_Grupo 5.py'
        modulo = runpy.run_path(str(ruta))
        salida = io.StringIO()
        with patch('sys.argv', [str(ruta), '--cli']), patch('builtins.input', side_effect=['1', '1', '2', '6', 'j']):
            with contextlib.redirect_stdout(salida):
                codigo = modulo['principal']()
        self.assertEqual(codigo, 0)
        self.assertIn('3', salida.getvalue())
        self.assertIn('Gauss-Jordan', salida.getvalue())

    def test_consola_rechaza_tamanos_fuera_del_limite(self):
        with patch('builtins.input', side_effect=['9', '0', '2']), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(leer_dimension('Dimensión: '), 2)
