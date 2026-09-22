"""Extensión de AXION existente: cuatro espacios y el cuaderno de sistemas previo."""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox

from axion_ui import AplicacionAxion, TemaAxion as T
from axion_workbench import EspacioOperaciones
from axion_operaciones import OPERACIONES


class AplicacionPrograma3(AplicacionAxion):
    """Conserva la API y el editor de Programa 2; añade navegación por módulos."""
    def __init__(self, raiz, almacen_historial=None):
        self.modulo = 'sistemas'
        self.espacios = {}
        super().__init__(raiz, almacen_historial)
        raiz.title('AXION | Programa 3 · Álgebra lineal')
        estilo = ttk.Style(raiz)
        estilo.theme_use('clam')
        estilo.configure('.', font=(T.FUENTE_SANS, 11), background=T.LIENZO, foreground=T.TINTA)
        estilo.configure('TButton', padding=(10, 6))
        estilo.map('TButton', background=[('pressed', '#D6E1F4'), ('active', '#EAF0F7')],
                   relief=[('pressed', 'sunken'), ('!pressed', 'raised')])
        estilo.configure('TEntry', fieldbackground=T.PAPEL, foreground=T.TINTA)
        estilo.map('TEntry', bordercolor=[('focus', T.INDIGO), ('invalid', T.ROJO)])
        estilo.configure('TNotebook.Tab', padding=(14, 8))
        estilo.map('TNotebook.Tab', background=[('selected', T.PAPEL)], foreground=[('selected', T.INDIGO)])
        estilo.configure('Titulo.Axion.TLabel', font=(T.FUENTE_SANS, 24, 'bold'))
        estilo.configure('Nota.Axion.TLabel', foreground=T.AMBAR)
        estilo.configure('Accion.Axion.TButton', background=T.INDIGO, foreground='white', padding=(14, 9))
        estilo.map('Accion.Axion.TButton', background=[('pressed', '#163A9D'), ('active', '#245BDD')])
        # Insertar navegación bajo la cabecera preserva todos los widgets del sistema.
        self.widgets_sistema = []
        for widget in raiz.grid_slaves():
            row = int(widget.grid_info()['row'])
            if row > 0:
                widget.grid_configure(row=row+1)
                self.widgets_sistema.append(widget)
        raiz.grid_rowconfigure(2, weight=0)
        raiz.grid_rowconfigure(3, weight=1)
        self.navegacion = ttk.Frame(raiz, padding=(20, 6))
        self.navegacion.grid(row=1, column=0, sticky='ew')
        self.selector_modulo = tk.StringVar(value='sistemas')
        for clave, etiqueta in [('vectores', 'Vectores'), ('matrices', 'Matrices'),
                                ('combinacion', 'Combinación lineal'), ('sistemas', 'Sistemas Ax=b')]:
            ttk.Radiobutton(self.navegacion, text=etiqueta, value=clave, variable=self.selector_modulo,
                            command=lambda k=clave: self.mostrar_modulo(k)).pack(side='left', padx=(0, 24))
        self.espacios['vectores'] = EspacioOperaciones(raiz, self, ['vector_suma', 'vector_resta', 'vector_escalar'])
        self.espacios['matrices'] = EspacioOperaciones(raiz, self, ['matriz_producto', 'matriz_suma', 'matriz_resta', 'matriz_escalar'])
        self.espacios['combinacion'] = EspacioOperaciones(raiz, self, ['combinacion'])
        raiz.bind('<Control-Return>', lambda _e: (self.resolver(), 'break')[1])
        raiz.bind('<Control-z>', lambda _e: self.deshacer_actual())
        raiz.bind('<Control-Z>', lambda _e: self.deshacer_actual())
        raiz.bind('<Control-s>', lambda _e: self.guardar_actual())
        self.etiqueta_motor.configure(text='PROGRAMA 3 · ARITMÉTICA EXACTA')
        self.mostrar_modulo('matrices')

    def mostrar_modulo(self, clave):
        self.modulo = clave
        self.selector_modulo.set(clave)
        for panel in self.espacios.values():
            panel.grid_remove()
        for w in self.widgets_sistema:
            w.grid() if clave == 'sistemas' else w.grid_remove()
        if clave != 'sistemas':
            self.espacios[clave].grid(row=2, column=0, rowspan=3, sticky='nsew')
            self.espacios[clave].actual.renderizar()

    def resolver(self):
        if self.modulo == 'sistemas':
            return super().resolver()
        return self.espacios[self.modulo].actual.calcular()

    def deshacer_actual(self):
        if self.modulo == 'sistemas':
            self.editor.deshacer()
        else:
            self.espacios[self.modulo].actual.deshacer()
        return 'break'

    def guardar_actual(self):
        if self.modulo == 'sistemas':
            if self.resultado:
                self.cuaderno.guardar_reporte()
        else:
            self.espacios[self.modulo].actual.guardar('txt')
        return 'break'

    def nuevo_ejercicio(self):
        if self.modulo == 'sistemas':
            return super().nuevo_ejercicio()
        self.espacios[self.modulo].actual.limpiar()

    def _atajo_paso(self, delta):
        if self.modulo == 'sistemas':
            return super()._atajo_paso(delta)
        t = self.espacios[self.modulo].actual
        if t.notebook.index(t.notebook.select()) == 1:
            t.cambiar_paso(delta)
        return 'break'

    def _distribucion_adaptable(self, event):
        if self.modulo == 'sistemas':
            super()._distribucion_adaptable(event)
        elif event.widget is self.raiz:
            if event.width < 1100:
                self.etiqueta_motor.pack_forget()
                self.separador_motor.pack_forget()
            elif not self.etiqueta_motor.winfo_manager():
                self.separador_motor.pack(side='left', padx=10)
                self.etiqueta_motor.pack(side='left')

    def mostrar_historial(self):
        dialogo = tk.Toplevel(self.raiz)
        dialogo.title('AXION · Historial local')
        dialogo.geometry('760x440')
        dialogo.transient(self.raiz)
        foco = self.raiz.focus_get()
        def cerrar():
            dialogo.destroy()
            if foco and foco.winfo_exists():
                foco.focus_set()
        dialogo.bind('<Escape>', lambda _e: cerrar())
        ttk.Label(dialogo, text='Ejercicios guardados · hasta 50', style='Titulo.Axion.TLabel').pack(anchor='w', padx=20, pady=15)
        ttk.Label(dialogo, text='Editar una copia recupera los operandos exactos. Calcula para obtener una nueva evidencia.').pack(anchor='w', padx=20)
        marco = ttk.Frame(dialogo, padding=20)
        marco.pack(fill='both', expand=True)
        lista = tk.Listbox(marco, font=(T.FUENTE_SANS, 11), activestyle='dotbox')
        scroll = ttk.Scrollbar(marco, command=lista.yview)
        lista.configure(yscrollcommand=scroll.set)
        scroll.pack(side='right', fill='y')
        lista.pack(fill='both', expand=True)
        registros = self.historial.entradas[:]
        for registro in registros:
            etiqueta = OPERACIONES[registro['operation']] if registro.get('kind') == 'operacion' else 'Sistema Ax=b · '+registro['classification']
            lista.insert('end', registro['created_at']+' · '+etiqueta)
        def abrir():
            if not lista.curselection():
                return
            r = registros[lista.curselection()[0]]
            if r.get('kind') == 'operacion':
                clave = 'vectores' if r['operation'].startswith('vector') else 'combinacion' if r['operation'] == 'combinacion' else 'matrices'
                self.mostrar_modulo(clave)
                self.espacios[clave].seleccionar(r['operation'])
                t = self.espacios[clave].actual
                t.transaccion(lambda: t.cargar({'a': r['a'], 'b': r['b'], 'escalar': r['scalar']}))
                t.notebook.select(0)
            else:
                self.mostrar_modulo('sistemas')
                self.editor.establecer_valores(r['matrix'])
                self.editor.metodo.set('Gauss-Jordan' if r['method'] == 'gauss-jordan' else 'Eliminación de Gauss')
                self.mostrar_etapa('definir')
            cerrar()
        lista.bind('<Return>', lambda _e: abrir())
        lista.bind('<Double-Button-1>', lambda _e: abrir())
        ttk.Button(dialogo, text='Editar una copia', command=abrir,
                   state='normal' if registros else 'disabled').pack(side='left', padx=20, pady=15)
        ttk.Button(dialogo, text='Cerrar', command=cerrar).pack(side='right', padx=20, pady=15)
        lista.focus_set()

    def mostrar_ayuda(self):
        if self.modulo == 'sistemas':
            return super().mostrar_ayuda()
        messagebox.showinfo('AXION · Ayuda',
            'Definir → Procedimiento → Resultado y comprobación.\n\n'
            'Vectores: suma/resta componente a componente; λ multiplica cada componente.\n'
            'Matrices: AB combina cada fila de A con cada columna de B.\n'
            'Combinación: los vectores se colocan como columnas de V para resolver Vc=b. '
            'Un conjunto dependiente puede representar b con infinitos coeficientes.\n\n'
            '1–8 por eje. Números: enteros, decimales (punto o coma), fracciones a/b, exponente e. '
            '64 caracteres, 48 dígitos; sin expresiones ni denominador cero.\n'
            'Pegar tabla: tabulaciones y saltos de línea, máximo 4096 caracteres. '
            'La coma es decimal, nunca separador de columnas.\n\n'
            'Ctrl+Enter calcula · Ctrl+Z deshace edición · Ctrl+S guarda TXT\n'
            'Alt+Izquierda/Derecha recorre pasos · Tab navega controles · F1 abre ayuda.\n'
            'Fracciones/Decimales solo cambia la presentación. ≈ señala aproximación.\n'
            'Las ediciones conservan el resultado anterior identificado hasta recalcular.', parent=self.raiz)


def lanzar_aplicacion():
    """Inicializa Tk solo al ejecutar el lanzador; importar no abre ventanas."""
    try:
        from ctypes import windll
        windll.shcore.SetProcessDpiAwareness(1)
    except (ImportError, AttributeError, OSError):
        pass
    raiz = tk.Tk()
    AplicacionPrograma3(raiz)
    raiz.mainloop()
