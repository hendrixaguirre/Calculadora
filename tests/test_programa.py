import unittest
from fractions import Fraction
import json
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import tkinter as tk

from axion_core import (
    construir_reporte,
    texto_ecuacion,
    matriz_exacta,
    formatear_numero,
    texto_matriz,
    lineas_parametricas,
    es_rref,
    resolver_sistema,
    a_fraccion,
    texto_forma_vectorial,
)
from axion_ui import AplicacionAxion
from axion_storage import AlmacenHistorial, construir_reporte_html


class PruebasMotorExacto(unittest.TestCase):
    def test_solucion_unica_2x2(self):
        resultado = resolver_sistema([[2, 1, 5], [1, -1, 1]], "gauss")
        self.assertEqual(resultado.clasificacion, "unica")
        self.assertEqual(resultado.solucion_unica, [Fraction(2), Fraction(1)])
        self.assertTrue(all(linea.valida for linea in resultado.verificacion))

    def test_solucion_unica_3x3(self):
        matriz = [[1, 1, 1, 6], [2, -1, 1, 3], [1, 2, -1, 2]]
        resultado = resolver_sistema(matriz, "gauss-jordan")
        self.assertEqual(resultado.clasificacion, "unica")
        for row in resultado.rref[:3]:
            self.assertEqual(sum(value != 0 for value in row[:-1]), 1)

    def test_infinitas_soluciones(self):
        resultado = resolver_sistema([[1, 1, 1, 2], [2, 2, 2, 4]])
        self.assertEqual(resultado.clasificacion, "infinitas")
        self.assertEqual(resultado.variables_libres, [1, 2])
        self.assertEqual(len(resultado.vectores_direccion), 2)
        self.assertTrue(resultado.verificacion_particular)
        self.assertTrue(resultado.verificacion_direcciones)

    def test_sistema_sin_solucion(self):
        resultado = resolver_sistema([[1, 1, 2], [1, 1, 5]])
        self.assertEqual(resultado.clasificacion, "inconsistente")
        self.assertEqual(resultado.fila_contradiccion[-1], 1)
        self.assertLess(resultado.rango_a, resultado.rango_aumentada)

    def test_mas_ecuaciones_que_variables(self):
        resultado = resolver_sistema([[1, 1, 2], [2, -1, 1], [3, 0, 3]])
        self.assertEqual(resultado.solucion_unica, [Fraction(1), Fraction(1)])

    def test_mas_variables_que_ecuaciones(self):
        resultado = resolver_sistema([[1, 0, 2, 3], [0, 1, -1, 0]])
        self.assertEqual(resultado.clasificacion, "infinitas")
        self.assertEqual(resultado.variables_libres, [2])

    def test_fila_de_ceros(self):
        resultado = resolver_sistema([[1, 2, 3], [0, 0, 0]])
        self.assertEqual((resultado.rango_a, resultado.rango_aumentada), (1, 1))

    def test_ecuaciones_repetidas(self):
        resultado = resolver_sistema([[1, 1, 2], [1, 1, 2]])
        self.assertEqual(resultado.clasificacion, "infinitas")

    def test_pivote_inicial_cero_intercambia_filas(self):
        resultado = resolver_sistema([[0, 1, 2], [1, 1, 3]])
        self.assertEqual(resultado.pasos[0].tipo_operacion, "initial")
        self.assertEqual(resultado.pasos[1].tipo_operacion, "swap")
        self.assertEqual(resultado.solucion_unica, [Fraction(1), Fraction(2)])

    def test_coeficientes_negativos(self):
        resultado = resolver_sistema([[-1, 2, 1], [3, -1, 7]])
        self.assertTrue(all(linea.valida for linea in resultado.verificacion))

    def test_fracciones_se_conservan_exactas(self):
        resultado = resolver_sistema([["1/2", 1, 2], [1, "-1/3", 1]])
        self.assertTrue(all(isinstance(value, Fraction) for row in resultado.rref for value in row))
        self.assertEqual(resultado.solucion_unica, [Fraction(10, 7), Fraction(9, 7)])

    def test_decimales_se_convierten_exactamente(self):
        self.assertEqual(a_fraccion("0.125"), Fraction(1, 8))
        self.assertEqual(a_fraccion(0.1), Fraction(1, 10))

    def test_todos_los_coeficientes_cero(self):
        resultado = resolver_sistema([[0, 0, 0], [0, 0, 0]])
        self.assertEqual(resultado.clasificacion, "infinitas")
        self.assertEqual(resultado.rango_a, 0)

    def test_sistema_homogeneo(self):
        resultado = resolver_sistema([[1, 2, 0], [2, 4, 0]])
        self.assertEqual(resultado.clasificacion, "infinitas")
        self.assertEqual(resultado.solucion_particular, [0, 0])

    def test_valores_muy_grandes(self):
        resultado = resolver_sistema([[10**12, 1, 10**12 + 1], [1, -1, 0]])
        self.assertEqual(resultado.solucion_unica, [1, 1])

    def test_gauss_y_gauss_jordan_son_metodos_reales(self):
        gauss = resolver_sistema([[2, 1, 5], [1, -1, 1]], "gauss")
        jordan = resolver_sistema([[2, 1, 5], [1, -1, 1]], "gauss-jordan")
        self.assertEqual(gauss.metodo_usado, "gauss")
        self.assertEqual(jordan.metodo_usado, "gauss-jordan")
        self.assertNotEqual(gauss.matriz_final, jordan.matriz_final)

    def test_automatico_informa_metodo_utilizado(self):
        resultado = resolver_sistema([[1, 0, 1], [0, 1, 2]], "automatico")
        self.assertEqual(resultado.metodo_usado, "gauss-jordan")

    def test_pasos_son_estructurados(self):
        resultado = resolver_sistema([[2, 1, 5], [1, -1, 1]])
        paso = resultado.pasos[0]
        for attribute in (
            "titulo", "objetivo", "tipo_operacion", "notacion_operacion", "matriz_antes",
            "matriz_despues", "celdas_modificadas", "explicacion_breve", "explicacion_formal",
        ):
            self.assertTrue(hasattr(paso, attribute))

    def test_ningun_paso_divide_entre_cero(self):
        resultado = resolver_sistema([[0, 1, 2], [1, 1, 3]])
        self.assertTrue(all(paso.multiplicador is None or paso.multiplicador.denominator != 0
                            for paso in resultado.pasos))

    def test_verificacion_usa_sistema_original(self):
        matriz = [[2, 1, 5], [1, -1, 1]]
        resultado = resolver_sistema(matriz)
        self.assertEqual(resultado.verificacion[0].coeficientes, (2, 1))
        self.assertEqual(resultado.original, matriz_exacta(matriz))

    def test_caso_a_programa_2(self):
        matriz = [[2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3]]
        resultado = resolver_sistema(matriz)
        self.assertEqual(resultado.rref, matriz_exacta(
            [[1, 0, 0, 2], [0, 1, 0, 3], [0, 0, 1, -1]]))
        self.assertEqual(resultado.columnas_pivote, [0, 1, 2])
        self.assertEqual(resultado.solucion_unica, [2, 3, -1])

    def test_caso_b_programa_2(self):
        resultado = resolver_sistema([[1, 2, -1, 3], [2, 4, -2, 6]])
        self.assertEqual(resultado.rref, matriz_exacta([[1, 2, -1, 3], [0, 0, 0, 0]]))
        self.assertEqual(resultado.columnas_pivote, [0])
        self.assertEqual(resultado.variables_libres, [1, 2])
        self.assertEqual(resultado.solucion_particular, [3, 0, 0])
        self.assertEqual(resultado.vectores_direccion, [[-2, 1, 0], [1, 0, 1]])

    def test_caso_c_pivote_aumentado_separado(self):
        resultado = resolver_sistema([[1, 1, 2], [2, 2, 5]])
        self.assertEqual(resultado.rref, matriz_exacta([[1, 1, 0], [0, 0, 1]]))
        self.assertEqual(resultado.columnas_pivote, [0])
        self.assertEqual(resultado.columnas_pivote_aumentada, [0, 2])
        self.assertEqual(resultado.pivote_contradiccion, (1, 2))
        self.assertEqual(resultado.variables_libres, [])

    def test_rref_cumple_definicion_y_es_idempotente(self):
        matrices = (
            [[0, 2, 4], [1, 3, 5]],
            [[1, 2, -1, 3], [2, 4, -2, 6]],
            [[1, 1, 2], [2, 2, 5]],
            [[0, 0, 1, 2], [0, 2, 3, 4]],
        )
        for matriz in matrices:
            resultado = resolver_sistema(matriz)
            self.assertTrue(es_rref(resultado.rref))
            self.assertEqual(resolver_sistema(resultado.rref).rref, resultado.rref)

    def test_eventos_reproducen_cada_matriz(self):
        resultado = resolver_sistema([[2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3]])
        for paso in resultado.pasos:
            replay = [row[:] for row in paso.matriz_antes]
            if paso.tipo_operacion == "swap":
                replay[paso.fila_origen], replay[paso.fila_destino] = replay[paso.fila_destino], replay[paso.fila_origen]
            elif paso.tipo_operacion == "scale":
                replay[paso.fila_destino] = [value * paso.multiplicador for value in replay[paso.fila_destino]]
            elif paso.tipo_operacion == "replace":
                replay[paso.fila_destino] = [
                    replay[paso.fila_destino][j] - paso.multiplicador * replay[paso.fila_origen][j]
                    for j in range(len(replay[0]))
                ]
            self.assertEqual(replay, paso.matriz_despues)
        self.assertEqual(resultado.pasos[-1].matriz_despues, resultado.rref)

    def test_instantaneas_de_pasos_son_independientes(self):
        resultado = resolver_sistema([[1, 2, 3], [2, 5, 8]])
        original_value = resultado.pasos[1].matriz_antes[0][0]
        resultado.pasos[0].matriz_despues[0][0] = Fraction(99)
        self.assertEqual(resultado.pasos[1].matriz_antes[0][0], original_value)

    def test_pivotes_y_no_pivotes_particionan_a(self):
        resultado = resolver_sistema([[0, 1, 0, 2], [0, 0, 1, 3]])
        self.assertEqual(set(resultado.columnas_pivote) | set(resultado.columnas_no_pivote_a), {0, 1, 2})
        self.assertFalse(set(resultado.columnas_pivote) & set(resultado.columnas_no_pivote_a))

    def test_casos_uno_por_uno_y_ocho_por_nueve(self):
        self.assertEqual(resolver_sistema([[2, 6]]).solucion_unica, [3])
        matriz = [[1 if row == column else 0 for column in range(8)] + [row + 1]
                  for row in range(8)]
        resultado = resolver_sistema(matriz)
        self.assertEqual(resultado.solucion_unica, list(range(1, 9)))
        self.assertTrue(es_rref(resultado.rref))

    def test_limites_de_dimensiones_tambien_se_aplican_en_el_motor(self):
        with self.assertRaisesRegex(ValueError, "máximo 8 ecuaciones"):
            resolver_sistema([[1, 1] for _ in range(9)])
        with self.assertRaisesRegex(ValueError, "máximo 8 ecuaciones"):
            resolver_sistema([[1] * 10])


class PruebasFormatoEducativo(unittest.TestCase):
    def test_formato_fraccion(self):
        self.assertEqual(formatear_numero(Fraction(3, 4)), "3/4")

    def test_formato_decimal_conserva_referencia_exacta(self):
        self.assertEqual(formatear_numero(Fraction(1, 3), "decimales", 4), "1/3 ≈ 0.3333")

    def test_ecuacion_simplifica_unos_y_signos(self):
        self.assertEqual(texto_ecuacion([1, -1, 0, 2]), "x₁ − x₂ = 2")

    def test_matriz_texto_incluye_divisor_aumentado(self):
        self.assertIn("│", texto_matriz(matriz_exacta([[1, 2, 3]])))

    def test_solucion_parametrica_incluye_reales(self):
        resultado = resolver_sistema([[1, 1, 1, 2], [2, 2, 2, 4]])
        self.assertIn("∈ ℝ", lineas_parametricas(resultado)[-1])
        self.assertIn("x = [2, 0, 0]ᵀ", texto_forma_vectorial(resultado))

    def test_reporte_contiene_doce_secciones(self):
        report = construir_reporte(resolver_sistema([[2, 1, 5], [1, -1, 1]]))
        self.assertIn("1. SISTEMA ORIGINAL", report)
        self.assertIn("12. CONCLUSIÓN", report)

    def test_celda_vacia_es_error(self):
        with self.assertRaisesRegex(ValueError, "Ingresa un valor"):
            a_fraccion("")

    def test_denominador_cero_es_error_especifico(self):
        with self.assertRaisesRegex(ZeroDivisionError, "denominador"):
            a_fraccion("1/0")

    def test_texto_invalido_es_rechazado(self):
        with self.assertRaises(ValueError):
            a_fraccion("abc")

    def test_no_finitos_y_expresiones_son_rechazados(self):
        for text in ("NaN", "inf", "1+2", "2**8"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                a_fraccion(text)

    def test_limites_de_entrada(self):
        with self.assertRaisesRegex(ValueError, "caracteres|dígitos"):
            a_fraccion("9" * 70)
        with self.assertRaisesRegex(ValueError, "exponente"):
            a_fraccion("1e101")
        self.assertEqual(a_fraccion("  -6 / -8  ".replace(" ", "")), Fraction(3, 4))


class PruebasPersistenciaYHTML(unittest.TestCase):
    def test_historial_guarda_y_recarga_fracciones_exactas(self):
        with tempfile.TemporaryDirectory() as directory:
            ruta = Path(directory) / "carpeta con acento á" / "historial.json"
            store = AlmacenHistorial(ruta, limite=2)
            self.assertTrue(store.add(resolver_sistema([["1/2", 1, 2], [1, 0, 3]])))
            loaded = AlmacenHistorial(ruta, limite=2)
            self.assertEqual(loaded.entradas[0]["matrix"][0][0], "1/2")
            self.assertEqual(json.loads(ruta.read_text(encoding="utf-8"))["schema_version"], 1)

    def test_historial_corrupto_no_ejecuta_ni_borra_memoria(self):
        with tempfile.TemporaryDirectory() as directory:
            ruta = Path(directory) / "historial.json"
            ruta.write_text("{contenido inválido", encoding="utf-8")
            store = AlmacenHistorial(ruta)
            self.assertEqual(store.entradas, [])
            self.assertIn("No se pudo cargar", store.ultimo_error)

    def test_recarga_corrupta_conserva_historial_que_ya_estaba_en_memoria(self):
        with tempfile.TemporaryDirectory() as directory:
            ruta = Path(directory) / "historial.json"
            store = AlmacenHistorial(ruta)
            self.assertTrue(store.add(resolver_sistema([[1, 1]])))
            anterior = list(store.entradas)
            ruta.write_text("{contenido inválido", encoding="utf-8")
            store.load()
            self.assertEqual(store.entradas, anterior)
            self.assertIn("No se pudo cargar", store.ultimo_error)

    def test_error_de_permiso_conserva_resultado_en_memoria(self):
        with tempfile.TemporaryDirectory() as directory:
            store = AlmacenHistorial(Path(directory) / "historial.json")
            with mock.patch("axion_storage.os.replace", side_effect=PermissionError("denegado")):
                self.assertFalse(store.add(resolver_sistema([[1, 1]])))
            self.assertEqual(len(store.entradas), 1)
            self.assertIn("denegado", store.ultimo_error)

    def test_html_es_autocontenido_y_escapa_contenido(self):
        report = construir_reporte_html(resolver_sistema([[1, 1]]))
        self.assertIn("<!doctype html>", report.lower())
        self.assertIn("@media print", report)
        self.assertNotIn("<script", report.lower())
        self.assertNotIn("http://", report.lower())
        self.assertNotIn("https://", report.lower())

    def test_html_nombra_correctamente_el_metodo_gauss(self):
        report = construir_reporte_html(resolver_sistema([[1, 1]], "gauss"))
        self.assertIn("Procedimiento de eliminación de Gauss", report)
        self.assertIn("Forma escalonada e interpretación", report)


class PruebasInterfazIntegral(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.raiz = tk.Tk()
        self.raiz.withdraw()
        self.aplicacion = AplicacionAxion(
            self.raiz, almacen_historial=AlmacenHistorial(Path(self.temp.name) / "historial.json"))
        self.raiz.update_idletasks()

    def tearDown(self):
        self.raiz.destroy()
        self.temp.cleanup()

    def load_unique(self):
        self.aplicacion.editor.establecer_valores([[2, 1, 5], [1, -1, 1]])

    @staticmethod
    def _buttons(widget):
        found = []
        for hijo in widget.winfo_children():
            if hijo.winfo_class() == "Button":
                found.append(hijo)
            found.extend(PruebasInterfazIntegral._buttons(hijo))
        return found

    def test_estado_inicial_no_interpreta_vacios_como_cero(self):
        self.assertEqual(self.aplicacion.editor.boton_resolver.cget("state"), "disabled")
        self.assertIn("Faltan 6 valores", self.aplicacion.editor.estado_entrada.cget("text"))
        self.assertEqual(self.aplicacion.editor.metodo.get(), "Gauss-Jordan")
        self.assertEqual(self.aplicacion.etapa_actual, "definir")
        self.assertEqual(self.aplicacion.botones_etapas["resolver"].cget("state"), "disabled")
        self.assertEqual(self.aplicacion.botones_etapas["interpretar"].cget("state"), "disabled")
        self.assertTrue(self.raiz.bind("<Control-z>"))

    def test_ejemplo_no_se_resuelve_automaticamente(self):
        self.aplicacion.editor.ejemplo.set("Solución única")
        self.aplicacion.editor.cargar_ejemplo()
        self.assertIsNone(self.aplicacion.resultado)
        self.assertEqual(self.aplicacion.editor.boton_resolver.cget("state"), "normal")

    def test_ejemplo_ocho_por_ocho_respeta_limite(self):
        self.aplicacion.editor.ejemplo.set("Prueba 8×8")
        self.aplicacion.editor.cargar_ejemplo()
        self.assertEqual(self.aplicacion.editor.filas.get(), 8)
        self.assertEqual(self.aplicacion.editor.variables.get(), 8)
        self.assertEqual(len(self.aplicacion.editor.variables_celdas[0]), 9)
        self.assertIsNone(self.aplicacion.resultado)

    def test_resolver_conserva_entrada_original(self):
        self.load_unique()
        antes = self.aplicacion.editor.obtener_valores()
        self.aplicacion.resolver()
        self.assertEqual(self.aplicacion.editor.obtener_valores(), antes)
        self.assertEqual(self.aplicacion.resultado.original, antes)
        self.assertEqual(self.aplicacion.etapa_actual, "resolver")
        self.assertEqual(self.aplicacion.botones_etapas["interpretar"].cget("state"), "normal")
        self.assertEqual(self.aplicacion.cuaderno.paso_activo, 0)
        self.assertEqual(self.aplicacion.resultado.pasos[0].tipo_operacion, "initial")

    def test_vista_ecuaciones_sincronizada(self):
        self.load_unique()
        self.aplicacion.editor.mostrar_vista("ecuaciones")
        self.assertIn("2x₁ + x₂ = 5", self.aplicacion.editor.etiqueta_ecuaciones.cget("text"))

    def test_validacion_denominador_cero(self):
        self.aplicacion.editor.variables_celdas[0][0].set("1/0")
        self.assertFalse(self.aplicacion.editor.validar_celda(0, 0))
        self.assertIn("denominador", self.aplicacion.editor.error_en_linea.cget("text"))

    def test_aumentar_dimensiones_conserva_valores(self):
        self.load_unique()
        self.aplicacion.editor.filas.set(3)
        self.aplicacion.editor.variables.set(3)
        self.aplicacion.editor.aplicar_dimensiones()
        self.assertEqual(self.aplicacion.editor.variables_celdas[0][0].get(), "2")
        self.assertEqual(len(self.aplicacion.editor.variables_celdas), 3)

    def test_navegacion_de_procedimiento(self):
        self.load_unique()
        self.aplicacion.resolver()
        buttons = self._buttons(self.aplicacion.cuaderno.pestana_procedimiento)
        anterior = next(boton for boton in buttons if boton.cget("text") == "← Paso anterior")
        self.assertEqual(anterior.cget("state"), "disabled")
        self.aplicacion.cuaderno.cambiar_paso(1)
        self.assertEqual(self.aplicacion.cuaderno.paso_activo, 1)
        self.aplicacion.cuaderno.seleccionar_paso(len(self.aplicacion.resultado.pasos) - 1)
        buttons = self._buttons(self.aplicacion.cuaderno.pestana_procedimiento)
        following = next(boton for boton in buttons if boton.cget("text") == "Paso siguiente →")
        self.assertEqual(following.cget("state"), "disabled")

    def test_comparador_define_distribucion_segun_ancho_real(self):
        self.load_unique()
        self.aplicacion.resolver()
        paso = self.aplicacion.resultado.pasos[0]
        self.assertFalse(self.aplicacion.cuaderno._usa_distribucion_ancha_paso(paso, 1024))
        self.assertTrue(self.aplicacion.cuaderno._usa_distribucion_ancha_paso(paso, 1600))
        self.assertEqual(self.aplicacion.cuaderno.paso_activo, 0)

    def test_cambio_de_modo_no_recalcula(self):
        self.load_unique()
        self.aplicacion.resolver()
        identity = id(self.aplicacion.resultado)
        self.aplicacion.modo_uso.set("rapido")
        self.aplicacion.actualizar_visualizacion()
        self.assertEqual(id(self.aplicacion.resultado), identity)

    def test_modo_rapido_abre_interpretacion(self):
        self.load_unique()
        self.aplicacion.modo_uso.set("rapido")
        self.aplicacion.resolver()
        self.assertEqual(self.aplicacion.etapa_actual, "interpretar")

    def test_cambio_de_formato_no_recalcula(self):
        self.load_unique()
        self.aplicacion.resolver()
        identity = id(self.aplicacion.resultado)
        self.aplicacion.modo_visualizacion.set("decimales")
        self.aplicacion.actualizar_visualizacion()
        self.assertEqual(id(self.aplicacion.resultado), identity)

    def test_precision_decimal_se_normaliza(self):
        self.aplicacion.precision.set(30)
        self.aplicacion.actualizar_visualizacion()
        self.assertEqual(self.aplicacion.precision.get(), 10)

    def test_precision_se_oculta_en_fracciones(self):
        self.aplicacion.modo_visualizacion.set("fracciones")
        self.aplicacion.actualizar_visualizacion()
        self.assertFalse(self.aplicacion.control_precision.winfo_manager())
        self.assertEqual(self.aplicacion.etiqueta_formato.cget("text"), "Resultados exactos")
        self.aplicacion.modo_visualizacion.set("decimales")
        self.aplicacion.actualizar_visualizacion()
        self.assertEqual(self.aplicacion.control_precision.winfo_manager(), "pack")
        self.assertIn("aproximados (≈)", self.aplicacion.etiqueta_formato.cget("text"))

    def test_cabecera_se_adapta_sin_reducir_tipografia(self):
        self.aplicacion._distribucion_adaptable(SimpleNamespace(
            widget=self.raiz, width=850, height=700))
        self.assertEqual(self.aplicacion._layout_mode, "estrecho")
        self.assertEqual(self.aplicacion.botones_etapas["interpretar"].cget("text"), "3. Interpretar")
        self.assertFalse(self.aplicacion.etiqueta_motor.winfo_manager())
        self.aplicacion._distribucion_adaptable(SimpleNamespace(
            widget=self.raiz, width=1280, height=800))
        self.assertEqual(self.aplicacion.botones_etapas["interpretar"].cget("text"),
                         "3. Interpretar y verificar")

    def test_expresiones_con_signo_no_muestran_mas_menos(self):
        expresion = self.aplicacion.cuaderno._expresion_con_signo(((2, "2"), (-1, "1"), (3, "3")))
        self.assertEqual(expresion, "2 − 1 + 3")
        self.assertNotIn("+ -", expresion)

    def test_restaurar_original(self):
        self.load_unique()
        self.aplicacion.resolver()
        self.aplicacion.editor.variables_celdas[0][0].set("99")
        self.aplicacion.editor.restaurar_original()
        self.assertEqual(self.aplicacion.editor.variables_celdas[0][0].get(), "2")

    def test_editar_invalida_pero_conserva_resultado_anterior(self):
        self.load_unique()
        self.aplicacion.resolver()
        anterior = self.aplicacion.resultado
        self.aplicacion.editor.variables_celdas[0][0].set("7")
        self.assertIs(self.aplicacion.resultado, anterior)
        self.assertTrue(self.aplicacion.resultado_desactualizado)
        self.assertIn("RESULTADO ANTERIOR", self.aplicacion.cuaderno.insignia_metodo.cget("text"))

    def test_deshacer_hasta_la_entrada_resuelta_revalida_el_resultado(self):
        self.load_unique()
        self.aplicacion.resolver()
        self.aplicacion.editor.instantanea()
        self.aplicacion.editor.variables_celdas[0][0].set("7")
        self.assertTrue(self.aplicacion.resultado_desactualizado)
        self.aplicacion.editor.deshacer()
        self.assertFalse(self.aplicacion.resultado_desactualizado)
        self.assertIn("Método utilizado", self.aplicacion.cuaderno.insignia_metodo.cget("text"))

    def test_limpiar_entrada_se_puede_deshacer(self):
        self.load_unique()
        self.aplicacion.editor.limpiar_matriz()
        self.assertEqual(self.aplicacion.editor.variables_celdas[0][0].get(), "")
        self.aplicacion.editor.deshacer()
        self.assertEqual(self.aplicacion.editor.variables_celdas[0][0].get(), "2")

    def test_limpiar_no_elimina_la_entrada_del_resultado_resuelto(self):
        self.load_unique()
        self.aplicacion.resolver()
        original = [row[:] for row in self.aplicacion.editor.instantanea_original]
        self.aplicacion.editor.limpiar_matriz()
        self.assertEqual(self.aplicacion.editor.instantanea_original, original)
        self.aplicacion.editor.restaurar_original()
        self.assertEqual(self.aplicacion.editor.obtener_valores(), self.aplicacion.resultado.original)

    def test_flechas_horizontales_conservan_el_cursor_dentro_de_la_celda(self):
        entrada = self.aplicacion.editor.entradas[0][0]
        entrada.delete(0, "end")
        entrada.insert(0, "123")
        entrada.icursor(1)
        event = SimpleNamespace(widget=entrada)
        self.assertIsNone(self.aplicacion.editor._movimiento_horizontal(event, 0, 0, 1))
        entrada.icursor("end")
        self.assertEqual(self.aplicacion.editor._movimiento_horizontal(event, 0, 0, 1), "break")

    def test_navegacion_y_atajos_no_crean_falsos_estados_de_deshacer(self):
        self.aplicacion.editor.pila_deshacer.clear()
        for event in (
            SimpleNamespace(keysym="Left", state=0, char=""),
            SimpleNamespace(keysym="c", state=4, char="\x03"),
            SimpleNamespace(keysym="Tab", state=0, char="\t"),
        ):
            self.aplicacion.editor._antes_tecla(event)
        self.assertEqual(self.aplicacion.editor.pila_deshacer, [])
        self.aplicacion.editor._antes_tecla(SimpleNamespace(keysym="BackSpace", state=0, char="\x08"))
        self.assertEqual(len(self.aplicacion.editor.pila_deshacer), 1)

    def test_pegado_invalido_es_atomico(self):
        self.load_unique()
        antes = [[value.get() for value in row] for row in self.aplicacion.editor.variables_celdas]
        self.raiz.clipboard_clear()
        self.raiz.clipboard_append("1\t2\n3")
        self.aplicacion.editor.pegado_inteligente()
        despues = [[value.get() for value in row] for row in self.aplicacion.editor.variables_celdas]
        self.assertEqual(despues, antes)

    def test_pegado_con_celda_vacia_no_colapsa_columnas(self):
        self.load_unique()
        antes = self.aplicacion.editor.obtener_valores()
        self.raiz.clipboard_clear()
        self.raiz.clipboard_append("1\t\t3\n4\t5\t6")
        self.aplicacion.editor.pegado_inteligente()
        self.assertEqual(self.aplicacion.editor.obtener_valores(), antes)
        self.assertIn("celda vacía", self.aplicacion.editor.error_en_linea.cget("text"))

    def test_pegado_tabulado_se_previsualiza_y_aplica(self):
        self.raiz.clipboard_clear()
        self.raiz.clipboard_append("1\t2\t3\n4\t5\t6")
        with mock.patch("axion_ui.messagebox.askyesno", return_value=True):
            self.aplicacion.editor.pegado_inteligente()
        self.assertEqual(self.aplicacion.editor.obtener_valores(), matriz_exacta([[1, 2, 3], [4, 5, 6]]))

    def test_coma_ambigua_no_se_adivina(self):
        self.load_unique()
        antes = self.aplicacion.editor.obtener_valores()
        self.raiz.clipboard_clear()
        self.raiz.clipboard_append("1,2,3\n4,5,6")
        with mock.patch("axion_ui.messagebox.askyesnocancel", return_value=False):
            self.aplicacion.editor.pegado_inteligente()
        self.assertEqual(self.aplicacion.editor.obtener_valores(), antes)

    def test_reporte_se_genera_en_interfaz(self):
        self.load_unique()
        self.aplicacion.resolver()
        self.assertIn("AXION", self.aplicacion.cuaderno.texto_reporte.get("1.0", "end"))
        self.assertEqual(str(self.aplicacion.cuaderno.reporte_horizontal.cget("orient")), "horizontal")
        self.assertTrue(self.aplicacion.cuaderno.visor_matriz_final.horizontal_habilitado)

    def test_impresion_informa_si_no_hay_navegador(self):
        self.load_unique()
        self.aplicacion.resolver()
        with mock.patch("axion_ui.webbrowser.open", return_value=False):
            self.aplicacion.cuaderno.abrir_reporte_para_imprimir()
        self.assertIn("No se encontró un navegador", self.aplicacion.etiqueta_estado.cget("text"))

    def test_rueda_en_matriz_horizontal_desplaza_el_panel_vertical_exterior(self):
        self.load_unique()
        self.aplicacion.resolver()
        event = SimpleNamespace(
            widget=self.aplicacion.cuaderno.visor_matriz_final.contenido, delta=-120,
        )
        with mock.patch.object(self.aplicacion.cuaderno.pestana_resultado.canvas, "yview_scroll") as outer:
            with mock.patch.object(self.aplicacion.cuaderno.visor_matriz_final.canvas, "yview_scroll") as inner:
                self.aplicacion._dirigir_rueda_raton(event)
        outer.assert_called_once()
        inner.assert_not_called()

    def test_error_inesperado_del_motor_no_cierra_la_interfaz(self):
        self.load_unique()
        with mock.patch("axion_ui.resolver_sistema", side_effect=RuntimeError("fallo simulado")):
            self.aplicacion.resolver()
        self.assertIsNone(self.aplicacion.resultado)
        self.assertIn("datos originales se conservaron", self.aplicacion.etiqueta_estado.cget("text"))
        self.assertEqual(self.aplicacion.editor.boton_resolver.cget("state"), "normal")

    def test_guardado_txt_y_html_es_real(self):
        self.load_unique()
        self.aplicacion.resolver()
        txt = Path(self.temp.name) / "reporte.txt"
        html_path = Path(self.temp.name) / "reporte.html"
        with mock.patch("axion_ui.filedialog.asksaveasfilename", return_value=str(txt)):
            self.aplicacion.cuaderno.guardar_reporte()
        with mock.patch("axion_ui.filedialog.asksaveasfilename", return_value=str(html_path)):
            self.aplicacion.cuaderno.guardar_html()
        self.assertIn("rango(A)", txt.read_text(encoding="utf-8"))
        self.assertIn("<!doctype html>", html_path.read_text(encoding="utf-8").lower())

    def test_procedimiento_se_puede_copiar(self):
        self.load_unique()
        self.aplicacion.resolver()
        self.aplicacion.cuaderno.copiar_procedimiento()
        copied = self.raiz.clipboard_get()
        self.assertIn("PASO 01", copied)
        self.assertIn("Antes:", copied)
        self.assertIn("Después:", copied)

    def test_tres_clasificaciones_visuales(self):
        cases = (
            ([[2, 1, 5], [1, -1, 1]], "unica"),
            ([[1, 1, 1, 2], [2, 2, 2, 4]], "infinitas"),
            ([[1, 1, 2], [1, 1, 5]], "inconsistente"),
        )
        for matriz, clasificacion in cases:
            self.aplicacion.editor.establecer_valores(matriz)
            self.aplicacion.resolver()
            self.assertEqual(self.aplicacion.resultado.clasificacion, clasificacion)


if __name__ == "__main__":
    unittest.panel_principal()
