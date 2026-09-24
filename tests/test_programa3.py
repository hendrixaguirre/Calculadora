"""Referencias A–K, contratos, propiedades e integración real Tk de Programa 3."""
import copy
import tempfile
import tkinter as tk
import unittest
from fractions import Fraction as F
from pathlib import Path
from unittest.mock import patch

from axion_core import a_fraccion, es_rref, texto_matriz
from axion_operaciones import (
    OPERACIONES, calcular_operacion, combinacion_lineal, dimension, escalar_matriz,
    escalar_vector, interpretar_tabla, multiplicar_matrices, reporte_operacion,
    resolver_ax_b, restar_matrices, restar_vectores, resumen_combinacion,
    sumar_matrices, sumar_vectores, validar_matriz, texto_tabla, pasos_propiedad,
)
from axion_programa3 import AplicacionPrograma3
from axion_storage import AlmacenHistorial


class PruebasPrograma3(unittest.TestCase):
    def test_propiedades_casos_del_profesor(self):
        for op, b, c, esperados in (
            ('propiedad_distributiva', [[1, 2], [3, 1]], None,
             {'u_mas_v': [4, 3], 'au': [5, 11], 'av': [5, 13],
              'lado_izquierdo': [10, 24], 'lado_derecho': [10, 24]}),
            ('propiedad_escalar', [[2, 1]], 3,
             {'cu': [6, 3], 'au': [4, 10],
              'lado_izquierdo': [12, 30], 'lado_derecho': [12, 30]}),
        ):
            with self.subTest(operacion=op):
                r = calcular_operacion(op, [[1, 2], [3, 4]], b, c)
                self.assertIsNone(r.salida)
                self.assertIsNone(r.sistema)
                self.assertTrue(r.propiedad['se_cumple'])
                for clave, valor in esperados.items():
                    self.assertEqual(r.propiedad[clave], valor)
                self.assertIn('diferencia exacta: 0', reporte_operacion(r))

    def test_propiedades_rectangulares_fracciones_y_escalar_cero(self):
        a = [['1/3', '-2/5'], [2, 0], ['0.25', 3]]
        for c in ('-2/7', '0', '0.5'):
            for op, b in [('propiedad_escalar', [['2/3', '-1/2']]),
                          ('propiedad_distributiva', [['2/3', '-1/2'], ['1/7', 2]])]:
                r = calcular_operacion(op, a, b, c)
                antes = copy.deepcopy(r)
                for modo in ('fracciones', 'decimales'):
                    pasos = pasos_propiedad(r, modo)
                    self.assertTrue(all(pasos))
                    self.assertIn('La propiedad se cumple', pasos[-1])
                    self.assertIn('Componente 3:', pasos[-1])
                    if modo == 'decimales':
                        self.assertIn('≈', '\n'.join(pasos))
                self.assertEqual(r, antes)
                self.assertEqual(r.propiedad['lado_izquierdo'], r.propiedad['lado_derecho'])
                self.assertTrue(all(isinstance(v, F) for v in r.propiedad['lado_izquierdo']))

    def test_corchetes_textuales_y_alineacion(self):
        a = [[1, 2, 3], [12, '-1/3', 6], [7, 8, 9]]
        for modo in ('fracciones', 'decimales'):
            for render in (texto_tabla, texto_matriz):
                lineas = render(a, modo).splitlines()
                self.assertEqual([l[0] for l in lineas], ['⎡', '⎢', '⎣'])
                self.assertEqual([l[-1] for l in lineas], ['⎤', '⎥', '⎦'])
                self.assertEqual(len({len(l) for l in lineas}), 1)
        self.assertEqual(texto_tabla([[1, 2, 3]]), '[ 1   2   3 ]')
        self.assertEqual(texto_tabla([[1], [2]]), '⎡ 1 ⎤\n⎣ 2 ⎦')

    def test_a_vectores(self):
        u, v = ['1/2', -2, 3], ['3/2', 5, -1]
        self.assertEqual(sumar_vectores(u,v), [2,3,2])
        self.assertEqual(restar_vectores(u,v), [-1,-7,4])
        self.assertEqual(escalar_vector(-2,u), [-1,4,-6])
        self.assertEqual(escalar_vector(10,['0.1','0.2']), [1,2])

    def test_b_matrices(self):
        s, t = [[1,-2],[3,0]], [[4,5],[-1,2]]
        self.assertEqual(sumar_matrices(s,t), [[5,3],[2,2]])
        self.assertEqual(restar_matrices(s,t), [[-3,-7],[4,-2]])
        self.assertEqual(escalar_matriz(-2,s), [[-2,4],[-6,0]])

    def test_c_producto_y_cuatro_detalles(self):
        r = calcular_operacion('matriz_producto', [[1,2,3],[4,5,6]], [[7,8],[9,10],[11,12]])
        self.assertEqual(r.salida, [[58,64],[139,154]])
        for i,j,valor in [(0,0,58),(0,1,64),(1,0,139),(1,1,154)]:
            self.assertTrue(r.detalle(i,j).endswith('= '+str(valor)))
        self.assertIn('(1)·(8) + (2)·(10) + (3)·(12)', r.detalle(0,1))

    def test_d_incompatibles(self):
        for funcion in (sumar_matrices, restar_matrices, multiplicar_matrices):
            with self.subTest(funcion=funcion.__name__), self.assertRaises(ValueError):
                funcion([[1,2,3],[4,5,6]], [[1,2],[3,4]])
        with self.assertRaises(ValueError):
            sumar_vectores([1,2],[1])
        with self.assertRaises(ValueError):
            restar_vectores([1],[1,2])

    def test_e_orden(self):
        p, q = [[1,1],[0,1]], [[1,0],[1,1]]
        self.assertEqual(multiplicar_matrices(p,q), [[2,1],[1,1]])
        self.assertEqual(multiplicar_matrices(q,p), [[1,1],[1,2]])

    def test_f_combinacion_columnas(self):
        s = combinacion_lineal([[1,0,1],[0,1,1]], [2,3,5])
        self.assertEqual(s.original, [[1,0,2],[0,1,3],[1,1,5]])
        self.assertEqual(s.solucion_unica, [2,3])
        self.assertEqual(s.rango_a, 2)
        self.assertTrue(all(l.valida for l in s.verificacion))

    def test_g_imposible(self):
        s = combinacion_lineal([[1,0,1],[0,1,1]], [2,3,6])
        self.assertEqual(s.clasificacion, 'inconsistente')
        self.assertEqual((s.rango_a,s.rango_aumentada), (2,3))
        self.assertIsNone(s.solucion_unica)
        self.assertNotIn('Verificado', resumen_combinacion(s))

    def test_h_familia_completa(self):
        s = combinacion_lineal([[1,2],[2,4]], [3,6])
        self.assertEqual(s.solucion_particular, [3,0])
        self.assertEqual(s.vectores_direccion, [[-2,1]])
        self.assertTrue(s.verificacion_particular and s.verificacion_direcciones)
        self.assertIn('Sí es combinación', resumen_combinacion(s))

    def test_i_regresion_unica(self):
        s = resolver_ax_b([[2,1,-1],[-3,-1,2],[-2,1,2]], [8,-11,-3])
        self.assertEqual(s.solucion_unica, [2,3,-1])

    def test_j_regresion_familia(self):
        s = resolver_ax_b([[1,2,-1],[2,4,-2]], [3,6])
        self.assertEqual(s.solucion_particular, [3,0,0])
        self.assertEqual(s.vectores_direccion, [[-2,1,0],[1,0,1]])
        self.assertTrue(s.verificacion_particular and s.verificacion_direcciones)

    def test_k_rref_inconsistente(self):
        s = resolver_ax_b([[1,1],[2,2]], [2,5])
        self.assertEqual(s.rref, [[1,1,0],[0,0,1]])
        self.assertTrue(es_rref(s.rref))
        self.assertEqual((s.rango_a,s.rango_aumentada), (1,2))
        self.assertEqual(s.columnas_pivote, [0])

    def test_cero_y_dimension_uno(self):
        self.assertEqual(sumar_vectores([0],[0]), [0])
        self.assertEqual(multiplicar_matrices([[2]], [['1/2']]), [[1]])
        s = combinacion_lineal([[0,0],[0,0]], [0,0])
        self.assertEqual(s.clasificacion, 'infinitas')
        self.assertEqual(len(s.vectores_direccion), 2)
        self.assertTrue(s.verificacion_direcciones)
        self.assertEqual(combinacion_lineal([[0,0]], [1,0]).clasificacion, 'inconsistente')

    def test_k_mayor_n_y_repetidos(self):
        s = combinacion_lineal([[1,0],[0,1],[1,0],[0,0]], [2,3])
        self.assertEqual(len(s.variables_libres), 2)
        self.assertTrue(s.verificacion_particular and s.verificacion_direcciones)

    def test_identidad_cero_distributividad(self):
        a, b, c = [[1,2],[-3,F(1,2)]], [[2,0],[1,3]], [[4,1],[2,-1]]
        self.assertEqual(multiplicar_matrices(a,[[1,0],[0,1]]), a)
        self.assertEqual(multiplicar_matrices(a,[[0],[0]]), [[0],[0]])
        self.assertEqual(multiplicar_matrices(a,sumar_matrices(b,c)),
                         sumar_matrices(multiplicar_matrices(a,b),multiplicar_matrices(a,c)))
        self.assertEqual(sumar_vectores([1,2],[3,4]), sumar_vectores([3,4],[1,2]))

    def test_inmutabilidad_e_instantaneas(self):
        a, b = [[1,2],[3,4]], [[5,6],[7,8]]
        copia = copy.deepcopy((a,b))
        r = calcular_operacion('matriz_producto',a,b)
        self.assertEqual((a,b),copia)
        a[0][0]=99
        b[1][1]=99
        self.assertEqual(r.a[0][0], 1)
        self.assertEqual(r.b[1][1], 8)
        r.salida[0][0]=0
        self.assertEqual(r.salida[1][0],43)

    def test_validacion_ubicacion(self):
        with self.assertRaisesRegex(ValueError, 'Matriz B, fila 2, columna 3'):
            validar_matriz([[1,2,3],[4,5,'1/0']], 'Matriz B')

    def test_malformados(self):
        for datos in ([], [[]], [[1],[1,2]], [[1]*9], [[1]]*9):
            with self.subTest(datos=datos), self.assertRaises(ValueError):
                validar_matriz(datos)
        for valor in ('NaN','inf','1/0','', '1 + 2', '1 2', '2**3', '9'*65, '1e101'):
            with self.subTest(valor=valor), self.assertRaises((ValueError,ZeroDivisionError)):
                a_fraccion(valor)

    def test_dimensiones_enteras_positivas(self):
        for v in (0,-1,9,True,1.0,'1.5',''):
            with self.subTest(v=v), self.assertRaises(ValueError):
                dimension(v)
        self.assertEqual(dimension('8'),8)

    def test_decimal_de_resultado_grande_sin_float(self):
        from axion_core import formatear_numero, numero_compacto
        valor = F(10**400+1,3)
        self.assertIn('≈',formatear_numero(valor,'decimales'))
        self.assertTrue(numero_compacto(F(1,3),'decimales').startswith('≈'))

    def test_ocho_por_ocho(self):
        a = [[F(i+j,7) for j in range(8)] for i in range(8)]
        identidad = [[int(i==j) for j in range(8)] for i in range(8)]
        self.assertEqual(multiplicar_matrices(a,identidad),a)
        self.assertEqual(len(resolver_ax_b(identidad,[1]*8).original[0]),9)

    def test_pegado_contrato(self):
        self.assertEqual(interpretar_tabla('0,1\t2\n3\t4'), [['0,1','2'],['3','4']])
        for texto in ('1\t\n2\t3','1\t2\n3', '1,2,3', '1'*4097):
            with self.subTest(texto=texto[:30]), self.assertRaises(ValueError):
                interpretar_tabla(texto)

    def test_reportes_datos_reales(self):
        r = calcular_operacion('vector_escalar', [['0.1','0.2']], escalar=10)
        self.assertIn('[ 1   2 ]',reporte_operacion(r))
        self.assertNotIn('Verificado',reporte_operacion(r))
        r = calcular_operacion('combinacion', [[1,2],[2,4]], [[3,6]])
        self.assertIn('TODAS las direcciones: correcto',reporte_operacion(r))

    def test_historial_mixto_y_corrupcion(self):
        with tempfile.TemporaryDirectory() as temp:
            ruta = Path(temp)/'historial.json'
            h = AlmacenHistorial(ruta)
            h.add(resolver_ax_b([[1]],[2]))
            h.add_operacion(calcular_operacion('vector_suma',[['1/3']],[['2/3']]))
            nuevo = AlmacenHistorial(ruta)
            self.assertEqual(len(nuevo.entradas),2)
            self.assertEqual(nuevo.entradas[0]['a'],[['1/3']])
            ruta.write_text('{"schema_version":1,"entries":[{"kind":"operacion"}]}',encoding='utf-8')
            nuevo.load()
            self.assertEqual(len(nuevo.entradas),2)
            self.assertTrue(nuevo.ultimo_error)


class PruebasInterfazPrograma3(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.raiz = tk.Tk()
        self.raiz.withdraw()
        self.app = AplicacionPrograma3(self.raiz, AlmacenHistorial(Path(self.temp.name)/'historial.json'))
        self.t = self.app.espacios['matrices'].actual

    def tearDown(self):
        self.raiz.update_idletasks()
        self.raiz.destroy()
        self.temp.cleanup()

    def resolver(self):
        self.t.ejemplo()
        self.t.calcular()

    @staticmethod
    def widgets(widget):
        for hijo in widget.winfo_children():
            yield hijo
            yield from PruebasInterfazPrograma3.widgets(hijo)

    def propiedad(self, operacion):
        self.app.mostrar_modulo('propiedades')
        espacio = self.app.espacios['propiedades']
        espacio.seleccionar(operacion)
        t = espacio.actual
        t.ejemplo()
        return t

    def test_propiedades_botones_recorrido_y_resultado(self):
        for op, cantidad, resultado, conceptos in (
            ('propiedad_distributiva', 7, '(10, 24)', ['u =', 'v =', 'u + v =', 'A(u + v) =', 'Au =', 'Av =', 'Au + Av =']),
            ('propiedad_escalar', 6, '(12, 30)', ['u =', 'c = 3', 'cu = (6, 3)', 'A(cu) =', 'Au = (4, 10)', 'c(Au) =']),
        ):
            with self.subTest(operacion=op):
                t = self.propiedad(op)
                boton = next(w for w in self.widgets(t) if w.winfo_class() == 'TButton'
                             and w.cget('text') == OPERACIONES[op])
                errores = []
                with patch.object(self.raiz, 'report_callback_exception', side_effect=lambda *e: errores.append(e)):
                    boton.invoke()
                self.assertEqual(errores, [])
                self.assertEqual(t.numero_pasos(), cantidad)
                self.assertEqual(t.notebook.index(t.notebook.select()), 1)
                self.assertEqual(str(t.atras.cget('state')), 'disabled')
                textos = [t.texto_paso.get('1.0', 'end')]
                for paso in range(1, cantidad):
                    t.adelante.invoke()
                    self.assertEqual(t.paso, paso)
                    textos.append(t.texto_paso.get('1.0', 'end'))
                self.assertEqual(str(t.adelante.cget('state')), 'disabled')
                t.cambiar_paso(99)
                self.assertEqual(t.paso, cantidad-1)
                for concepto in conceptos:
                    self.assertIn(concepto, '\n'.join(textos))
                self.assertIn(resultado, textos[-1])
                self.assertIn('La propiedad se cumple', textos[-1])
                for _ in range(cantidad-1):
                    t.atras.invoke()
                self.assertEqual(t.paso, 0)
                siguiente = next(w for w in self.widgets(t.procedimiento)
                                 if w.winfo_class() == 'TButton' and w.cget('text') == 'Ir al resultado')
                siguiente.invoke()
                self.assertEqual(t.notebook.index(t.notebook.select()), 2)
                self.assertIn(resultado, t.texto_resultado.get('1.0', 'end'))
                self.assertFalse(t.selector.winfo_manager())
                self.assertFalse(t.detalle.master.winfo_manager())

    def test_propiedades_formato_modo_rapido_y_atajos(self):
        for op in ('propiedad_distributiva', 'propiedad_escalar'):
            t = self.propiedad(op)
            t.a.variables[0][0].set('1/3')
            self.app.modo_uso.set('rapido')
            t.calcular()
            self.assertEqual(t.notebook.index(t.notebook.select()), 2)
            r = copy.deepcopy(t.resultado)
            t.notebook.select(1)
            self.app._atajo_paso(1)
            self.assertEqual(t.paso, 1)
            self.app._atajo_paso(-1)
            self.assertEqual(t.paso, 0)
            with patch('axion_workbench.calcular_operacion', side_effect=AssertionError('Recalculó')):
                for modo in ('decimales', 'fracciones'):
                    self.app.modo_visualizacion.set(modo)
                    t.renderizar()
                    self.assertEqual(t.resultado, r)
                    self.assertEqual('≈' in t.texto_resultado.get('1.0', 'end'), modo == 'decimales')
                    for _ in range(t.numero_pasos()):
                        t.cambiar_paso(1)
                    t.cambiar_paso(-99)

    def test_propiedades_historial_reabre_modulo_correcto(self):
        for op in ('propiedad_distributiva', 'propiedad_escalar'):
            t = self.propiedad(op)
            t.calcular()
            esperado = t.instantanea()
            t.limpiar()
            self.app.mostrar_modulo('matrices')
            self.app.mostrar_historial()
            dialogo = next(w for w in self.raiz.winfo_children() if isinstance(w, tk.Toplevel))
            lista = next(w for w in self.widgets(dialogo) if isinstance(w, tk.Listbox))
            lista.selection_set(0)
            boton = next(w for w in self.widgets(dialogo) if w.winfo_class() == 'TButton'
                         and w.cget('text') == 'Editar una copia')
            errores = []
            with patch.object(self.raiz, 'report_callback_exception', side_effect=lambda *e: errores.append(e)):
                boton.invoke()
            self.assertEqual(errores, [])
            self.assertEqual(self.app.modulo, 'propiedades')
            self.assertEqual(self.app.espacios['propiedades'].actual.operacion, op)
            self.assertEqual(t.instantanea(), esperado)
            self.assertEqual(t.notebook.index(t.notebook.select()), 0)

    def test_propiedades_exportacion_y_edicion_conservan_evidencia(self):
        for op in ('propiedad_distributiva', 'propiedad_escalar'):
            t = self.propiedad(op)
            t.calcular()
            r = t.resultado
            for extension in ('txt', 'html'):
                ruta = Path(self.temp.name) / (op + '.' + extension)
                with patch('axion_workbench.filedialog.asksaveasfilename', return_value=str(ruta)):
                    t.guardar(extension)
                contenido = ruta.read_text(encoding='utf-8')
                self.assertIn('La propiedad se cumple', contenido)
                self.assertIn('diferencia exacta: 0', contenido)
            t.a.variables[0][0].set('99')
            self.assertIn('Entrada modificada', t.estado.get())
            self.assertIs(t.resultado, r)
            t.deshacer()
            self.assertIn('vigente', t.estado.get())
            self.assertEqual(t.a.datos()[0][0], '1')
        recargado = AlmacenHistorial(self.app.historial.ruta)
        self.assertFalse(recargado.ultimo_error)
        self.assertEqual([e['operation'] for e in recargado.entradas],
                         ['propiedad_escalar', 'propiedad_distributiva'])

    def test_corchetes_redimensionan_y_matriz_decimal_no_se_parte(self):
        self.raiz.deiconify()
        for n in (1, 8, 3):
            a = [[F(i+j+1, 3) for j in range(n)] for i in range(n)]
            self.t.transaccion(lambda: self.t.cargar({'a': a, 'b': a, 'escalar': ''}))
            self.raiz.update()
            self.assertEqual(len(self.t.a.corchetes), 2)
            for corchete in self.t.a.corchetes:
                self.assertEqual(int(corchete.grid_info()['rowspan']), n)
                self.assertEqual(len(corchete.find_withtag('corchete')), 1)
            self.t.calcular()
            for modo in ('fracciones', 'decimales'):
                self.app.modo_visualizacion.set(modo)
                self.t.renderizar()
                contenido = self.t.texto_resultado.get('1.0', 'end')
                self.assertEqual('≈' in contenido.split('Selecciona')[0], modo == 'decimales')
                self.assertEqual(str(self.t.texto_resultado.tag_cget('numero', 'wrap')), 'none')
                self.assertEqual(str(self.t.texto_resultado.tag_cget('numero', 'spacing3')), '0')
            self.t.notebook.select(0)

    def test_corchetes_editores_y_coleccion_de_vectores(self):
        a = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
        self.raiz.deiconify()
        self.t.transaccion(lambda: self.t.cargar({'a': a, 'b': a, 'escalar': ''}))
        self.raiz.update()
        for editor in (self.t.a, self.t.b):
            self.assertEqual(len(editor.corchetes), 2)
            for corchete in editor.corchetes:
                self.assertEqual(int(corchete.grid_info()['rowspan']), 3)
                self.assertGreaterEqual(corchete.winfo_height(),
                    editor.celdas[-1][0].winfo_y() + editor.celdas[-1][0].winfo_height()
                    - editor.celdas[0][0].winfo_y())
        self.app.mostrar_modulo('combinacion')
        t = self.app.espacios['combinacion'].actual
        t.transaccion(lambda: t.cargar({'a': a, 'b': [[12, 15, 18]], 'escalar': ''}))
        t.calcular()
        self.assertEqual(t.a.corchetes, ())  # Son tres vectores separados.
        texto = t.texto_paso.get('1.0', 'end')
        self.assertIn('v1 = [ 1   2   3 ]', texto)
        self.assertIn('V =\n⎡ 1   4   7 ⎤\n⎢ 2   5   8 ⎥\n⎣ 3   6   9 ⎦', texto)
        for _ in range(t.numero_pasos()):
            t.cambiar_paso(1)
        self.assertTrue(t.resultado.sistema.verificacion_particular)

    def test_sistemas_corchetes_gauss_jordan_e_interpretacion(self):
        self.app.mostrar_modulo('sistemas')
        self.app.editor.establecer_valores([[2, 1, -1, 8], [-3, -1, 2, -11], [-2, 1, 2, -3]])
        self.raiz.deiconify()
        self.raiz.update()
        self.assertEqual(len(self.app.editor.corchetes), 2)
        self.app.editor.boton_resolver.invoke()
        self.assertEqual(self.app.resultado.solucion_unica, [2, 3, -1])
        self.assertTrue(es_rref(self.app.resultado.rref))
        self.app._atajo_paso(1)
        self.assertEqual(self.app.cuaderno.paso_activo, 1)
        self.app.mostrar_etapa('interpretar')
        self.assertTrue(all(l.valida for l in self.app.resultado.verificacion))
        for modo in ('decimales', 'fracciones'):
            self.app.modo_visualizacion.set(modo)
            self.app.actualizar_visualizacion()
            self.assertEqual(self.app.resultado.solucion_unica, [2, 3, -1])

    def test_guiado_inicial_detalle_y_teclado(self):
        self.resolver()
        self.assertEqual(self.t.paso,0)
        self.assertEqual(self.t.notebook.index(self.t.notebook.select()),1)
        self.app._atajo_paso(1)
        self.assertEqual(self.t.paso,1)
        self.t.celda.current(1)
        self.t.celda.event_generate('<<ComboboxSelected>>')
        self.assertIn('= 64',self.t.detalle.get('1.0','end'))

    def test_invalida_y_deshace_sin_perder_evidencia(self):
        self.resolver()
        r=self.t.resultado
        self.t.a.variables[0][0].set('99')
        self.assertIn('Entrada modificada',self.t.estado.get())
        self.assertIs(r,self.t.resultado)
        self.t.deshacer()
        self.assertEqual(self.t.a.datos()[0][0],'1')
        self.assertIn('vigente',self.t.estado.get())

    def test_formatos_no_recalculan(self):
        self.resolver()
        with patch('axion_workbench.calcular_operacion',side_effect=AssertionError('recalculó')):
            self.app.modo_visualizacion.set('decimales')
            self.t.renderizar()
        self.assertEqual(self.t.resultado.salida[0][1],64)

    def test_borradores_por_operacion_y_modulo(self):
        self.t.a.variables[0][0].set('7/9')
        self.app.espacios['matrices'].seleccionar('matriz_suma')
        self.app.espacios['matrices'].actual.a.variables[0][0].set('8')
        self.app.mostrar_modulo('vectores')
        self.app.mostrar_modulo('matrices')
        self.app.espacios['matrices'].seleccionar('matriz_producto')
        self.assertEqual(self.t.a.datos()[0][0],'7/9')

    def test_pegado_atomico_y_deshacer(self):
        anterior=self.t.a.datos()
        with patch('axion_workbench.messagebox.askyesno',return_value=True):
            self.t.a.pegar('1\t2\n3\t1/0')
            self.assertEqual(self.t.a.datos(),anterior)
            self.t.a.pegar('1\t2\t3\n4\t5\t6')
        self.assertEqual(len(self.t.a.datos()[0]),3)
        self.t.deshacer()
        self.assertEqual(self.t.a.datos(),anterior)

    def test_dimension_interseccion_confirmacion(self):
        self.t.ejemplo()
        self.t.a.columnas.set('2')
        with patch('axion_workbench.messagebox.askyesno',return_value=False):
            self.t.a.redimensionar()
        self.assertEqual(self.t.a.datos()[0],['1','2','3'])
        self.t.a.columnas.set('4')
        self.t.a.redimensionar()
        self.assertEqual(self.t.a.datos()[0],['1','2','3',''])
        self.t.deshacer()
        self.assertEqual(self.t.a.datos()[0],['1','2','3'])
        self.assertEqual(self.t.a.columnas.get(),'3')

    def test_limpiar_y_rellenar_reversibles(self):
        self.t.rellenar()
        self.assertEqual(self.t.a.datos(),[['0','0'],['0','0']])
        self.t.deshacer()
        self.assertEqual(self.t.a.datos(),[['',''],['','']])
        self.resolver()
        self.t.limpiar()
        self.assertIsNotNone(self.t.resultado)
        self.t.deshacer()
        self.assertEqual(self.t.a.datos()[0],['1','2','3'])

    def test_error_no_publica_resultado_parcial(self):
        self.t.ejemplo()
        self.t.transaccion(lambda:self.t.b.establecer([[1,2],[3,4]]))
        self.t.calcular()
        self.assertIsNone(self.t.resultado)
        self.assertIn('3 columnas y B tiene 2 filas',self.t.estado.get())

    def test_dimensiones_pendientes_invalidan(self):
        self.resolver()
        self.t.a.columnas.set('7')
        self.assertIn('Entrada modificada',self.t.estado.get())
        self.t.calcular()
        self.assertIn('pulsa Aplicar',self.t.estado.get())

    def test_combinacion_tres_estados(self):
        self.app.mostrar_modulo('combinacion')
        t = self.app.espacios['combinacion'].actual
        for a,b,clase in [([[1,0,1],[0,1,1]],[[2,3,5]],'unica'),
                          ([[1,0,1],[0,1,1]],[[2,3,6]],'inconsistente'),
                          ([[1,2],[2,4]],[[3,6]],'infinitas')]:
            t.transaccion(lambda:t.cargar({'a':a,'b':b,'escalar':''}))
            t.calcular()
            self.assertEqual(t.resultado.sistema.clasificacion,clase)
            self.assertEqual(t.paso,0)

    def test_exportaciones_y_restaurar(self):
        self.resolver()
        for extension in ('txt','html'):
            ruta=Path(self.temp.name)/('informe.'+extension)
            with patch('axion_workbench.filedialog.asksaveasfilename',return_value=str(ruta)):
                self.t.guardar(extension)
            contenido=ruta.read_text(encoding='utf-8')
            self.assertIn('154',contenido)
            self.assertNotIn('https://',contenido)
        self.t.limpiar()
        self.t.restaurar()
        self.assertEqual(self.t.a.datos()[0],['1','2','3'])


if __name__ == '__main__':
    unittest.main()
