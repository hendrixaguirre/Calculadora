"""Editores y cuaderno de Programa 3: widgets ttk, borradores y evidencia exacta.

Los paneles de cada operación permanecen vivos al navegar. Una edición invalida
la evidencia visible; deshacer y restaurar actúan sobre instantáneas de entrada.
"""
from __future__ import annotations

import html
import tkinter as tk
from copy import deepcopy
from pathlib import Path
from tkinter import ttk, messagebox, filedialog

from axion_core import formatear_numero, texto_matriz
from axion_operaciones import (OPERACIONES, dimension, interpretar_tabla,
    calcular_operacion, texto_tabla, resumen_combinacion, resumen_propiedad,reporte_operacion)
from axion_ui import TemaAxion as T, AreaDesplazableAxion


def texto_lectura(parent):
    """Vista textual seleccionable, sin truncamiento y con desplazamiento local."""
    marco = ttk.Frame(parent)
    marco.pack(fill='both', expand=True, pady=8)
    texto = tk.Text(marco, wrap='word', height=10, width=40, bg=T.PAPEL,
                    fg=T.TINTA, font=(T.FUENTE_SANS, 12), padx=18, pady=14,
                    relief='flat', highlightthickness=1, highlightbackground=T.LINEA)
    barra = ttk.Scrollbar(marco, orient='vertical', command=texto.yview)
    texto.configure(yscrollcommand=barra.set)
    barra.pack(side='right', fill='y')
    texto.pack(fill='both', expand=True)
    return texto


def escribir(texto, contenido):
    texto.configure(state='normal')
    texto.delete('1.0', 'end')
    texto.insert('1.0', contenido)
    texto.tag_configure('titulo', font=(T.FUENTE_SANS, 16, 'bold'), foreground=T.TINTA, spacing3=10)
    texto.tag_add('titulo', '1.0', '1.end')
    texto.tag_configure('numero', font=(T.FUENTE_MONO, 15), spacing1=3, spacing3=3)
    for indice, linea in enumerate(contenido.splitlines(), 1):
        if linea.startswith('[ '):
            texto.tag_add('numero', f'{indice}.0', f'{indice}.end')
    texto.configure(state='disabled')


class EditorTabla(ttk.LabelFrame):
    """Tabla con tamaño explícito, etiquetas humanas y pegado TSV atómico."""
    def __init__(self, parent, taller, nombre, filas=2, columnas=2, vector=False, combinacion=False):
        super().__init__(parent, text=nombre, padding=10)
        self.taller, self.nombre = taller, nombre
        self.vector, self.combinacion = vector, combinacion
        self.filas = tk.StringVar(value=str(filas))
        self.columnas = tk.StringVar(value=str(columnas))
        self.variables, self.celdas = [], []
        barra = ttk.Frame(self)
        barra.pack(fill='x', pady=(0, 7))
        if not vector:
            ttk.Label(barra, text='Vectores k' if combinacion else 'Filas').pack(side='left')
            ttk.Spinbox(barra, from_=1, to=8, width=3, textvariable=self.filas).pack(side='left', padx=5)
        ttk.Label(barra, text='Dimensión n' if vector or combinacion else 'Columnas').pack(side='left')
        ttk.Spinbox(barra, from_=1, to=8, width=3, textvariable=self.columnas).pack(side='left', padx=5)
        ttk.Button(barra, text='Aplicar', command=self.redimensionar).pack(side='left', padx=5)
        ttk.Button(barra, text='Pegar tabla', command=self.pegar).pack(side='left')
        self.area = AreaDesplazableAxion(self, horizontal=True, vertical=True, height=170)
        self.area.canvas.configure(height=125, width=240)
        self.area.pack(fill='both', expand=True)
        self.establecer([['' for _ in range(columnas)] for _ in range(filas)])
        self.filas.trace_add('write', lambda *_: taller.cambio())
        self.columnas.trace_add('write', lambda *_: taller.cambio())

    def datos(self):
        return [[v.get() for v in fila] for fila in self.variables]

    def establecer(self, valores):
        for w in self.area.contenido.winfo_children():
            w.destroy()
        self.filas.set(str(len(valores)))
        self.columnas.set(str(len(valores[0])))
        self.variables, self.celdas = [], []
        for j in range(len(valores[0])):
            ttk.Label(self.area.contenido, text=f'{"Componente" if self.vector or self.combinacion else "Columna"} {j+1}').grid(row=0, column=j+1, padx=8)
        for i, fila in enumerate(valores):
            ttk.Label(self.area.contenido, text=f'v{i+1}' if self.combinacion else str(i+1)).grid(row=i+1, column=0, padx=6)
            variables, celdas = [], []
            for j, valor in enumerate(fila):
                var = tk.StringVar(value=str(valor))
                celda = ttk.Entry(self.area.contenido, textvariable=var, width=max(8, len(str(valor))+1),
                                  justify='center', font=(T.FUENTE_MONO, 13))
                celda.configure(validate='key', validatecommand=(self.register(lambda texto: len(texto) <= 64), '%P'),
                                invalidcommand=lambda: self.taller.estado.set('Máximo 64 caracteres por número; reduce la longitud.'))
                celda.grid(row=i+1, column=j+1, padx=4, pady=4, ipady=5)
                var.trace_add('write', lambda *_, v=var, c=celda: self.editar(v, c))
                celda.bind('<Control-v>', self.pegado_teclado)
                celda.bind('<Control-V>', self.pegado_teclado)
                celda.bind('<FocusIn>', lambda _e, c=celda: self.revelar(c))
                variables.append(var)
                celdas.append(celda)
            self.variables.append(variables)
            self.celdas.append(celdas)

    def revelar(self, celda):
        """Tab desplaza la tabla hasta la celda enfocada, sin cambiar el cursor."""
        self.update_idletasks()
        ancho = max(1, self.area.contenido.winfo_width())
        alto = max(1, self.area.contenido.winfo_height())
        x0, x1 = self.area.canvas.xview()
        y0, y1 = self.area.canvas.yview()
        x, y = celda.winfo_x()/ancho, celda.winfo_y()/alto
        if x < x0 or x + celda.winfo_width()/ancho > x1:
            self.area.canvas.xview_moveto(max(0, x - .02))
        if y < y0 or y + celda.winfo_height()/alto > y1:
            self.area.canvas.yview_moveto(max(0, y - .03))
        exterior = self.taller.scroll_definir
        posicion = celda.winfo_rooty() - exterior.canvas.winfo_rooty()
        if posicion < 0 or posicion + celda.winfo_height() > exterior.canvas.winfo_height():
            destino = (self.winfo_rooty() - exterior.contenido.winfo_rooty()) / max(1, exterior.contenido.winfo_height())
            exterior.canvas.yview_moveto(destino)

    def editar(self, variable, celda):
        celda.configure(width=max(8, min(65, len(variable.get())+1)))
        self.taller.cambio()

    def redimensionar(self):
        try:
            m, n = dimension(self.filas.get()), dimension(self.columnas.get())
        except ValueError as error:
            self.taller.error(str(error))
            return
        anterior = self.datos()
        descartados = any(valor.strip() for i, fila in enumerate(anterior) for j, valor in enumerate(fila) if i >= m or j >= n)
        if descartados and not messagebox.askyesno('Reducir dimensiones',
                f'{self.nombre}: se descartarán celdas no vacías. ¿Continuar?', parent=self):
            self.filas.set(str(len(anterior)))
            self.columnas.set(str(len(anterior[0])))
            return
        nuevo = [[anterior[i][j] if i < len(anterior) and j < len(anterior[0]) else '' for j in range(n)] for i in range(m)]
        self.taller.transaccion(lambda: self.establecer(nuevo))

    def pegado_teclado(self, _event=None):
        try:
            texto = self.clipboard_get()
        except tk.TclError:
            return 'break'
        if '\t' in texto or '\n' in texto or '\r' in texto:
            self.pegar(texto)
            return 'break'
        # Un escalar conserva el pegado normal de ttk.Entry.
        return None

    def pegar(self, texto=None):
        try:
            texto = self.clipboard_get() if texto is None else texto
            valores = interpretar_tabla(texto, self.nombre)
            if self.vector and len(valores) != 1:
                raise ValueError(f'{self.nombre}: pega una sola fila de componentes')
        except (ValueError, tk.TclError) as error:
            self.taller.error(str(error))
            return
        vista = '\n'.join('\t'.join(fila) for fila in valores)
        if messagebox.askyesno('Previsualizar pegado',
                f'{self.nombre}: {len(valores)}×{len(valores[0])}\n'
                'Formato: Tab = columnas; salto = filas; punto/coma = decimal.\n'
                f'{vista}\n\n¿Reemplazar esta tabla completa? Deshacer recupera la anterior.', parent=self):
            self.taller.transaccion(lambda: self.establecer(valores))


class TallerOperacion(ttk.Frame):
    """Controlador de una operación: cálculo explícito, versiones y navegación."""

    def __init__(self, parent, app, operacion):
        super().__init__(parent, padding=(18, 8))

        self.app, self.operacion = app, operacion
        self.resultado = None
        self.resuelta = None
        self.paso = 0
        self.suspendido = True
        self.deshacer_pila = []
        self.anterior = None

        self.escalar = tk.StringVar(value='')
        self.estado = tk.StringVar(
            value='Define todos los valores. Las celdas vacías no son cero.'
        )

        self.notebook = ttk.Notebook(self)

        ttk.Label(
            self,
            textvariable=self.estado,
            wraplength=900,
            style='Nota.Axion.TLabel'
        ).pack(
            side='bottom',
            fill='x',
            pady=(8, 0)
        )

        self.notebook.pack(
            fill='both',
            expand=True
        )

        self.definir = ttk.Frame(
            self.notebook,
            padding=12
        )

        self.scroll_definir = AreaDesplazableAxion(
            self.definir,
            background=T.LIENZO
        )

        self.scroll_definir.pack(
            fill='both',
            expand=True
        )

        self.contenido_definir = self.scroll_definir.contenido

        self.procedimiento = ttk.Frame(
            self.notebook,
            padding=12
        )

        self.final = ttk.Frame(
            self.notebook,
            padding=12
        )

        for pagina, nombre in (
            (self.definir, '1. Definir'),
            (self.procedimiento, '2. Procedimiento'),
            (self.final, '3. Resultado y comprobación')
        ):
            self.notebook.add(
                pagina,
                text=nombre
            )

        self.notebook.tab(
            1,
            state='disabled'
        )

        self.notebook.tab(
            2,
            state='disabled'
        )

        ttk.Label(
            self.contenido_definir,
            text=OPERACIONES[operacion],
            style='Titulo.Axion.TLabel'
        ).pack(
            anchor='w',
            pady=(0, 5)
        )

        ayuda = (
            'Introduce un vector vᵢ por fila. AXION lo colocará como columna de V para resolver Vc=b.'
            if operacion == 'combinacion'
            else
            'Racionales exactos · 1–8 por eje · enteros, decimales o fracciones.'
        )

        ttk.Label(
            self.contenido_definir,
            text=ayuda,
            wraplength=740
        ).pack(
            anchor='w',
            pady=(0, 8)
        )

        self.forma = tk.StringVar()

        ttk.Label(
            self.contenido_definir,
            textvariable=self.forma,
            style='Nota.Axion.TLabel',
            wraplength=750
        ).pack(
            anchor='w',
            pady=(0, 8)
        )

        self.editores = ttk.Frame(
            self.contenido_definir
        )

        self.editores.pack(
            fill='both',
            expand=True
        )

        self.selector_editor = ttk.Frame(
            self.contenido_definir
        )

        self.editor_visible = tk.StringVar(
            value='a'
        )

        for clave, etiqueta in [
            ('a', 'Editar A / vectores dados'),
            ('b', 'Editar B / objetivo')
        ]:
            ttk.Radiobutton(
                self.selector_editor,
                text=etiqueta,
                variable=self.editor_visible,
                value=clave,
                command=self.mostrar_editor
            ).pack(
                side='left',
                padx=(0, 16)
            )

        self.editores.columnconfigure(
            0,
            weight=1
        )

        self.editores.rowconfigure(
            0,
            weight=1
        )

        # =====================================================
        # IDENTIFICAR EL TIPO DE OPERACIÓN
        # =====================================================

        es_vector = operacion.startswith('vector')

        combinacion = (
            operacion == 'combinacion'
        )

        propiedad_distributiva = (
            operacion == 'propiedad_distributiva'
        )

        propiedad_escalar = (
            operacion == 'propiedad_escalar'
        )

        # Las propiedades tienen su propio tratamiento.
        # No debemos considerar propiedad_escalar como una
        # operación normal que termina en "escalar".

        escalar = (
            operacion.endswith('escalar')
            and not propiedad_escalar
        )

        # =====================================================
        # EDITOR A
        # =====================================================

        if propiedad_distributiva or propiedad_escalar:

            nombre_a = 'Matriz A'
            filas_a = 2
            columnas_a = 2
            vector_a = False
            combinacion_a = False

        else:

            nombre_a = (
                'Vectores v₁,…,vₖ'
                if combinacion
                else
                'Vector u'
                if es_vector
                else
                'Matriz A'
            )

            filas_a = (
                1
                if es_vector
                else
                2
            )

            columnas_a = (
                3
                if es_vector or combinacion
                else
                2
            )

            vector_a = es_vector
            combinacion_a = combinacion

        self.a = EditorTabla(
            self.editores,
            self,
            nombre_a,
            filas=filas_a,
            columnas=columnas_a,
            vector=vector_a,
            combinacion=combinacion_a
        )

        self.a.grid(
            row=0,
            column=0,
            sticky='nsew',
            pady=3
        )

        # =====================================================
        # EDITOR B
        # =====================================================

        self.b = None

        # -----------------------------------------------------
        # PROPIEDAD DISTRIBUTIVA
        # A(u + v) = Au + Av
        # -----------------------------------------------------

        if propiedad_distributiva:

            self.b = EditorTabla(
                self.editores,
                self,
                'Vectores u y v',
                filas=2,
                columnas=2,
                vector=False,
                combinacion=False
            )

            self.b.grid(
                row=0,
                column=1,
                sticky='nsew',
                padx=(8, 0),
                pady=3
            )

            self.editores.columnconfigure(
                1,
                weight=1
            )

        # -----------------------------------------------------
        # PROPIEDAD DEL ESCALAR
        # A(cu) = c(Au)
        # -----------------------------------------------------

        elif propiedad_escalar:

            self.b = EditorTabla(
                self.editores,
                self,
                'Vector u',
                filas=1,
                columnas=2,
                vector=True,
                combinacion=False
            )

            self.b.grid(
                row=1,
                column=0,
                sticky='nsew',
                pady=3
            )

            self.editores.rowconfigure(
                1,
                weight=1
            )

            # Escalar c
            fila = ttk.Frame(
                self.contenido_definir
            )

            fila.pack(
                fill='x',
                pady=8
            )

            ttk.Label(
                fila,
                text='Escalar c'
            ).pack(
                side='left',
                padx=(0, 10)
            )

            ttk.Entry(
                fila,
                textvariable=self.escalar,
                width=24,
                font=(T.FUENTE_MONO, 13)
            ).pack(
                side='left'
            )

        # -----------------------------------------------------
        # OPERACIONES NORMALES CON SEGUNDO OPERANDO
        # -----------------------------------------------------

        elif not escalar:

            self.b = EditorTabla(
                self.editores,
                self,
                (
                    'Objetivo b'
                    if combinacion
                    else
                    'Vector v'
                    if es_vector
                    else
                    'Matriz B'
                ),
                filas=(
                    1
                    if es_vector or combinacion
                    else
                    2
                ),
                columnas=(
                    3
                    if es_vector or combinacion
                    else
                    2
                ),
                vector=es_vector or combinacion
            )

            self.b.grid(
                row=1,
                column=0,
                sticky='nsew',
                pady=3
            )

            self.editores.rowconfigure(
                1,
                weight=1
            )

        # -----------------------------------------------------
        # OPERACIONES NORMALES CON ESCALAR
        # -----------------------------------------------------

        else:

            fila = ttk.Frame(
                self.contenido_definir
            )

            fila.pack(
                fill='x',
                pady=8
            )

            ttk.Label(
                fila,
                text='Escalar λ'
            ).pack(
                side='left',
                padx=(0, 10)
            )

            ttk.Entry(
                fila,
                textvariable=self.escalar,
                width=24,
                font=(T.FUENTE_MONO, 13)
            ).pack(
                side='left'
            )

        # =====================================================
        # EVENTOS Y BOTONES
        # =====================================================

        self.escalar.trace_add(
            'write',
            lambda *_: self.cambio()
        )

        acciones = ttk.Frame(
            self.contenido_definir
        )

        acciones.pack(
            fill='x',
            pady=8,
            before=self.editores
        )

        ttk.Button(
            acciones,
            text=OPERACIONES[operacion],
            style='Accion.Axion.TButton',
            command=self.calcular
        ).grid(
            row=0,
            column=0,
            sticky='w',
            pady=(0, 5)
        )

        ttk.Button(
            acciones,
            text='Ejemplo',
            command=self.ejemplo
        ).grid(
            row=0,
            column=1,
            padx=7
        )

        editar = ttk.Menubutton(
            acciones,
            text='Editar entrada'
        )

        menu = tk.Menu(
            editar,
            tearoff=False,
            font=(T.FUENTE_SANS, 11)
        )

        menu.add_command(
            label='Limpiar entrada',
            command=self.limpiar
        )

        menu.add_command(
            label='Rellenar vacíos con 0',
            command=self.rellenar
        )

        editar.configure(
            menu=menu
        )

        editar.grid(
            row=0,
            column=2,
            padx=7
        )

        self.boton_deshacer = ttk.Button(
            acciones,
            text='Deshacer edición',
            command=self.deshacer,
            state='disabled'
        )

        self.boton_deshacer.grid(
            row=0,
            column=3,
            padx=7
        )

        # =====================================================
        # PROCEDIMIENTO
        # =====================================================

        nav = ttk.Frame(
            self.procedimiento
        )

        nav.pack(
            fill='x'
        )

        self.atras = ttk.Button(
            nav,
            text='Anterior',
            command=lambda: self.cambiar_paso(-1)
        )

        self.atras.pack(
            side='left'
        )

        self.indicador = ttk.Label(
            nav,
            text='Paso 1'
        )

        self.indicador.pack(
            side='left',
            padx=16
        )

        self.adelante = ttk.Button(
            nav,
            text='Siguiente',
            command=lambda: self.cambiar_paso(1)
        )

        self.adelante.pack(
            side='left'
        )

        ttk.Button(
            nav,
            text='Ir al resultado',
            command=lambda: self.notebook.select(2)
        ).pack(
            side='right'
        )

        self.texto_paso = texto_lectura(
            self.procedimiento
        )

        self.texto_resultado = texto_lectura(
            self.final
        )

        self.selector = ttk.Frame(
            self.final
        )

        self.selector.pack(
            fill='x'
        )

        ttk.Label(
            self.selector,
            text='Inspeccionar celda / componente:'
        ).pack(
            side='left'
        )

        self.celda = ttk.Combobox(
            self.selector,
            state='readonly',
            width=12
        )

        self.celda.pack(
            side='left',
            padx=8
        )

        self.celda.bind(
            '<<ComboboxSelected>>',
            lambda _e: self.detalle_seleccionado()
        )

        self.detalle = texto_lectura(
            self.final
        )

        self.detalle.configure(
            height=4
        )

        exportar = ttk.Frame(
            self.final
        )

        exportar.pack(
            fill='x'
        )

        for etiqueta, comando in [
            ('Copiar resultado', self.copiar),
            ('Guardar TXT', lambda: self.guardar('txt')),
            ('Guardar HTML', lambda: self.guardar('html')),
            ('Editar una copia', self.restaurar)
        ]:
            ttk.Button(
                exportar,
                text=etiqueta,
                command=comando
            ).pack(
                side='left',
                padx=(0, 8)
            )

        # =====================================================
        # DISTRIBUCIÓN FINAL
        # =====================================================

        for widget in self.final.winfo_children():
            widget.pack_forget()

        self.final.columnconfigure(
            0,
            weight=1
        )

        self.final.rowconfigure(
            0,
            weight=1
        )

        self.final.rowconfigure(
            2,
            weight=1
        )

        self.texto_resultado.configure(
            height=5
        )

        self.texto_resultado.master.grid(
            row=0,
            column=0,
            sticky='nsew',
            pady=5
        )

        self.selector.grid(
            row=1,
            column=0,
            sticky='ew'
        )

        self.detalle.master.grid(
            row=2,
            column=0,
            sticky='nsew',
            pady=5
        )

        exportar.grid(
            row=3,
            column=0,
            sticky='ew',
            pady=5
        )

        self.suspendido = False

        self.anterior = self.instantanea()

        self.actualizar_forma()

        self.editores.bind(
            '<Configure>',
            self.distribuir
        )

        self._ancha = None

    def distribuir(self, event):
        ancha = event.width >= 1030
        if self.b is None or ancha == self._ancha:
            return
        self._ancha = ancha
        self.editores.columnconfigure(1, weight=1 if ancha else 0)
        self.editores.rowconfigure(1, weight=0)
        if ancha:
            self.selector_editor.pack_forget()
            self.a.grid(row=0, column=0, sticky='nsew')
            self.b.grid(row=0, column=1, sticky='nsew', padx=(8, 0), pady=3)
        else:
            self.selector_editor.pack(fill='x', pady=4, before=self.editores)
            self.mostrar_editor()

    def mostrar_editor(self):
        """En ventana estrecha cambia de operando sin reconstruirlo ni borrar foco/datos."""
        if self.b is not None and not self._ancha:
            self.a.grid_remove()
            self.b.grid_remove()
            editor = self.a if self.editor_visible.get() == 'a' else self.b
            editor.grid(row=0, column=0, sticky='nsew', padx=0, pady=3)

    def instantanea(self):
        return {'a': self.a.datos(), 'b': self.b.datos() if self.b else None,
                'escalar': self.escalar.get(),
                'dim_a': (self.a.filas.get(), self.a.columnas.get()),
                'dim_b': (self.b.filas.get(), self.b.columnas.get()) if self.b else None}

    def cambio(self):
        if self.suspendido:
            return
        nueva = self.instantanea()
        # Escribir un tamaño pendiente invalida, pero aplicar el tamaño será
        # una única acción de deshacer que recupera la forma anterior real.
        if self.anterior is not None and any(nueva[k] != self.anterior[k] for k in ('a', 'b', 'escalar')):
            self.deshacer_pila.append(deepcopy(self.anterior))
            self.deshacer_pila = self.deshacer_pila[-50:]
        self.anterior = deepcopy(nueva)
        self.anterior['dim_a'] = (str(len(nueva['a'])), str(len(nueva['a'][0])))
        if nueva['b'] is not None:
            self.anterior['dim_b'] = (str(len(nueva['b'])), str(len(nueva['b'][0])))
        self.boton_deshacer.configure(state='normal' if self.deshacer_pila else 'disabled')
        self.estado.set('Entrada modificada: vuelve a calcular. Se conserva el resultado anterior.' if self.resultado and nueva != self.resuelta
                        else 'Resultado vigente · cálculo exacto.' if self.resultado else 'Editando. Completa todos los valores y calcula.')
        self.actualizar_forma()

    def actualizar_forma(self):
        a = f'{self.a.filas.get()}×{self.a.columnas.get()}'
        b = f'{self.b.filas.get()}×{self.b.columnas.get()}' if self.b else ''
        if self.operacion == 'matriz_producto':
            self.forma.set(f'A: {a} · B: {b} → C tendría {self.a.filas.get()}×{self.b.columnas.get()} si son compatibles. '
                           'Se requiere: columnas de A = filas de B.')
        elif self.operacion == 'combinacion':
            self.forma.set(f'n = {self.a.columnas.get()}, k = {self.a.filas.get()}; V: {self.a.columnas.get()}×{self.a.filas.get()}. '
                           'n y k son independientes. Objetivo b: una fila de n componentes.')
        else:
            self.forma.set(f'Entrada A / u: {a}' + (f' · B / v: {b}. Suma y resta requieren formas iguales.' if self.b else ' · λ multiplica todas las entradas.'))

    def transaccion(self, accion):
        """Una operación masiva equivale a una sola acción de deshacer."""
        self.suspendido = True
        try:
            accion()
        finally:
            self.suspendido = False
        self.cambio()

    def cargar(self, estado):
        self.a.establecer(estado['a'])
        if self.b:
            self.b.establecer(estado['b'])
        self.escalar.set(estado.get('escalar') or '')
        if 'dim_a' in estado:
            self.a.filas.set(estado['dim_a'][0])
            self.a.columnas.set(estado['dim_a'][1])
        if self.b and estado.get('dim_b'):
            self.b.filas.set(estado['dim_b'][0])
            self.b.columnas.set(estado['dim_b'][1])

    def deshacer(self):
        if not self.deshacer_pila:
            return 'break'
        anterior = self.deshacer_pila.pop()
        self.suspendido = True
        self.cargar(anterior)
        self.suspendido = False
        self.anterior = self.instantanea()
        self.cambio()
        return 'break'

    def error(self, mensaje):
        self.estado.set('Error: ' + mensaje + (' · Resultado anterior conservado.' if self.resultado else ''))
        self.notebook.select(0)

    def calcular(self):
        try:
            for editor in (self.a, self.b):
                if editor:
                    m, n = dimension(editor.filas.get()), dimension(editor.columnas.get())
                    if (m, n) != (len(editor.variables), len(editor.variables[0])):
                        raise ValueError(f'{editor.nombre}: pulsa Aplicar para confirmar las nuevas dimensiones')
            r = calcular_operacion(self.operacion, self.a.datos(), self.b.datos() if self.b else None,
                                   self.escalar.get() if self.operacion.endswith('escalar') or self.operacion == 'propiedad_escalar' else None)
        except ValueError as error:
            self.error(str(error))
            return
        self.resultado, self.resuelta, self.paso = r, deepcopy(self.instantanea()), 0
        self.notebook.tab(1, state='normal')
        self.notebook.tab(2, state='normal')
        self.renderizar()
        self.estado.set('Resultado vigente · cálculo exacto.' + (' Comprobación de representación incluida.' if r.sistema else ''))
        if not self.app.historial.add_operacion(r):
            self.estado.set(self.app.historial.ultimo_error + ' Resultado conservado en memoria.')
        self.notebook.select(1 if self.app.modo_uso.get() == 'guiado' else 2)

    def numero_pasos(self):
        r = self.resultado
        return 1 + len(r.sistema.pasos) if r.sistema else 1 + len(r.salida)*len(r.salida[0])

    def cambiar_paso(self, delta):
        if self.resultado:
            self.paso = max(0, min(self.numero_pasos()-1, self.paso+delta))
            self.renderizar_paso()

    def renderizar_paso(self):
        r, modo = self.resultado, self.app.modo_visualizacion.get()
        n = self.numero_pasos()
        self.indicador.configure(text=f'Paso {self.paso+1} de {n}')
        self.atras.configure(state='disabled' if self.paso == 0 else 'normal')
        self.adelante.configure(state='disabled' if self.paso == n-1 else 'normal')
        if self.paso == 0:
            contenido = f'Estado inicial · {OPERACIONES[self.operacion]}\n\nA / vectores dados:\n{texto_tabla(r.a, modo)}'
            if r.b is not None:
                contenido += f'\n\nB / objetivo b:\n{texto_tabla(r.b, modo)}'
            if r.escalar is not None:
                contenido += f'\n\nλ = {formatear_numero(r.escalar, modo)}'
            if r.sistema:
                contenido += '\n\nV = [v₁ v₂ … vₖ]: los vectores pasan de las filas del editor a COLUMNAS.\nVc=b; cada incógnita cᵢ multiplica vᵢ.\n[V|b]:\n' + texto_matriz(r.sistema.original, modo)
            elif self.operacion == 'matriz_producto':
                contenido += f'\n\nA {len(r.a)}×{len(r.a[0])}, B {len(r.b)}×{len(r.b[0])}; C tendrá {len(r.salida)}×{len(r.salida[0])} celdas.\nPara cada c[i,j], r recorre la fila i de A y la columna j de B.'
        elif r.sistema:
            p = r.sistema.pasos[self.paso-1]
            contenido = (f'{p.titulo}\n{p.notacion_operacion}\n\n{p.explicacion_breve}\n{p.explicacion_formal}\n\n'
                         f'Antes:\n{texto_matriz(p.matriz_antes, modo)}\n\nDespués:\n{texto_matriz(p.matriz_despues, modo)}\n\n'
                         'Las columnas de incógnitas corresponden a c₁,…,cₖ; la última columna es b.')
        else:
            i, j = divmod(self.paso-1, len(r.salida[0]))
            contenido = self.texto_detalle(i, j)
        escribir(self.texto_paso, contenido)

    def texto_detalle(self, i, j):
        r, modo = self.resultado, self.app.modo_visualizacion.get()
        texto = r.detalle(i, j, modo)
        if self.operacion == 'matriz_producto':
            texto += f'\n\nFILA {i+1} seleccionada de A: ' + texto_tabla([r.a[i]], modo)
            texto += f'\nCOLUMNA {j+1} seleccionada de B: ' + texto_tabla([[fila[j] for fila in r.b]], modo)
        return texto

    def renderizar(self):
        if not self.resultado:
            return
        r, modo = self.resultado, self.app.modo_visualizacion.get()
        
        if r.sistema:
            escribir(self.texto_resultado, resumen_combinacion(r.sistema, modo))
            self.selector.grid_remove()
            self.detalle.master.grid_remove()
            self.final.rowconfigure(2, weight=0)
        else:
            escribir(self.texto_resultado, f'Cálculo exacto · resultado {len(r.salida)}×{len(r.salida[0])}\n\n' + texto_tabla(r.salida, modo)
                     + '\n\nSelecciona una celda para ver sus operandos y desarrollo.\nEn Decimales, ≈ indica una presentación aproximada; el valor exacto se conserva.')
            self.celda.configure(values=[f'[{i+1},{j+1}]' for i in range(len(r.salida)) for j in range(len(r.salida[0]))])
            if self.celda.current() < 0:
                self.celda.current(0)
            self.detalle_seleccionado()
        self.renderizar_paso()

    def detalle_seleccionado(self):
        if self.resultado and self.resultado.salida:
            i, j = divmod(max(0, self.celda.current()), len(self.resultado.salida[0]))
            escribir(self.detalle, self.texto_detalle(i, j))

    def ejemplo(self):
        op = self.operacion
        if op == 'combinacion':
            a, b, escalar = [[1, 0, 1], [0, 1, 1]], [[2, 3, 5]], ''
        elif op.startswith('vector'):
            a, b, escalar = [['1/2', -2, 3]], [['3/2', 5, -1]], '-2'
        elif op == 'matriz_producto':
            a, b, escalar = [[1, 2, 3], [4, 5, 6]], [[7, 8], [9, 10], [11, 12]], ''
        else:
            a, b, escalar = [[1, -2], [3, 0]], [[4, 5], [-1, 2]], '-2'
        self.transaccion(lambda: self.cargar({'a': a, 'b': b, 'escalar': escalar}))
        self.notebook.select(0)

    def limpiar(self):
        def accion():
            for editor in (self.a, self.b):
                if editor:
                    for fila in editor.variables:
                        for v in fila:
                            v.set('')
            self.escalar.set('')
        self.transaccion(accion)
        self.notebook.select(0)

    def rellenar(self):
        def accion():
            for editor in (self.a, self.b):
                if editor:
                    for fila in editor.variables:
                        for v in fila:
                            if not v.get().strip():
                                v.set('0')
        self.transaccion(accion)

    def restaurar(self):
        if self.resuelta:
            self.transaccion(lambda: self.cargar(self.resuelta))
            self.notebook.select(0)

    def copiar(self):
        if self.resultado:
            self.clipboard_clear()
            self.clipboard_append(reporte_operacion(self.resultado, self.app.modo_visualizacion.get()))

    def guardar(self, extension):
        if not self.resultado:
            return
        ruta = filedialog.asksaveasfilename(parent=self, defaultextension='.'+extension,
                                           filetypes=[(extension.upper(), '*.'+extension)])
        if not ruta:
            return
        contenido = reporte_operacion(self.resultado, self.app.modo_visualizacion.get())
        if extension == 'html':
            contenido = ('<!doctype html><html lang="es"><meta charset="utf-8">'
                         '<title>AXION — Programa 3</title><style>body{max-width:960px;margin:40px auto;'
                         'font:18px system-ui;color:#172033}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style>'
                         '<h1>AXION</h1><pre>' + html.escape(contenido) + '</pre></html>')
        try:
            Path(ruta).write_text(contenido, encoding='utf-8')
        except OSError as error:
            self.estado.set(f'No se pudo guardar: {error}. Resultado conservado en memoria.')


class EspacioOperaciones(ttk.Frame):
    """Cada operación conserva tanto su borrador como su cuaderno resuelto."""
    def __init__(self, parent, app, claves):
        super().__init__(parent)
        self.app, self.claves, self.talleres = app, claves, {}
        barra = ttk.Frame(self, padding=(20, 7))
        barra.pack(fill='x')
        ttk.Label(barra, text='Operación').pack(side='left', padx=(0, 10))
        self.operacion = ttk.Combobox(barra, state='readonly', values=[OPERACIONES[k] for k in claves], width=32)
        self.operacion.pack(side='left')
        self.operacion.current(0)
        self.operacion.bind('<<ComboboxSelected>>', lambda _e: self.seleccionar())
        for texto, variable, valores in [('Vista', app.modo_visualizacion, ['fracciones', 'decimales']),
                                         ('Modo', app.modo_uso, ['guiado', 'rapido'])]:
            ttk.Label(barra, text=texto).pack(side='left', padx=(18, 5))
            combo = ttk.Combobox(barra, state='readonly', width=12, textvariable=variable, values=valores)
            combo.pack(side='left')
            combo.bind('<<ComboboxSelected>>', lambda _e: self.actual.renderizar())
        self.seleccionar()

    def seleccionar(self, clave=None):
        clave = clave or self.claves[self.operacion.current()]
        self.operacion.current(self.claves.index(clave))
        for taller in self.talleres.values():
            taller.pack_forget()
        if clave not in self.talleres:
            self.talleres[clave] = TallerOperacion(self, self.app, clave)
        self.actual = self.talleres[clave]
        self.actual.pack(fill='both', expand=True)
        self.actual.renderizar()
