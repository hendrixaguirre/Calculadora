"""Interfaz del laboratorio educativo AXION construida con Tkinter.

Los identificadores creados por el proyecto están en español. Se conservan en
inglés únicamente nombres fijados por Python o Tkinter —por ejemplo ``self``,
``event``, ``text``, ``row``, ``column``, ``width``, ``height`` y ``command``—
porque modificarlos impediría que la biblioteca reconociera sus opciones.
"""

from __future__ import annotations

import re
import tempfile
import tkinter as tk
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from axion_core import (
    ResultadoCalculo,
    Matriz,
    PasoFila,
    construir_reporte,
    numero_compacto,
    texto_ecuacion,
    formatear_numero,
    texto_matriz,
    lineas_parametricas,
    nombre_fila,
    resolver_sistema,
    a_fraccion,
    texto_forma_vectorial,
)
from axion_storage import VERSION_MOTOR, AlmacenHistorial, construir_reporte_html


class TemaAxion:
    LIENZO = "#F6F5F0"
    PAPEL = "#FFFFFF"
    PAPEL_ALTERNO = "#F8F9F7"
    TINTA = "#172033"
    ATENUADO = "#667085"
    LINEA = "#D7DCE2"
    LINEA_OSCURA = "#AEB7C4"
    AZUL_MARINO = "#182338"
    INDIGO = "#1D4ED8"
    INDIGO_PALIDO = "#EAF0F7"
    AZUL_PALIDO = "#E8F2FA"
    AMBAR = "#9A3412"
    AMBAR_PALIDO = "#FFF4DD"
    VERDE_AZULADO = "#187A5A"
    VERDE_AZULADO_PALIDO = "#E8F5EF"
    ROJO = "#A33A46"
    ROJO_PALIDO = "#FBECEF"
    FUENTE_SANS = "Segoe UI"
    FUENTE_MONO = "Cascadia Mono"


def limpiar_hijos(widget):
    for hijo in widget.winfo_children():
        hijo.destroy()


class AreaDesplazableAxion(tk.Frame):
    def __init__(
        self, parent, background=TemaAxion.PAPEL, horizontal=False,
        vertical=True, **kwargs,
    ):
        super().__init__(parent, bg=background, **kwargs)
        self.horizontal_habilitado = horizontal
        self.vertical_habilitado = vertical
        self.canvas = tk.Canvas(self, bg=background, highlightthickness=0)
        self.vertical = None
        if vertical:
            self.vertical = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
            self.vertical.pack(side="right", fill="y")
        if horizontal:
            self.horizontal = ttk.Scrollbar(self, orient="horizontal", command=self.canvas.xview)
            self.canvas.configure(xscrollcommand=self.horizontal.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        self.contenido = tk.Frame(self.canvas, bg=background)
        self.ventana = self.canvas.create_window((0, 0), window=self.contenido, anchor="nw")
        if vertical:
            self.canvas.configure(yscrollcommand=self.vertical.set)
        self.contenido.bind("<Configure>", self._actualizar_region)
        self.canvas.bind("<Configure>", self._redimensionar_contenido)
        self.canvas.bind("<MouseWheel>", self._rueda)

    def _actualizar_region(self, _event=None):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self._sincronizar_desplazamiento_horizontal()

    def _redimensionar_contenido(self, event):
        solicitado = self.contenido.winfo_reqwidth()
        width = max(event.width, solicitado) if self.horizontal_habilitado else event.width
        self.canvas.itemconfigure(self.ventana, width=width)
        self._sincronizar_desplazamiento_horizontal()

    def _sincronizar_desplazamiento_horizontal(self):
        if not self.horizontal_habilitado:
            return
        necesaria = self.contenido.winfo_reqwidth() > self.canvas.winfo_width() + 2
        if necesaria and not self.horizontal.winfo_manager():
            opciones = {"side": "bottom", "fill": "x"}
            if self.canvas.winfo_manager():
                opciones["before"] = self.canvas
            self.horizontal.pack(**opciones)
        elif not necesaria and self.horizontal.winfo_manager():
            self.horizontal.pack_forget()

    def _rueda(self, event):
        if self.vertical_habilitado:
            self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")
        return "break"


class BarraDesplazamientoAutomaticaAxion(ttk.Scrollbar):
    """Solo ocupa espacio cuando el contenido realmente necesita desplazamiento."""

    def set(self, inferior, superior_limite):
        if float(inferior) <= 0.0 and float(superior_limite) >= 1.0:
            self.grid_remove()
        else:
            self.grid()
        super().set(inferior, superior_limite)


class VistaMatrizAxion(tk.Frame):
    """Representa una matriz con significado visual para filas, pivote y cambios."""

    def __init__(
        self, parent, matriz: Matriz, *, modo="fracciones", precision=4,
        fila_origen=None, fila_destino=None, pivote=None, modificadas=None,
        compacta=False, background=TemaAxion.PAPEL,
    ):
        super().__init__(parent, bg=background)
        modificadas = modificadas or set()
        variables = len(matriz[0]) - 1
        tamano_fuente = 11 if compacta else 13
        for column in range(variables):
            tk.Label(self, text=f"x{self._subindice(column + 1)}", bg=background,
                     fg=TemaAxion.ATENUADO, font=(TemaAxion.FUENTE_SANS, 10)).grid(
                         row=0, column=column + 3, pady=(0, 5))
        tk.Label(self, text="b", bg=background, fg=TemaAxion.INDIGO,
                 font=(TemaAxion.FUENTE_SANS, 10, "bold")).grid(
                     row=0, column=variables + 5, pady=(0, 5))
        for indice_fila, row in enumerate(matriz):
            marcador = ""
            color_marcador = TemaAxion.ATENUADO
            if indice_fila == fila_destino:
                marcador, color_marcador = "DESTINO", TemaAxion.AMBAR
            elif indice_fila == fila_origen:
                marcador, color_marcador = "REFERENCIA", TemaAxion.INDIGO
            tk.Label(self, text=marcador, bg=background, fg=color_marcador,
                     width=11, anchor="e", font=(TemaAxion.FUENTE_SANS, 10, "bold")).grid(
                         row=indice_fila + 1, column=0, padx=(0, 7))
            tk.Label(self, text=nombre_fila(indice_fila), bg=background, fg=TemaAxion.ATENUADO,
                     font=(TemaAxion.FUENTE_MONO, 10)).grid(row=indice_fila + 1, column=1, padx=(0, 6))
            for column, value in enumerate(row):
                es_pivote = pivote == (indice_fila, column)
                esta_modificada = (indice_fila, column) in modificadas
                if es_pivote:
                    fill, color = TemaAxion.VERDE_AZULADO_PALIDO, TemaAxion.VERDE_AZULADO
                elif esta_modificada:
                    fill, color = TemaAxion.AMBAR_PALIDO, TemaAxion.AMBAR
                elif indice_fila == fila_destino:
                    fill, color = "#FFFAF0", TemaAxion.TINTA
                elif indice_fila == fila_origen:
                    fill, color = "#F2F7FB", TemaAxion.TINTA
                else:
                    fill, color = background, TemaAxion.TINTA
                visualizacion = numero_compacto(value, modo, precision)
                columna_objetivo = variables + 5 if column == variables else column + 3
                etiqueta = tk.Label(
                    self, text=visualizacion, bg=fill, fg=color, width=max(8 if not compacta else 7, len(visualizacion) + 1),
                    pady=7 if not compacta else 4, font=(TemaAxion.FUENTE_MONO, tamano_fuente, "bold"),
                    highlightthickness=1 if es_pivote or esta_modificada else 0,
                    highlightbackground=TemaAxion.VERDE_AZULADO if es_pivote else TemaAxion.AMBAR,
                )
                etiqueta.grid(row=indice_fila + 1, column=columna_objetivo, padx=2, pady=2)
            tk.Frame(self, bg=TemaAxion.LINEA_OSCURA, width=1).grid(
                row=indice_fila + 1, column=variables + 4, sticky="ns", padx=6)
        filas = len(matriz)
        left = "[" if filas == 1 else "\n".join(["⎡"] + ["⎢"] * (filas - 2) + ["⎣"])
        right = "]" if filas == 1 else "\n".join(["⎤"] + ["⎥"] * (filas - 2) + ["⎦"])
        tk.Label(self, text=left, bg=background, fg=TemaAxion.TINTA,
                 font=(TemaAxion.FUENTE_MONO, 21 if not compacta else 17)).grid(
                     row=1, column=2, rowspan=filas, sticky="e", padx=(8, 0))
        tk.Label(self, text=right, bg=background, fg=TemaAxion.TINTA,
                 font=(TemaAxion.FUENTE_MONO, 21 if not compacta else 17)).grid(
                     row=1, column=variables + 6, rowspan=filas, sticky="w")

    @staticmethod
    def _subindice(value):
        return str(value).translate(str.maketrans("0123456789", "₀₁₂₃₄₅₆₇₈₉"))


class EditorSistemaAxion(tk.Frame):
    EJEMPLOS = {
        "Solución única": (
            [[2, 1, 5], [1, -1, 1]],
            "Dos ecuaciones independientes con una sola solución.",
        ),
        "Infinitas soluciones": (
            [[1, 1, 1, 2], [2, 2, 2, 4]],
            "La segunda ecuación es múltiplo de la primera y aparecen variables libres.",
        ),
        "Sistema incompatible": (
            [[1, 1, 2], [1, 1, 5]],
            "Las ecuaciones tienen el mismo lado izquierdo, pero resultados diferentes.",
        ),
        "Intercambio de filas": (
            [[0, 1, 2], [1, 1, 3]],
            "El primer candidato a pivote es cero y se requiere intercambiar filas.",
        ),
        "Sistema 3×3": (
            [[1, 1, 1, 6], [2, -1, 1, 3], [1, 2, -1, 2]],
            "Ejemplo de tres variables con solución única.",
        ),
        "Sistema con fracciones": (
            [["1/2", 1, 2], [1, "-1/3", 1]],
            "Conserva 1/2 y −1/3 como valores racionales exactos.",
        ),
        "Fracciones extensas": (
            [["123456789/100000000", "-9876543/7654321", "11111111/9999999"],
             ["17/31", "29/37", "41/43"]],
            "Comprueba el dimensionado y el desplazamiento con racionales de varios dígitos.",
        ),
        "Prueba 8×8": (
            [[1 if row == column else 0 for column in range(8)] + [row + 1]
             for row in range(8)],
            "Matriz aumentada 8×9 para comprobar el límite visible de AXION.",
        ),
    }

    def __init__(self, parent, aplicacion):
        super().__init__(parent, bg=TemaAxion.PAPEL, highlightthickness=1,
                         highlightbackground=TemaAxion.LINEA)
        self.aplicacion = aplicacion
        self.filas = tk.IntVar(value=2)
        self.variables = tk.IntVar(value=2)
        self.metodo = tk.StringVar(value="Gauss-Jordan")
        self.vista = "matriz"
        self.variables_celdas: list[list[tk.StringVar]] = []
        self.entradas: list[list[tk.Entry]] = []
        self.pila_deshacer: list[list[list[str]]] = []
        self.foco_original = ""
        self.suspender_eventos = False
        self.modificado = False
        self.instantanea_original: list[list[str]] | None = None
        self._construir()
        self.generar_matriz(conservar=False)

    def _construir(self):
        cabecera = tk.Frame(self, bg=TemaAxion.PAPEL)
        cabecera.pack(fill="x", padx=24, pady=(14, 8))
        tk.Label(cabecera, text="1. Definir sistema", bg=TemaAxion.PAPEL,
                 fg=TemaAxion.TINTA, font=(TemaAxion.FUENTE_SANS, 24, "bold")).pack(anchor="w")
        tk.Label(cabecera, text="Introduce los coeficientes de la matriz aumentada [A|b]. Límites: 1–8 ecuaciones y variables.",
                 bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO,
                 font=(TemaAxion.FUENTE_SANS, 11)).pack(anchor="w", pady=(5, 0))

        controles = tk.Frame(self, bg=TemaAxion.PAPEL)
        controles.pack(fill="x", padx=24, pady=(2, 7))
        self._control_dimension(controles, "Ecuaciones", self.filas).pack(side="left")
        self._control_dimension(controles, "Variables", self.variables).pack(side="left", padx=16)
        tk.Button(controles, text="Aplicar dimensiones", command=self.aplicar_dimensiones,
                  relief="flat", bg=TemaAxion.INDIGO_PALIDO, fg=TemaAxion.INDIGO,
                  activebackground="#DDE8F3", cursor="hand2", padx=12, pady=8,
                  font=(TemaAxion.FUENTE_SANS, 11, "bold")).pack(side="left")

        fila_metodo = tk.Frame(self, bg=TemaAxion.PAPEL)
        fila_metodo.pack(fill="x", padx=24, pady=(1, 7))
        tk.Label(fila_metodo, text="Método", bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO,
                 font=(TemaAxion.FUENTE_SANS, 11)).pack(side="left")
        caja_metodo = ttk.Combobox(
            fila_metodo, textvariable=self.metodo, state="readonly", width=23,
            values=("Gauss-Jordan", "Eliminación de Gauss"),
            font=(TemaAxion.FUENTE_SANS, 11),
        )
        caja_metodo.pack(side="left", padx=(8, 0))
        caja_metodo.bind("<<ComboboxSelected>>", lambda _e: self._metodo_cambiado())
        self.ayuda_metodo = tk.Label(
            self, text="Gauss-Jordan obtiene la forma escalonada reducida por filas (RREF).",
            bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO, anchor="w",
            font=(TemaAxion.FUENTE_SANS, 11)
        )
        self.ayuda_metodo.pack(fill="x", padx=24, pady=(0, 6))

        pestanas = tk.Frame(self, bg=TemaAxion.PAPEL)
        pestanas.pack(fill="x", padx=24)
        self.botones_pestanas = {}
        for clave, text in (("matriz", "Matriz editable"), ("ecuaciones", "Vista como ecuaciones")):
            boton = tk.Button(
                pestanas, text=text, command=lambda indice_k=clave: self.mostrar_vista(indice_k), relief="flat",
                bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO, cursor="hand2",
                padx=10, pady=7, font=(TemaAxion.FUENTE_SANS, 11, "bold")
            )
            boton.pack(side="left")
            self.botones_pestanas[clave] = boton
        tk.Frame(self, bg=TemaAxion.LINEA, height=1).pack(fill="x", padx=24)

        self.contenedor_editor = tk.Frame(self, bg=TemaAxion.PAPEL, height=230)
        self.contenedor_editor.pack(fill="x", padx=24, pady=7)
        self.contenedor_editor.pack_propagate(False)
        self.contenedor_matriz = tk.Frame(self.contenedor_editor, bg=TemaAxion.PAPEL)
        self.contenedor_matriz.grid_rowconfigure(0, weight=1)
        self.contenedor_matriz.grid_columnconfigure(0, weight=1)
        self.lienzo_matriz = tk.Canvas(
            self.contenedor_matriz, bg=TemaAxion.PAPEL, highlightthickness=0
        )
        self.desplazamiento_matriz_y = BarraDesplazamientoAutomaticaAxion(
            self.contenedor_matriz, orient="vertical", command=self.lienzo_matriz.yview
        )
        self.desplazamiento_matriz_x = BarraDesplazamientoAutomaticaAxion(
            self.contenedor_matriz, orient="horizontal", command=self.lienzo_matriz.xview
        )
        self.lienzo_matriz.configure(
            yscrollcommand=self.desplazamiento_matriz_y.set, xscrollcommand=self.desplazamiento_matriz_x.set
        )
        self.lienzo_matriz.grid(row=0, column=0, sticky="nsew")
        self.desplazamiento_matriz_y.grid(row=0, column=1, sticky="ns")
        self.desplazamiento_matriz_x.grid(row=1, column=0, sticky="ew")
        self.marco_matriz = tk.Frame(self.lienzo_matriz, bg=TemaAxion.PAPEL)
        self.ventana_matriz = self.lienzo_matriz.create_window(
            (0, 0), window=self.marco_matriz, anchor="nw"
        )
        self.marco_matriz.bind("<Configure>", lambda _e: self.lienzo_matriz.configure(
            scrollregion=self.lienzo_matriz.bbox("all")))
        self.lienzo_matriz.bind("<Configure>", self._centrar_matriz)
        self.lienzo_matriz.bind("<MouseWheel>", lambda e: self.lienzo_matriz.yview_scroll(
            -1 if e.delta > 0 else 1, "units"))
        self.marco_ecuaciones = tk.Frame(self.contenedor_editor, bg=TemaAxion.PAPEL)
        self.etiqueta_ecuaciones = tk.Label(
            self.marco_ecuaciones, text="", bg=TemaAxion.PAPEL, fg=TemaAxion.TINTA,
            justify="left", anchor="nw", font=(TemaAxion.FUENTE_SANS, 13), wraplength=470
        )
        self.etiqueta_ecuaciones.pack(fill="both", expand=True, padx=12, pady=12)

        self.error_en_linea = tk.Label(
            self, text="", bg=TemaAxion.PAPEL, fg=TemaAxion.ROJO,
            anchor="w", font=(TemaAxion.FUENTE_SANS, 11)
        )
        self.error_en_linea.pack(fill="x", padx=24)
        self.estado_entrada = tk.Label(
            self, text="", bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO,
            anchor="w", font=(TemaAxion.FUENTE_SANS, 11)
        )
        self.estado_entrada.pack(fill="x", padx=24, pady=(3, 9))

        area_ejemplos = tk.Frame(self, bg=TemaAxion.PAPEL_ALTERNO,
                                highlightthickness=1, highlightbackground=TemaAxion.LINEA)
        area_ejemplos.pack(fill="x", padx=24, pady=(0, 8))
        tk.Label(area_ejemplos, text="Ejemplos para probar", bg=TemaAxion.PAPEL_ALTERNO,
                 fg=TemaAxion.TINTA, font=(TemaAxion.FUENTE_SANS, 10, "bold")).pack(
                     anchor="w", padx=12, pady=(9, 4))
        selector_metodo = tk.Frame(area_ejemplos, bg=TemaAxion.PAPEL_ALTERNO)
        selector_metodo.pack(fill="x", padx=12)
        self.ejemplo = tk.StringVar(value="Solución única")
        ttk.Combobox(selector_metodo, textvariable=self.ejemplo, state="readonly", width=26,
                     values=tuple(self.EJEMPLOS), font=(TemaAxion.FUENTE_SANS, 11)).pack(side="left")
        tk.Button(selector_metodo, text="Cargar ejemplo", command=self.cargar_ejemplo,
                  relief="flat", bg=TemaAxion.INDIGO_PALIDO, fg=TemaAxion.INDIGO,
                  cursor="hand2", padx=10, pady=6,
                  font=(TemaAxion.FUENTE_SANS, 11, "bold")).pack(side="left", padx=8)
        self.descripcion_ejemplo = tk.Label(
            area_ejemplos, text=self.EJEMPLOS["Solución única"][1], bg=TemaAxion.PAPEL_ALTERNO,
            fg=TemaAxion.ATENUADO, anchor="w", wraplength=700, font=(TemaAxion.FUENTE_SANS, 10)
        )
        self.descripcion_ejemplo.pack(fill="x", padx=12, pady=(5, 9))
        self.ejemplo.trace_add("write", lambda *_: self.descripcion_ejemplo.configure(
            text=self.EJEMPLOS[self.ejemplo.get()][1]))

        acciones = tk.Frame(self, bg=TemaAxion.PAPEL)
        acciones.pack(fill="x", padx=24, pady=(0, 12))
        self.botones_secundarios = {}
        for text, command in (("Limpiar entrada", self.limpiar_matriz),
                              ("Restaurar entrada resuelta", self.restaurar_original),
                              ("Deshacer edición", self.deshacer)):
            boton = tk.Button(acciones, text=text, command=command, relief="flat",
                               bg=TemaAxion.PAPEL, fg=TemaAxion.INDIGO,
                               disabledforeground=TemaAxion.LINEA_OSCURA,
                               activebackground=TemaAxion.INDIGO_PALIDO, cursor="hand2",
                               padx=8, pady=8, font=(TemaAxion.FUENTE_SANS, 10))
            boton.pack(side="left", padx=(0, 3))
            self.botones_secundarios[text] = boton
        self.boton_resolver = tk.Button(
            acciones, text="Resolver con Gauss-Jordan", command=self.aplicacion.resolver,
            relief="flat", bg=TemaAxion.INDIGO, fg="white",
            activebackground="#254C79", activeforeground="white", cursor="hand2",
            padx=20, pady=10, font=(TemaAxion.FUENTE_SANS, 10, "bold"), state="disabled"
        )
        self.boton_resolver.pack(side="right")

    def _control_dimension(self, parent, title, variable):
        marco = tk.Frame(parent, bg=TemaAxion.PAPEL)
        tk.Label(marco, text=title, bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO,
                 font=(TemaAxion.FUENTE_SANS, 11)).pack(side="left", padx=(0, 7))
        caja = tk.Frame(marco, bg=TemaAxion.PAPEL, highlightthickness=1,
                       highlightbackground=TemaAxion.LINEA)
        caja.pack(side="left")
        tk.Button(caja, text="−", command=lambda: variable.set(max(1, variable.get() - 1)),
                  relief="flat", bg=TemaAxion.PAPEL, fg=TemaAxion.INDIGO,
                  width=2, cursor="hand2").pack(side="left")
        tk.Label(caja, textvariable=variable, bg=TemaAxion.PAPEL, fg=TemaAxion.TINTA,
                 width=2, font=(TemaAxion.FUENTE_SANS, 10, "bold")).pack(side="left")
        tk.Button(caja, text="+", command=lambda: variable.set(min(8, variable.get() + 1)),
                  relief="flat", bg=TemaAxion.PAPEL, fg=TemaAxion.INDIGO,
                  width=2, cursor="hand2").pack(side="left")
        return marco

    def _metodo_cambiado(self):
        descripciones = {
            "Automático": "AXION elegirá el método y mostrará cuál utilizó.",
            "Eliminación de Gauss": "Obtiene forma escalonada y usa sustitución hacia atrás.",
            "Gauss-Jordan": "Continúa hasta la forma escalonada reducida por filas.",
        }
        self.ayuda_metodo.configure(text=descripciones[self.metodo.get()])
        self.boton_resolver.configure(
            text=("Resolver con Gauss-Jordan" if self.metodo.get() == "Gauss-Jordan"
                  else "Resolver con eliminación de Gauss")
        )
        self.modificado = True
        self.aplicacion.marcar_edicion()

    def mostrar_vista(self, vista):
        self.vista = vista
        self.contenedor_matriz.pack_forget()
        self.marco_ecuaciones.pack_forget()
        if vista == "matriz":
            self.contenedor_matriz.pack(fill="both", expand=True)
            self.contenedor_matriz.update_idletasks()
            self._actualizar_posicion_matriz()
        else:
            self.actualizar_ecuaciones()
            self.marco_ecuaciones.pack(fill="both", expand=True)
        for clave, boton in self.botones_pestanas.items():
            seleccionado = clave == vista
            boton.configure(fg=TemaAxion.INDIGO if seleccionado else TemaAxion.ATENUADO,
                             bg=TemaAxion.INDIGO_PALIDO if seleccionado else TemaAxion.PAPEL)

    def _centrar_matriz(self, event):
        self._actualizar_posicion_matriz(event.width, event.height)

    def _actualizar_posicion_matriz(self, width=None, height=None):
        self.marco_matriz.update_idletasks()
        width = width or self.lienzo_matriz.winfo_width()
        height = height or self.lienzo_matriz.winfo_height()
        ancho_solicitado = self.marco_matriz.winfo_reqwidth()
        alto_solicitado = self.marco_matriz.winfo_reqheight()
        self.lienzo_matriz.coords(
            self.ventana_matriz,
            max(0, (width - ancho_solicitado) // 2),
            max(0, (height - alto_solicitado) // 2),
        )
        self.lienzo_matriz.configure(scrollregion=self.lienzo_matriz.bbox("all"))

    def instantanea(self):
        if not self.variables_celdas or self.suspender_eventos:
            return
        state = [[variable.get() for variable in row] for row in self.variables_celdas]
        if not self.pila_deshacer or self.pila_deshacer[-1] != state:
            self.pila_deshacer.append(state)
            self.pila_deshacer = self.pila_deshacer[-50:]

    def aplicar_dimensiones(self):
        try:
            filas, variables = self.filas.get(), self.variables.get()
            if not (1 <= filas <= 8 and 1 <= variables <= 8):
                raise ValueError('Usa entre 1 y 8 ecuaciones y variables')
        except (tk.TclError, ValueError) as error:
            self.error_en_linea.configure(text=f'Dimensiones inválidas: {error}', fg=TemaAxion.ROJO)
            return
        filas_anteriores = len(self.variables_celdas)
        columnas_anteriores = len(self.variables_celdas[0]) if self.variables_celdas else 0
        filas_nuevas, columnas_nuevas = self.filas.get(), self.variables.get() + 1
        valores_eliminados = []
        for i in range(filas_anteriores):
            for j in range(columnas_anteriores):
                if (i >= filas_nuevas or j >= columnas_nuevas) and self.variables_celdas[i][j].get().strip():
                    valores_eliminados.append(self.variables_celdas[i][j].get())
        if valores_eliminados and not messagebox.askyesno(
                "Reducir dimensiones",
                "Las nuevas dimensiones eliminarán valores existentes. ¿Deseas continuar?",
                parent=self.winfo_toplevel()):
            self.filas.set(filas_anteriores)
            self.variables.set(columnas_anteriores - 1)
            return
        self.instantanea()
        self.generar_matriz(conservar=True)

    def generar_matriz(self, conservar=True):
        anterior = [[variable_auxiliar.get() for variable_auxiliar in row] for row in self.variables_celdas] if conservar else []
        limpiar_hijos(self.marco_matriz)
        self.variables_celdas, self.entradas = [], []
        filas, variables = self.filas.get(), self.variables.get()
        grid = tk.Frame(self.marco_matriz, bg=TemaAxion.PAPEL)
        grid.pack(expand=True)
        for column in range(variables):
            tk.Label(grid, text=f"x{VistaMatrizAxion._subindice(column + 1)}", bg=TemaAxion.PAPEL,
                     fg=TemaAxion.ATENUADO, font=(TemaAxion.FUENTE_SANS, 10)).grid(
                         row=0, column=column + 1, pady=(0, 6))
        tk.Label(grid, text="b", bg=TemaAxion.PAPEL, fg=TemaAxion.INDIGO,
                 font=(TemaAxion.FUENTE_SANS, 10, "bold")).grid(
                     row=0, column=variables + 2, pady=(0, 6))
        left = "[" if filas == 1 else "\n".join(["⎡"] + ["⎢"] * (filas - 2) + ["⎣"])
        right = "]" if filas == 1 else "\n".join(["⎤"] + ["⎥"] * (filas - 2) + ["⎦"])
        tk.Label(grid, text=left, bg=TemaAxion.PAPEL, fg=TemaAxion.TINTA,
                 font=(TemaAxion.FUENTE_MONO, 24)).grid(row=1, column=0, rowspan=filas, sticky="ns")
        tk.Frame(grid, bg=TemaAxion.LINEA_OSCURA, width=1).grid(
            row=1, column=variables + 1, rowspan=filas, sticky="ns", padx=7, pady=3)
        tk.Label(grid, text=right, bg=TemaAxion.PAPEL, fg=TemaAxion.TINTA,
                 font=(TemaAxion.FUENTE_MONO, 24)).grid(
                     row=1, column=variables + 3, rowspan=filas, sticky="ns")
        self.suspender_eventos = True
        for row in range(filas):
            variables_fila, entradas_fila = [], []
            for column in range(variables + 1):
                value = anterior[row][column] if row < len(anterior) and column < len(anterior[row]) else ""
                variable = tk.StringVar(value=value)
                entrada = tk.Entry(
                    grid, textvariable=variable, width=7, justify="center", relief="flat",
                     bg=TemaAxion.PAPEL_ALTERNO, fg=TemaAxion.TINTA,
                     insertbackground=TemaAxion.INDIGO, font=(TemaAxion.FUENTE_MONO, 13),
                    highlightthickness=1, highlightbackground=TemaAxion.LINEA,
                    highlightcolor=TemaAxion.INDIGO,
                )
                columna_objetivo = variables + 2 if column == variables else column + 1
                entrada.grid(row=row + 1, column=columna_objetivo, padx=3, pady=3, ipady=8)
                entrada.bind("<FocusIn>", self._al_enfocar)
                entrada.bind("<FocusOut>", lambda e, r=row, c=column: self.validar_celda(r, c))
                entrada.bind("<KeyPress>", self._antes_tecla)
                entrada.bind("<Escape>", self._salir_celda)
                entrada.bind("<Control-v>", self.pegado_inteligente)
                entrada.bind("<Control-V>", self.pegado_inteligente)
                entrada.bind("<Control-z>", lambda _e: (self.deshacer(), "break")[1])
                entrada.bind("<Return>", lambda _e, r=row, c=column: self.mover_foco(r + 1, c))
                entrada.bind("<Up>", lambda _e, r=row, c=column: self.mover_foco(r - 1, c))
                entrada.bind("<Down>", lambda _e, r=row, c=column: self.mover_foco(r + 1, c))
                entrada.bind("<Left>", lambda e, r=row, c=column: self._movimiento_horizontal(e, r, c, -1))
                entrada.bind("<Right>", lambda e, r=row, c=column: self._movimiento_horizontal(e, r, c, 1))
                variable.trace_add("write", lambda *_: self.al_editar())
                variables_fila.append(variable)
                entradas_fila.append(entrada)
            self.variables_celdas.append(variables_fila)
            self.entradas.append(entradas_fila)
        self.suspender_eventos = False
        self.mostrar_vista(self.vista)
        self._actualizar_posicion_matriz()
        self.actualizar_estado()

    def _al_enfocar(self, event):
        self.foco_original = event.widget.get()
        event.widget.configure(bg="#F0F5FB", highlightbackground=TemaAxion.INDIGO)
        row = int(event.widget.grid_info()["row"])
        column = int(event.widget.grid_info()["column"])
        columna_logica = column - 1 if column <= self.variables.get() else self.variables.get()
        funcion = "término independiente b" if columna_logica == self.variables.get() else f"coeficiente de x{columna_logica + 1}"
        self.aplicacion.establecer_estado(f"Ecuación {row}: {funcion}.", "editando")

    def _antes_tecla(self, event):
        navegacion = {
            "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R",
            "Tab", "Return", "Escape", "Left", "Right", "Up", "Down",
            "Home", "End", "Prior", "Next",
        }
        control_o_alt = event.state & 0x0C
        if not control_o_alt and event.keysym not in navegacion and (
                event.char or event.keysym in {"BackSpace", "Delete"}):
            self.instantanea()

    def _movimiento_horizontal(self, event, row, column, direccion):
        """Conserva el cursor de texto y cruza de celda solo en los extremos."""
        try:
            if event.widget.selection_present():
                return None
        except tk.TclError:
            return None
        posicion_insercion = event.widget.index("insert")
        if direccion < 0 and posicion_insercion > 0:
            return None
        if direccion > 0 and posicion_insercion < len(event.widget.get()):
            return None
        return self.mover_foco(row, column + direccion)

    def _salir_celda(self, event):
        event.widget.delete(0, "end")
        event.widget.insert(0, self.foco_original)
        event.widget.selection_clear()
        return "break"

    def mover_foco(self, row, column):
        if row >= len(self.entradas):
            self.aplicacion.resolver()
            return "break"
        if 0 <= row < len(self.entradas) and 0 <= column < len(self.entradas[0]):
            self.entradas[row][column].focus_set()
            self.entradas[row][column].selection_range(0, "end")
        return "break"

    def validar_celda(self, row, column):
        entrada = self.entradas[row][column]
        text = self.variables_celdas[row][column].get().strip()
        try:
            a_fraccion(text)
        except ZeroDivisionError:
            mensaje = "El denominador no puede ser cero"
        except ValueError:
            mensaje = "Ingresa un valor" if not text else "Utiliza enteros, decimales o fracciones"
        else:
            entrada.configure(bg=TemaAxion.PAPEL_ALTERNO, highlightbackground=TemaAxion.LINEA)
            self.error_en_linea.configure(text="")
            self.actualizar_estado()
            return True
        entrada.configure(bg=TemaAxion.ROJO_PALIDO, highlightbackground=TemaAxion.ROJO)
        self.error_en_linea.configure(text=f"Fila {row + 1}, columna {column + 1}: {mensaje}.")
        self.actualizar_estado()
        return False

    def al_editar(self):
        if self.suspender_eventos:
            return
        self.modificado = True
        self.actualizar_ecuaciones()
        self.actualizar_estado()
        self.aplicacion.marcar_edicion()

    def actualizar_estado(self):
        faltantes, invalido = 0, 0
        for row in self.variables_celdas:
            for variable in row:
                text = variable.get().strip()
                if not text:
                    faltantes += 1
                else:
                    try:
                        a_fraccion(text)
                    except (ValueError, ZeroDivisionError):
                        invalido += 1
        if invalido:
            text, color = f"Revisa {invalido} valor(es) inválido(s) antes de continuar.", TemaAxion.ROJO
            state = "disabled"
        elif faltantes:
            text, color = f"Faltan {faltantes} valores para completar la matriz.", TemaAxion.AMBAR
            state = "disabled"
        else:
            text, color = "Matriz completa. Lista para resolver.", TemaAxion.VERDE_AZULADO
            state = "normal"
        self.estado_entrada.configure(text=text, fg=color)
        self.boton_resolver.configure(state=state)
        if hasattr(self, "secondary_buttons"):
            tiene_valores = any(variable.get().strip() for row in self.variables_celdas for variable in row)
            self.botones_secundarios["Limpiar entrada"].configure(
                state="normal" if tiene_valores else "disabled")
            self.botones_secundarios["Restaurar entrada resuelta"].configure(
                state="normal" if self.instantanea_original is not None else "disabled")
            self.botones_secundarios["Deshacer edición"].configure(
                state="normal" if self.pila_deshacer else "disabled")

    def actualizar_ecuaciones(self):
        lineas = []
        for index, row in enumerate(self.variables_celdas):
            values = [variable.get().strip() for variable in row]
            try:
                linea = texto_ecuacion(values)
            except (ValueError, ZeroDivisionError):
                linea = f"Ecuación {index + 1}: completa todos los valores"
            lineas.append(linea)
        self.etiqueta_ecuaciones.configure(text="\n\n".join(lineas))

    def obtener_valores(self):
        values = []
        for indice_fila, row in enumerate(self.variables_celdas):
            interpretados = []
            for indice_columna, variable in enumerate(row):
                try:
                    interpretados.append(a_fraccion(variable.get()))
                except ZeroDivisionError as error:
                    self.validar_celda(indice_fila, indice_columna)
                    self.entradas[indice_fila][indice_columna].focus_set()
                    raise ValueError("El denominador no puede ser cero") from error
                except ValueError as error:
                    self.validar_celda(indice_fila, indice_columna)
                    self.entradas[indice_fila][indice_columna].focus_set()
                    raise ValueError("Revisa las celdas marcadas antes de continuar") from error
            values.append(interpretados)
        return values

    def establecer_valores(self, values, registrar_deshacer=True):
        if registrar_deshacer:
            self.instantanea()
        filas, columns = len(values), len(values[0])
        self.filas.set(filas)
        self.variables.set(columns - 1)
        self.generar_matriz(conservar=False)
        self.suspender_eventos = True
        for i, row in enumerate(values):
            for j, value in enumerate(row):
                self.variables_celdas[i][j].set(formatear_numero(value))
        self.suspender_eventos = False
        self.modificado = True
        self.actualizar_ecuaciones()
        self.actualizar_estado()
        self.aplicacion.marcar_edicion()

    def cargar_ejemplo(self):
        values, descripcion = self.EJEMPLOS[self.ejemplo.get()]
        self.establecer_valores(values)
        self.descripcion_ejemplo.configure(text=descripcion + " Puedes modificarlo antes de resolver.")
        self.boton_resolver.focus_set()
        self.aplicacion.establecer_estado("Ejemplo cargado. Revísalo y pulsa la acción principal para resolver.", "listo")

    def limpiar_matriz(self):
        self.instantanea()
        self.suspender_eventos = True
        for row in self.variables_celdas:
            for variable in row:
                variable.set("")
        self.suspender_eventos = False
        self.modificado = True
        self.error_en_linea.configure(text="")
        self.actualizar_ecuaciones()
        self.actualizar_estado()
        if self.aplicacion.resultado:
            self.aplicacion.marcar_edicion()
        else:
            self.aplicacion.establecer_estado("Entrada vacía. Puedes deshacer esta acción.", "inicial")

    def restaurar_original(self):
        if self.instantanea_original is None:
            self.error_en_linea.configure(text="Todavía no existe una matriz original resuelta.")
            return
        self.establecer_valores(self.instantanea_original)
        self.error_en_linea.configure(text="Valores originales restaurados.", fg=TemaAxion.VERDE_AZULADO)

    def deshacer(self):
        if not self.pila_deshacer:
            self.error_en_linea.configure(text="No hay cambios para deshacer.", fg=TemaAxion.ATENUADO)
            return
        state = self.pila_deshacer.pop()
        if len(state) != len(self.variables_celdas) or len(state[0]) != len(self.variables_celdas[0]):
            self.filas.set(len(state))
            self.variables.set(len(state[0]) - 1)
            self.generar_matriz(conservar=False)
        self.suspender_eventos = True
        for i, row in enumerate(state):
            for j, value in enumerate(row):
                self.variables_celdas[i][j].set(value)
        self.suspender_eventos = False
        self.actualizar_ecuaciones()
        self.actualizar_estado()
        self.error_en_linea.configure(text="Último cambio deshecho.", fg=TemaAxion.VERDE_AZULADO)
        self.aplicacion.marcar_edicion()

    def pegado_inteligente(self, _event=None):
        try:
            text = self.clipboard_get().strip()
        except tk.TclError:
            self.error_en_linea.configure(text="El portapapeles no contiene texto.", fg=TemaAxion.ROJO)
            return "break"
        if len(text) > 4096:
            self.error_en_linea.configure(
                text="El pegado supera 4096 caracteres. Divide la matriz en una entrada más pequeña.",
                fg=TemaAxion.ROJO)
            return "break"
        lineas_crudas = text.splitlines()
        if any(not linea.strip() for linea in lineas_crudas):
            self.error_en_linea.configure(
                text="No se pudo pegar la matriz: hay una fila vacía entre los datos.",
                fg=TemaAxion.ROJO,
            )
            return "break"
        lineas = [linea.strip() for linea in lineas_crudas]
        interpretados = []
        try:
            for linea in lineas:
                if "\t" in linea:
                    celdas = linea.split("\t")
                elif ";" in linea:
                    celdas = linea.split(";")
                elif re.search(r"\s", linea):
                    celdas = re.split(r"\s+", linea)
                else:
                    if "," in linea:
                        interpretacion = messagebox.askyesnocancel(
                            "Formato de comas ambiguo",
                            "Esta fila usa comas sin tabulaciones ni espacios.\n\n"
                            "Sí: las comas separan columnas (1,2,3).\n"
                            "No: la coma es decimal; cancela y separa columnas con Tab, espacio o punto y coma.\n\n"
                            "¿Deseas tratar las comas como separadores de columnas?",
                            parent=self.winfo_toplevel())
                        if interpretacion is not True:
                            return "break"
                    celdas = linea.split(",")
                if any(not celda.strip() for celda in celdas):
                    raise ValueError("hay una celda vacía; escribe 0 si ese coeficiente es cero")
                interpretados.append([a_fraccion(celda) for celda in celdas])
            if not interpretados or any(len(row) != len(interpretados[0]) for row in interpretados):
                raise ValueError("Las filas pegadas no tienen la misma longitud")
            if len(interpretados[0]) < 2:
                raise ValueError("Incluye al menos una variable y la columna b")
            if len(interpretados) > 8 or len(interpretados[0]) - 1 > 8:
                raise ValueError("AXION admite como máximo 8 ecuaciones y 8 variables")
        except (ValueError, ZeroDivisionError) as error:
            self.error_en_linea.configure(text=f"No se pudo pegar la matriz: {error}.", fg=TemaAxion.ROJO)
            return "break"
        dimensiones_nuevas = (len(interpretados), len(interpretados[0]) - 1)
        dimensiones_actuales = (self.filas.get(), self.variables.get())
        vista_previa = "\n".join("   ".join(formatear_numero(value) for value in row) for row in interpretados)
        nota_dimensiones = (
            f"Se ajustará el editor desde {dimensiones_actuales[0]}×{dimensiones_actuales[1]} "
            f"a {dimensiones_nuevas[0]}×{dimensiones_nuevas[1]}.\n\n"
            if dimensiones_nuevas != dimensiones_actuales else ""
        )
        if not messagebox.askyesno(
                "Previsualizar matriz pegada",
                f"{nota_dimensiones}Matriz aumentada detectada:\n\n{vista_previa}\n\n"
                "¿Deseas reemplazar la entrada actual de forma atómica?",
                parent=self.winfo_toplevel()):
            return "break"
        self.establecer_valores(interpretados)
        self.error_en_linea.configure(text="Matriz pegada y validada correctamente.", fg=TemaAxion.VERDE_AZULADO)
        return "break"

    def reiniciar_nuevo(self):
        self.filas.set(2)
        self.variables.set(2)
        self.pila_deshacer.clear()
        self.instantanea_original = None
        self.modificado = False
        self.generar_matriz(conservar=False)
        self.error_en_linea.configure(text="")

    def clave_metodo(self):
        return {
            "Eliminación de Gauss": "gauss",
            "Gauss-Jordan": "gauss-jordan",
        }[self.metodo.get()]


class CuadernoResolucionAxion(tk.Frame):
    def __init__(self, parent, aplicacion):
        super().__init__(parent, bg=TemaAxion.PAPEL, highlightthickness=1,
                         highlightbackground=TemaAxion.LINEA)
        self.aplicacion = aplicacion
        self.resultado: ResultadoCalculo | None = None
        self.paso_activo = 0
        self.vista_completa = False
        self.mostrar_formal = False
        self._construir()

    def _construir(self):
        cabecera = tk.Frame(self, bg=TemaAxion.PAPEL)
        cabecera.pack(fill="x", padx=24, pady=(18, 8))
        tk.Label(cabecera, text="Cuaderno de resolución", bg=TemaAxion.PAPEL,
                 fg=TemaAxion.TINTA, font=(TemaAxion.FUENTE_SANS, 18, "bold")).pack(side="left")
        self.insignia_metodo = tk.Label(
            cabecera, text="Sin resolver", bg=TemaAxion.PAPEL_ALTERNO, fg=TemaAxion.ATENUADO,
            padx=10, pady=5, font=(TemaAxion.FUENTE_SANS, 10, "bold")
        )
        self.insignia_metodo.pack(side="right")

        estilo = ttk.Style(self)
        estilo.configure("Axion.TNotebook", background=TemaAxion.PAPEL, borderwidth=0)
        estilo.configure("Axion.TNotebook.Tab", padding=(14, 8),
                        font=(TemaAxion.FUENTE_SANS, 10, "bold"))
        self.pestanas = ttk.Notebook(self, style="Axion.TNotebook")
        self.pestanas.pack(fill="both", expand=True, padx=16, pady=(0, 16))
        self.pestana_resultado = AreaDesplazableAxion(self.pestanas)
        self.pestana_procedimiento = tk.Frame(self.pestanas, bg=TemaAxion.PAPEL)
        self.pestana_verificacion = AreaDesplazableAxion(self.pestanas)
        self.pestana_reporte = tk.Frame(self.pestanas, bg=TemaAxion.PAPEL)
        self.pestanas.add(self.pestana_resultado, text="Resultado")
        self.pestanas.add(self.pestana_procedimiento, text="Procedimiento")
        self.pestanas.add(self.pestana_verificacion, text="Verificación")
        self.pestanas.add(self.pestana_reporte, text="Reporte")
        self.renderizar_vacio()

    def renderizar_vacio(self):
        limpiar_hijos(self.pestana_resultado.contenido)
        vacio = tk.Frame(self.pestana_resultado.contenido, bg=TemaAxion.PAPEL)
        vacio.pack(fill="x", padx=36, pady=90)
        tk.Label(vacio, text="Ax = b", bg=TemaAxion.PAPEL, fg=TemaAxion.INDIGO,
                 font=(TemaAxion.FUENTE_MONO, 28, "bold")).pack()
        tk.Label(vacio, text="Tu resolución aparecerá aquí", bg=TemaAxion.PAPEL,
                 fg=TemaAxion.TINTA, font=(TemaAxion.FUENTE_SANS, 16, "bold")).pack(pady=(18, 5))
        tk.Label(vacio, text=("Completa la matriz original, revisa su vista como ecuaciones "
                              "y selecciona Resolver sistema."), bg=TemaAxion.PAPEL,
                 fg=TemaAxion.ATENUADO, wraplength=480, justify="center",
                 font=(TemaAxion.FUENTE_SANS, 11)).pack()
        limpiar_hijos(self.pestana_procedimiento)
        limpiar_hijos(self.pestana_verificacion.contenido)
        limpiar_hijos(self.pestana_reporte)

    def establecer_resultado(self, resultado):
        self.resultado = resultado
        self.paso_activo = 0
        self.mostrar_formal = False
        self.vista_completa = False
        metodo = "Gauss-Jordan" if resultado.metodo_usado == "gauss-jordan" else "Eliminación de Gauss"
        self.insignia_metodo.configure(text=f"Método utilizado: {metodo}",
                                    bg=TemaAxion.INDIGO_PALIDO, fg=TemaAxion.INDIGO)
        self.renderizar_todo()
        self.pestanas.select(self.pestana_resultado)

    def renderizar_todo(self):
        if not self.resultado:
            return
        self.renderizar_resultado()
        self.renderizar_procedimiento()
        self.renderizar_verificacion()
        self.renderizar_reporte()

    def _titulo_seccion(self, parent, title, subtitulo=None):
        tk.Label(parent, text=title, bg=TemaAxion.PAPEL, fg=TemaAxion.TINTA,
                 font=(TemaAxion.FUENTE_SANS, 16, "bold")).pack(anchor="w")
        if subtitulo:
            tk.Label(parent, text=subtitulo, bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO,
                     wraplength=760, justify="left", font=(TemaAxion.FUENTE_SANS, 11)).pack(
                         anchor="w", pady=(3, 0))

    def _separador(self, parent, pady=16):
        tk.Frame(parent, bg=TemaAxion.LINEA, height=1).pack(fill="x", pady=pady)

    def renderizar_resultado(self):
        resultado = self.resultado
        self.aplicacion._result_layout_mode = (
            "compacto" if self.aplicacion.raiz.winfo_width() < 1200 else "amplio"
        )
        area = self.pestana_resultado.contenido
        limpiar_hijos(area)
        panel_principal = tk.Frame(area, bg=TemaAxion.PAPEL)
        panel_principal.pack(fill="both", expand=True, padx=24, pady=20)
        etiquetas = {
            "unica": ("Sistema consistente determinado", "Solución única", TemaAxion.VERDE_AZULADO, TemaAxion.VERDE_AZULADO_PALIDO),
            "infinitas": ("Sistema consistente indeterminado", "Infinitas soluciones", TemaAxion.INDIGO, TemaAxion.INDIGO_PALIDO),
            "inconsistente": ("Sistema inconsistente", "No existe solución", TemaAxion.ROJO, TemaAxion.ROJO_PALIDO),
        }
        clasificacion, encabezado, color, palido = etiquetas[resultado.clasificacion]
        tk.Label(panel_principal, text=clasificacion, bg=palido, fg=color, anchor="w",
                 padx=14, pady=8, font=(TemaAxion.FUENTE_SANS, 10, "bold")).pack(fill="x")
        tk.Label(panel_principal, text=encabezado, bg=TemaAxion.PAPEL, fg=color, anchor="w",
                 font=(TemaAxion.FUENTE_SANS, 22, "bold")).pack(fill="x", pady=(14, 6))
        texto_solucion = self._texto_solucion()
        envoltura_contenido = max(460, min(1100, self.aplicacion.raiz.winfo_width() - 260))
        tk.Label(panel_principal, text=texto_solucion, bg=TemaAxion.PAPEL, fg=TemaAxion.TINTA,
                 justify="left", anchor="w", wraplength=envoltura_contenido,
                 font=(TemaAxion.FUENTE_MONO, 15, "bold")).pack(fill="x")
        tk.Label(panel_principal, text=resultado.conclusion, bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO,
                 justify="left", anchor="w", wraplength=envoltura_contenido,
                 font=(TemaAxion.FUENTE_SANS, 10)).pack(fill="x", pady=(10, 0))
        self._separador(panel_principal)
        metodo = "Gauss-Jordan" if resultado.metodo_usado == "gauss-jordan" else "Eliminación de Gauss"
        self._titulo_seccion(panel_principal, "Lectura estructural", f"Método utilizado: {metodo}")
        tecnica = (
            f"Rango(A)  {resultado.rango_a}     Rango([A|b])  {resultado.rango_aumentada}     "
            f"Pivotes de A  {self._pivotes()}\n"
            f"Pivotes de [A|b]  {self._pivotes_aumentada()}\n"
            f"Variables básicas  {self._variables(resultado.variables_basicas)}     "
            f"Variables libres  "
            f"{'No aplica en un sistema inconsistente' if resultado.clasificacion == 'inconsistente' else self._variables(resultado.variables_libres)}"
        )
        tk.Label(panel_principal, text=tecnica, bg=TemaAxion.PAPEL_ALTERNO, fg=TemaAxion.TINTA,
                 justify="left", anchor="w", wraplength=envoltura_contenido,
                 padx=14, pady=10,
                 font=(TemaAxion.FUENTE_MONO, 11)).pack(fill="x", pady=(8, 0))
        self._separador(panel_principal)
        etiqueta_final = "RREF final" if resultado.metodo_usado == "gauss-jordan" else "Forma escalonada final"
        self._titulo_seccion(panel_principal, etiqueta_final, "Matriz empleada para interpretar la solución.")
        self.visor_matriz_final = AreaDesplazableAxion(
            panel_principal, background=TemaAxion.PAPEL, horizontal=True, vertical=False,
        )
        matriz_final = VistaMatrizAxion(
            self.visor_matriz_final.contenido, resultado.matriz_final,
            modo=self.aplicacion.modo_visualizacion.get(), precision=self.aplicacion.precision.get(),
        )
        matriz_final.pack(anchor="center")
        matriz_final.update_idletasks()
        self.visor_matriz_final.configure(height=matriz_final.winfo_reqheight() + 18)
        self.visor_matriz_final.pack(fill="x", pady=(9, 0))
        self.visor_matriz_final.pack_propagate(False)
        acciones = tk.Frame(panel_principal, bg=TemaAxion.PAPEL)
        acciones.pack(fill="x", pady=(18, 0))
        especificaciones_acciones = (
            ("Copiar resultado", self.copiar_resultado, False),
            ("Ver verificación", lambda: self.pestanas.select(self.pestana_verificacion), False),
            ("Volver al procedimiento", lambda: self.aplicacion.mostrar_etapa("resolver"), False),
            ("Editar una copia", self.aplicacion.editar_copia_resultado, False),
            ("Nuevo sistema", self.aplicacion.nuevo_ejercicio, False),
            ("Guardar reporte", self.guardar_reporte, True),
        )
        if self.aplicacion.raiz.winfo_width() < 1200:
            for column in range(3):
                acciones.grid_columnconfigure(column, weight=1, uniform="result_actions")
            for index, (text, command, principal) in enumerate(especificaciones_acciones):
                self._boton_accion(acciones, text, command, principal).grid(
                    row=index // 3, column=index % 3, sticky="ew", padx=4, pady=4,
                )
        else:
            for index, (text, command, principal) in enumerate(especificaciones_acciones):
                self._boton_accion(acciones, text, command, principal).pack(
                    side="left", padx=(0 if index == 0 else 8, 0),
                )

    def _texto_solucion(self):
        resultado = self.resultado
        modo, precision = self.aplicacion.modo_visualizacion.get(), self.aplicacion.precision.get()
        if resultado.solucion_unica is not None:
            return "     ".join(
                f"x{VistaMatrizAxion._subindice(i + 1)} = {formatear_numero(value, modo, precision)}"
                for i, value in enumerate(resultado.solucion_unica)
            )
        if resultado.clasificacion == "infinitas":
            lineas = lineas_parametricas(resultado, modo, precision)
            if self.aplicacion.modo_uso.get() == "guiado":
                lineas.extend(["", "Forma vectorial:", texto_forma_vectorial(resultado, modo, precision)])
            return "\n".join(lineas)
        contradiccion = formatear_numero(resultado.fila_contradiccion[-1], modo, precision)
        return f"0 = {contradiccion}   ← contradicción"

    def _variables(self, columns):
        return " · ".join(f"x{VistaMatrizAxion._subindice(column + 1)}" for column in columns) or "∅"

    def _pivotes(self):
        return " · ".join(
            f"F{row + 1}C{column + 1}" for row, column in self.resultado.posiciones_pivote
        ) or "∅"

    def _pivotes_aumentada(self):
        return " · ".join(
            f"F{row + 1}–{'b' if column == self.resultado.variables else f'C{column + 1}'}"
            for row, column in self.resultado.posiciones_pivote_aumentada
        ) or "∅"

    def _boton_accion(self, parent, text, command, principal=False):
        return tk.Button(
            parent, text=text, command=command, relief="flat", cursor="hand2",
            bg=TemaAxion.INDIGO if principal else TemaAxion.INDIGO_PALIDO,
            fg="white" if principal else TemaAxion.INDIGO,
            activebackground="#254C79" if principal else "#DDE8F3",
            activeforeground="white" if principal else TemaAxion.INDIGO,
            disabledforeground=TemaAxion.ATENUADO,
            padx=12, pady=8, font=(TemaAxion.FUENTE_SANS, 10, "bold")
        )

    def renderizar_procedimiento(self):
        if self.resultado:
            self.aplicacion._procedure_layout_key = self._usa_distribucion_ancha_paso(
                self.resultado.pasos[self.paso_activo]
            )
        limpiar_hijos(self.pestana_procedimiento)
        barra_herramientas = tk.Frame(self.pestana_procedimiento, bg=TemaAxion.PAPEL)
        barra_herramientas.pack(fill="x", padx=20, pady=(16, 8))
        tk.Label(barra_herramientas, text="Explorar procedimiento", bg=TemaAxion.PAPEL,
                 fg=TemaAxion.TINTA, font=(TemaAxion.FUENTE_SANS, 16, "bold")).pack(side="left")
        self._boton_accion(barra_herramientas, "Vista completa" if not self.vista_completa else "Paso a paso",
                            self.alternar_vista_completa).pack(side="right")
        self._boton_accion(barra_herramientas, "Copiar procedimiento", self.copiar_procedimiento).pack(
            side="right", padx=(0, 8))
        if self.vista_completa:
            self._renderizar_procedimiento_completo()
        else:
            self._renderizar_vista_paso()

    def _renderizar_vista_paso(self):
        resultado = self.resultado
        paso = resultado.pasos[self.paso_activo]
        navegacion = tk.Frame(self.pestana_procedimiento, bg=TemaAxion.PAPEL_ALTERNO,
                              highlightthickness=1, highlightbackground=TemaAxion.LINEA)
        navegacion.pack(fill="x", padx=20, pady=(0, 10))
        boton_anterior = self._boton_accion(
            navegacion, "← Paso anterior", lambda: self.cambiar_paso(-1)
        )
        boton_anterior.configure(state="disabled" if self.paso_activo == 0 else "normal")
        boton_anterior.pack(side="left", padx=10, pady=8)
        tk.Label(navegacion, text=f"Paso {self.paso_activo + 1:02d} de {len(resultado.pasos):02d}",
                 bg=TemaAxion.PAPEL_ALTERNO, fg=TemaAxion.TINTA,
                 font=(TemaAxion.FUENTE_SANS, 11, "bold")).pack(side="left", expand=True)
        self._boton_accion(navegacion, "Ir al resultado",
                            lambda: self.aplicacion.mostrar_etapa("interpretar")).pack(side="right", padx=4, pady=8)
        boton_siguiente = self._boton_accion(
            navegacion, "Paso siguiente →", lambda: self.cambiar_paso(1)
        )
        boton_siguiente.configure(
            state="disabled" if self.paso_activo == len(resultado.pasos) - 1 else "normal"
        )
        boton_siguiente.pack(side="right", padx=(4, 10), pady=8)

        contenido = tk.Frame(self.pestana_procedimiento, bg=TemaAxion.PAPEL)
        contenido.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        ancha = self._usa_distribucion_ancha_paso(paso)
        titulos = [f"{index + 1:02d}  {paso.titulo}" for index, paso in enumerate(resultado.pasos)]
        if ancha:
            barra_lateral = tk.Frame(contenido, bg=TemaAxion.PAPEL_ALTERNO, width=270,
                               highlightthickness=1, highlightbackground=TemaAxion.LINEA)
            barra_lateral.pack(side="left", fill="y", padx=(0, 14))
            barra_lateral.pack_propagate(False)
            tk.Label(barra_lateral, text="Línea de reducción", bg=TemaAxion.PAPEL_ALTERNO,
                     fg=TemaAxion.TINTA, font=(TemaAxion.FUENTE_SANS, 12, "bold")).pack(
                         anchor="w", padx=12, pady=(12, 7))
            lista_visual = tk.Listbox(barra_lateral, activestyle="dotbox", exportselection=False,
                                 selectmode="browse", relief="flat", bd=0,
                                 bg=TemaAxion.PAPEL_ALTERNO, fg=TemaAxion.TINTA,
                                 selectbackground=TemaAxion.INDIGO,
                                 selectforeground="white", font=(TemaAxion.FUENTE_SANS, 10))
            lista_visual.pack(fill="both", expand=True, padx=8, pady=(0, 8))
            for title in titulos:
                lista_visual.insert("end", title)
            lista_visual.selection_set(self.paso_activo)
            lista_visual.see(self.paso_activo)
            lista_visual.bind("<<ListboxSelect>>", lambda _e: (
                self.seleccionar_paso(lista_visual.curselection()[0]) if lista_visual.curselection() else None))
        else:
            selector = ttk.Combobox(contenido, state="readonly", values=titulos,
                                    font=(TemaAxion.FUENTE_SANS, 11))
            selector.current(self.paso_activo)
            selector.pack(fill="x", pady=(0, 10))
            selector.bind("<<ComboboxSelected>>", lambda _e: self.seleccionar_paso(selector.current()))

        area_paso = AreaDesplazableAxion(contenido)
        area_paso.pack(side="left" if ancha else "top", fill="both", expand=True)
        self._renderizar_contenido_paso(area_paso.contenido, resultado.pasos[self.paso_activo])

    def _ancho_estimado_matriz(self, paso: PasoFila):
        anchos_columnas = []
        for column in range(len(paso.matriz_antes[0])):
            mas_larga = max(len(numero_compacto(row[column], self.aplicacion.modo_visualizacion.get(),
                                             self.aplicacion.precision.get()))
                          for row in paso.matriz_antes + paso.matriz_despues)
            anchos_columnas.append(max(64, (mas_larga + 3) * 9))
        return 150 + sum(anchos_columnas)

    def _usa_distribucion_ancha_paso(self, paso: PasoFila, ancho_ventana=None):
        width = ancho_ventana if ancho_ventana is not None else self.aplicacion.raiz.winfo_width()
        ancho_disponible = width - 360
        return width >= 1150 and (
            2 * self._ancho_estimado_matriz(paso) + 56
        ) <= ancho_disponible

    def _renderizar_contenido_paso(self, parent, paso: PasoFila):
        superior = tk.Frame(parent, bg=TemaAxion.PAPEL)
        superior.pack(fill="x", pady=(4, 0))
        tk.Label(superior, text=f"PASO {paso.indice:02d}", bg=TemaAxion.PAPEL,
                 fg=TemaAxion.INDIGO, font=(TemaAxion.FUENTE_SANS, 11, "bold")).pack(anchor="w")
        tk.Label(superior, text=paso.titulo, bg=TemaAxion.PAPEL, fg=TemaAxion.TINTA,
                 font=(TemaAxion.FUENTE_SANS, 17, "bold")).pack(anchor="w", pady=(2, 5))
        tk.Label(superior, text=paso.objetivo, bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO,
                 wraplength=820, justify="left", font=(TemaAxion.FUENTE_SANS, 12)).pack(anchor="w")
        operacion = tk.Label(
            superior, text=paso.notacion_operacion, bg=TemaAxion.INDIGO_PALIDO,
            fg=TemaAxion.INDIGO, padx=14, pady=9, font=(TemaAxion.FUENTE_MONO, 12, "bold")
        )
        operacion.pack(anchor="w", pady=(12, 8))
        tk.Label(superior, text=paso.explicacion_breve, bg=TemaAxion.PAPEL, fg=TemaAxion.TINTA,
                 wraplength=840, justify="left", font=(TemaAxion.FUENTE_SANS, 12)).pack(anchor="w")
        if self.aplicacion.modo_uso.get() == "guiado":
            paso_calculo = paso.tipo_operacion in {"scale", "replace"}
            texto_abrir = "Ver cálculo de esta fila" if paso_calculo else "Ver explicación completa"
            texto_cerrar = "Ocultar cálculo de esta fila" if paso_calculo else "Ocultar explicación completa"
            boton_detalle = self._boton_accion(
                superior, texto_cerrar if self.mostrar_formal else texto_abrir,
                self.alternar_explicacion_formal,
            )
            boton_detalle.pack(anchor="w", pady=(8, 0))
            if self.mostrar_formal:
                tk.Label(superior, text=paso.explicacion_formal, bg=TemaAxion.PAPEL_ALTERNO,
                         fg=TemaAxion.ATENUADO, padx=12, pady=9, wraplength=700,
                         justify="left", font=(TemaAxion.FUENTE_SANS, 11)).pack(fill="x", pady=(6, 0))
        self._separador(parent, 12)
        comparador = tk.Frame(parent, bg=TemaAxion.PAPEL)
        comparador.pack(fill="x")
        ancha = self._usa_distribucion_ancha_paso(paso)
        comparador.grid_columnconfigure(0, weight=1)
        if ancha:
            comparador.grid_columnconfigure(2, weight=1)
        antes = tk.Frame(
            comparador, bg=TemaAxion.PAPEL_ALTERNO, padx=14, pady=10,
            highlightthickness=1, highlightbackground=TemaAxion.LINEA,
        )
        antes.grid(row=0, column=0, sticky="nsew")
        tk.Label(antes, text="ANTES", bg=TemaAxion.PAPEL_ALTERNO, fg=TemaAxion.ATENUADO,
                 font=(TemaAxion.FUENTE_SANS, 10, "bold")).pack(anchor="w")
        visor_antes = AreaDesplazableAxion(
            antes, background=TemaAxion.PAPEL_ALTERNO, horizontal=True, vertical=False,
        )
        visor_antes.configure(height=min(350, 60 + len(paso.matriz_antes) * 36))
        visor_antes.pack(fill="x", pady=(5, 0))
        visor_antes.pack_propagate(False)
        VistaMatrizAxion(
            visor_antes.contenido, paso.matriz_antes, modo=self.aplicacion.modo_visualizacion.get(),
            precision=self.aplicacion.precision.get(), fila_origen=paso.fila_origen,
            fila_destino=paso.fila_destino, pivote=paso.posicion_pivote, compacta=True,
            background=TemaAxion.PAPEL_ALTERNO,
        ).pack(anchor="center")
        tk.Label(comparador, text="→" if ancha else "↓", bg=TemaAxion.PAPEL, fg=TemaAxion.INDIGO,
                 font=(TemaAxion.FUENTE_SANS, 20, "bold")).grid(
                     row=0 if ancha else 1, column=1 if ancha else 0,
                     padx=12 if ancha else 0, pady=8 if not ancha else 0, sticky="w" if not ancha else "")
        despues = tk.Frame(
            comparador, bg=TemaAxion.PAPEL_ALTERNO, padx=14, pady=10,
            highlightthickness=1, highlightbackground=TemaAxion.LINEA,
        )
        despues.grid(row=0 if ancha else 2, column=2 if ancha else 0,
                   sticky="nsew")
        tk.Label(despues, text="DESPUÉS", bg=TemaAxion.PAPEL_ALTERNO, fg=TemaAxion.ATENUADO,
                 font=(TemaAxion.FUENTE_SANS, 10, "bold")).pack(anchor="w")
        modificadas = {(celda.fila, celda.columna) for celda in paso.celdas_modificadas}
        visor_despues = AreaDesplazableAxion(
            despues, background=TemaAxion.PAPEL_ALTERNO, horizontal=True, vertical=False,
        )
        visor_despues.configure(height=min(350, 60 + len(paso.matriz_despues) * 36))
        visor_despues.pack(fill="x", pady=(5, 0))
        visor_despues.pack_propagate(False)
        VistaMatrizAxion(
            visor_despues.contenido, paso.matriz_despues, modo=self.aplicacion.modo_visualizacion.get(),
            precision=self.aplicacion.precision.get(), fila_origen=paso.fila_origen,
            fila_destino=paso.fila_destino, pivote=paso.posicion_pivote, modificadas=modificadas,
            compacta=True, background=TemaAxion.PAPEL_ALTERNO,
        ).pack(anchor="center")
        if paso.celdas_modificadas and self.aplicacion.modo_uso.get() == "guiado":
            self._separador(parent, 12)
            self._titulo_seccion(parent, "Valores modificados")
            cambios = "     ".join(
                f"F{celda.fila + 1}C{celda.columna + 1}: "
                f"{formatear_numero(celda.antes, self.aplicacion.modo_visualizacion.get(), self.aplicacion.precision.get())} → "
                f"{formatear_numero(celda.despues, self.aplicacion.modo_visualizacion.get(), self.aplicacion.precision.get())}"
                for celda in paso.celdas_modificadas
            )
            tk.Label(parent, text=cambios, bg=TemaAxion.PAPEL, fg=TemaAxion.AMBAR,
                     wraplength=max(520, min(1000, self.aplicacion.raiz.winfo_width() - 430)),
                     justify="left", font=(TemaAxion.FUENTE_MONO, 10, "bold")).pack(anchor="w")

    def _renderizar_procedimiento_completo(self):
        desplazamiento = AreaDesplazableAxion(self.pestana_procedimiento)
        desplazamiento.pack(fill="both", expand=True, padx=20, pady=(0, 18))
        for index, paso in enumerate(self.resultado.pasos):
            seccion = tk.Frame(desplazamiento.contenido, bg=TemaAxion.PAPEL)
            seccion.pack(fill="x", pady=(8, 16))
            self._renderizar_contenido_paso(seccion, paso)
            if index < len(self.resultado.pasos) - 1:
                self._separador(desplazamiento.contenido, 4)

    def seleccionar_paso(self, index):
        self.paso_activo = max(0, min(index, len(self.resultado.pasos) - 1))
        self.renderizar_procedimiento()

    def cambiar_paso(self, delta):
        self.seleccionar_paso(self.paso_activo + delta)

    def alternar_vista_completa(self):
        self.vista_completa = not self.vista_completa
        self.renderizar_procedimiento()

    def alternar_explicacion_formal(self):
        self.mostrar_formal = not self.mostrar_formal
        self.renderizar_procedimiento()

    def copiar_procedimiento(self):
        modo, precision = self.aplicacion.modo_visualizacion.get(), self.aplicacion.precision.get()
        bloques = []
        for paso in self.resultado.pasos:
            bloques.append(
                f"PASO {paso.indice:02d} — {paso.titulo}\n"
                f"Objetivo: {paso.objetivo}\n"
                f"Operación: {paso.notacion_operacion}\n"
                f"{paso.explicacion_breve}\n\n"
                f"Antes:\n{texto_matriz(paso.matriz_antes, modo, precision)}\n\n"
                f"Después:\n{texto_matriz(paso.matriz_despues, modo, precision)}"
            )
        self.copiar_texto(
            "\n\n" + ("\n\n" + "─" * 56 + "\n\n").join(bloques),
            "Procedimiento copiado al portapapeles.",
        )

    @staticmethod
    def _expresion_con_signo(elementos):
        """Une términos conservando el signo, sin producir secuencias como '+ -1'."""
        expresion = ""
        for valor_signo, text in elementos:
            negativo = valor_signo < 0
            limpio = text[1:] if text.startswith("-") else text
            if not expresion:
                expresion = ("−" if negativo else "") + limpio
            else:
                expresion += (" − " if negativo else " + ") + limpio
        return expresion or "0"

    def renderizar_verificacion(self):
        resultado = self.resultado
        area = self.pestana_verificacion.contenido
        limpiar_hijos(area)
        panel_principal = tk.Frame(area, bg=TemaAxion.PAPEL)
        panel_principal.pack(fill="both", expand=True, padx=24, pady=20)
        self._titulo_seccion(
            panel_principal, "Verificación sobre el sistema original",
            "La comprobación utiliza exactamente las ecuaciones introducidas, no la matriz transformada."
        )
        self._separador(panel_principal, 12)
        modo, precision = self.aplicacion.modo_visualizacion.get(), self.aplicacion.precision.get()
        envoltura_verificacion = max(460, min(1050, self.aplicacion.raiz.winfo_width() - 240))
        if resultado.solucion_unica is not None:
            for elemento in resultado.verificacion:
                bloque = tk.Frame(panel_principal, bg=TemaAxion.PAPEL)
                bloque.pack(fill="x", pady=(0, 14))
                tk.Label(bloque, text=f"Ecuación {elemento.indice_ecuacion + 1}",
                         bg=TemaAxion.PAPEL, fg=TemaAxion.INDIGO,
                         font=(TemaAxion.FUENTE_SANS, 10, "bold")).pack(anchor="w")
                original = texto_ecuacion(resultado.original[elemento.indice_ecuacion], modo, precision)
                tk.Label(bloque, text=original, bg=TemaAxion.PAPEL, fg=TemaAxion.TINTA,
                         wraplength=envoltura_verificacion, justify="left",
                         font=(TemaAxion.FUENTE_MONO, 12, "bold")).pack(anchor="w", pady=(3, 5))
                if self.aplicacion.modo_uso.get() == "guiado":
                    sustituciones = []
                    for coeficiente, solucion in zip(elemento.coeficientes, resultado.solucion_unica):
                        magnitud = abs(coeficiente)
                        sustituciones.append((
                            coeficiente,
                            f"{numero_compacto(magnitud, modo, precision)}"
                            f"({numero_compacto(solucion, modo, precision)})",
                        ))
                    tk.Label(bloque, text="Sustitución:  " + self._expresion_con_signo(sustituciones),
                              bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO,
                              wraplength=envoltura_verificacion, justify="left",
                              font=(TemaAxion.FUENTE_SANS, 11)).pack(anchor="w")
                    simplificada = [
                        (termino, numero_compacto(abs(termino), modo, precision))
                        for termino in elemento.terminos_sustituidos
                    ]
                    tk.Label(bloque, text="Simplificación:  " + self._expresion_con_signo(simplificada),
                        bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO,
                        wraplength=envoltura_verificacion, justify="left",
                        font=(TemaAxion.FUENTE_SANS, 11)).pack(anchor="w")
                tk.Label(
                    bloque,
                    text=(f"Resultado:  {formatear_numero(elemento.valor_izquierdo, modo, precision)} = "
                          f"{formatear_numero(elemento.lado_derecho, modo, precision)}  "
                          f"· Diferencia exacta: {formatear_numero(elemento.diferencia, modo, precision)}  "
                          f"{'✓ Correcto' if elemento.valida else '✕ Incorrecto'}"),
                    bg=TemaAxion.VERDE_AZULADO_PALIDO if elemento.valida else TemaAxion.ROJO_PALIDO,
                    fg=TemaAxion.VERDE_AZULADO if elemento.valida else TemaAxion.ROJO,
                    wraplength=envoltura_verificacion, justify="left",
                    padx=10, pady=6, font=(TemaAxion.FUENTE_SANS, 10, "bold")
                ).pack(anchor="w", pady=(6, 0))
        elif resultado.clasificacion == "infinitas":
            particular_valida = resultado.verificacion_particular is True
            direcciones_validas = resultado.verificacion_direcciones is True
            todo_valido = particular_valida and direcciones_validas
            tk.Label(panel_principal, text="Comprobación de la familia paramétrica",
                     bg=TemaAxion.PAPEL, fg=TemaAxion.INDIGO,
                     font=(TemaAxion.FUENTE_SANS, 12, "bold")).pack(anchor="w")
            tk.Label(panel_principal, text=(f"A·x₀ = b  {'✓' if particular_valida else '✕'}\n"
                                  f"A·vₖ = 0  {'✓' if direcciones_validas else '✕'}\n\nLa solución particular satisface "
                                  "el sistema y cada vector de dirección pertenece al espacio nulo. "
                                  "Por tanto, cualquier valor real de los parámetros produce una solución."),
                     bg=TemaAxion.VERDE_AZULADO_PALIDO if todo_valido else TemaAxion.ROJO_PALIDO,
                     fg=TemaAxion.VERDE_AZULADO if todo_valido else TemaAxion.ROJO, justify="left",
                     wraplength=envoltura_verificacion, padx=14, pady=12,
                     font=(TemaAxion.FUENTE_SANS, 10)).pack(fill="x", pady=(9, 0))
        else:
            contradiccion = formatear_numero(resultado.fila_contradiccion[-1], modo, precision)
            tk.Label(panel_principal, text="Fila contradictoria", bg=TemaAxion.PAPEL,
                     fg=TemaAxion.ROJO, font=(TemaAxion.FUENTE_SANS, 12, "bold")).pack(anchor="w")
            tk.Label(panel_principal, text=f"0 = {contradiccion}", bg=TemaAxion.ROJO_PALIDO,
                     fg=TemaAxion.ROJO, padx=14, pady=9,
                     font=(TemaAxion.FUENTE_MONO, 16, "bold")).pack(anchor="w", pady=(8, 5))
            tk.Label(panel_principal, text=("Esta igualdad es imposible. Por eso rango(A) < rango([A|b]) "
                                 "y no existe un conjunto de valores que satisfaga todas las ecuaciones."),
                     bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO, wraplength=envoltura_verificacion,
                     justify="left", font=(TemaAxion.FUENTE_SANS, 10)).pack(anchor="w")

    def renderizar_reporte(self):
        limpiar_hijos(self.pestana_reporte)
        barra_herramientas = tk.Frame(self.pestana_reporte, bg=TemaAxion.PAPEL)
        barra_herramientas.pack(fill="x", padx=18, pady=(16, 8))
        tk.Label(barra_herramientas, text="Reporte completo del ejercicio", bg=TemaAxion.PAPEL,
                 fg=TemaAxion.TINTA, font=(TemaAxion.FUENTE_SANS, 16, "bold")).pack(anchor="w")
        acciones_reporte = tk.Frame(barra_herramientas, bg=TemaAxion.PAPEL)
        acciones_reporte.pack(fill="x", pady=(10, 0))
        self._boton_accion(acciones_reporte, "Copiar reporte", self.copiar_reporte).pack(side="left")
        self._boton_accion(acciones_reporte, "Abrir reporte para imprimir",
                            self.abrir_reporte_para_imprimir).pack(side="left", padx=8)
        self._boton_accion(acciones_reporte, "Guardar HTML", self.guardar_html).pack(side="left", padx=8)
        self._boton_accion(acciones_reporte, "Guardar TXT", self.guardar_reporte,
                            principal=True).pack(side="left", padx=8)
        marco = tk.Frame(self.pestana_reporte, bg=TemaAxion.PAPEL)
        marco.pack(fill="both", expand=True, padx=18, pady=(0, 18))
        desplazamiento = ttk.Scrollbar(marco)
        desplazamiento.pack(side="right", fill="y")
        self.reporte_horizontal = ttk.Scrollbar(marco, orient="horizontal")
        self.reporte_horizontal.pack(side="bottom", fill="x")
        self.texto_reporte = tk.Text(
            marco, wrap="none", relief="flat", bg=TemaAxion.PAPEL_ALTERNO,
            fg=TemaAxion.TINTA, padx=14, pady=12, font=(TemaAxion.FUENTE_MONO, 11),
            yscrollcommand=desplazamiento.set, xscrollcommand=self.reporte_horizontal.set,
        )
        self.texto_reporte.pack(fill="both", expand=True)
        desplazamiento.configure(command=self.texto_reporte.yview)
        self.reporte_horizontal.configure(command=self.texto_reporte.xview)
        self.texto_reporte.insert("1.0", construir_reporte(
            self.resultado, self.aplicacion.modo_visualizacion.get(), self.aplicacion.precision.get()))
        self.texto_reporte.configure(state="disabled")

    def copiar_texto(self, text, mensaje):
        self.clipboard_clear()
        self.clipboard_append(text)
        self.update()
        self.aplicacion.establecer_estado(mensaje, "listo")

    def copiar_resultado(self):
        self.copiar_texto(self._texto_solucion(), "Resultado copiado al portapapeles.")

    def copiar_reporte(self):
        self.copiar_texto(construir_reporte(
            self.resultado, self.aplicacion.modo_visualizacion.get(), self.aplicacion.precision.get()),
            "Reporte completo copiado al portapapeles.")

    def guardar_reporte(self):
        ruta = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(), title="Guardar reporte de AXION",
            defaultextension=".txt", filetypes=(("Documento de texto", "*.txt"),),
            initialfile=f"AXION_{datetime.now():%Y%m%d_%H%M}.txt",
        )
        if not ruta:
            return
        try:
            Path(ruta).write_text(construir_reporte(
                self.resultado, self.aplicacion.modo_visualizacion.get(), self.aplicacion.precision.get()), encoding="utf-8")
        except OSError as error:
            self.aplicacion.establecer_estado(f"No se pudo guardar el reporte: {error}", "error")
            return
        self.aplicacion.establecer_estado("Reporte guardado correctamente.", "listo")

    def guardar_html(self):
        ruta = filedialog.asksaveasfilename(
            parent=self.winfo_toplevel(), title="Guardar reporte HTML de AXION",
            defaultextension=".html", filetypes=(("Documento HTML", "*.html"),),
            initialfile=f"AXION_Programa2_{datetime.now():%Y%m%d_%H%M}.html",
        )
        if not ruta:
            return
        try:
            Path(ruta).write_text(construir_reporte_html(
                self.resultado, self.aplicacion.modo_visualizacion.get(), self.aplicacion.precision.get()), encoding="utf-8")
        except OSError as error:
            self.aplicacion.establecer_estado(f"No se pudo guardar el HTML: {error}", "error")
            return
        self.aplicacion.establecer_estado("Reporte HTML guardado correctamente.", "listo")

    def abrir_reporte_para_imprimir(self):
        try:
            with tempfile.NamedTemporaryFile(
                    "w", encoding="utf-8", suffix=".html", delete=False) as archivo:
                archivo.write(construir_reporte_html(
                    self.resultado, self.aplicacion.modo_visualizacion.get(), self.aplicacion.precision.get()))
                ruta = Path(archivo.name)
            abierto = webbrowser.open(ruta.as_uri())
        except OSError as error:
            self.aplicacion.establecer_estado(f"No se pudo preparar el reporte para imprimir: {error}", "error")
            return
        if abierto:
            self.aplicacion.establecer_estado(
                "Reporte abierto para imprimir; el PDF se crea desde el navegador.", "listo")
        else:
            self.aplicacion.establecer_estado(
                f"No se encontró un navegador. El reporte temporal está en: {ruta}", "error")


class AplicacionAxion:
    def __init__(self, raiz, almacen_historial=None):
        self.raiz = raiz
        self.raiz.title("AXION | Programa 2 · Gauss-Jordan")
        ancho_pantalla = self.raiz.winfo_screenwidth()
        alto_pantalla = self.raiz.winfo_screenheight()
        ancho_minimo = min(820, max(640, ancho_pantalla - 80))
        alto_minimo = min(620, max(520, alto_pantalla - 100))
        ancho_inicial = max(ancho_minimo, min(1280, ancho_pantalla - 40))
        alto_inicial = max(alto_minimo, min(800, alto_pantalla - 80))
        self.raiz.geometry(f"{ancho_inicial}x{alto_inicial}")
        self.raiz.minsize(ancho_minimo, alto_minimo)
        self.raiz.configure(bg=TemaAxion.LIENZO)
        self.resultado: ResultadoCalculo | None = None
        self.modo_uso = tk.StringVar(value="guiado")
        self.modo_visualizacion = tk.StringVar(value="fracciones")
        self.precision = tk.IntVar(value=4)
        self._layout_mode = None
        self._procedure_layout_key = None
        self._result_layout_mode = None
        self.etapa_actual = "definir"
        self.resultado_desactualizado = False
        self.historial = almacen_historial if almacen_historial is not None else AlmacenHistorial()
        self._construir_estructura()
        if self.historial.ultimo_error:
            self.establecer_estado(self.historial.ultimo_error + " Se iniciará un historial nuevo en memoria.", "error")
        self.raiz.bind("<Control-Return>", lambda _e: self.resolver())
        self.raiz.bind("<Control-z>", lambda _e: (self.editor.deshacer(), "break")[1])
        self.raiz.bind("<Control-Z>", lambda _e: (self.editor.deshacer(), "break")[1])
        self.raiz.bind("<Configure>", self._distribucion_adaptable)
        self.raiz.bind_all("<MouseWheel>", self._dirigir_rueda_raton, add="+")
        self.raiz.bind("<Alt-Left>", lambda _e: self._atajo_paso(-1))
        self.raiz.bind("<Alt-Right>", lambda _e: self._atajo_paso(1))
        self.raiz.bind("<Control-s>", lambda _e: self.cuaderno.guardar_reporte() if self.resultado else None)

    def _construir_estructura(self):
        self.raiz.grid_rowconfigure(2, weight=1)
        self.raiz.grid_columnconfigure(0, weight=1)
        cabecera = tk.Frame(self.raiz, bg=TemaAxion.AZUL_MARINO, height=62)
        cabecera.grid(row=0, column=0, sticky="ew")
        cabecera.grid_propagate(False)
        marca = tk.Frame(cabecera, bg=TemaAxion.AZUL_MARINO)
        marca.pack(side="left", padx=24, pady=8)
        tk.Label(marca, text="AXION", bg=TemaAxion.AZUL_MARINO, fg="white",
                 font=(TemaAxion.FUENTE_SANS, 20, "bold")).pack(anchor="w")
        tk.Label(marca, text="Álgebra lineal, paso a paso",
                 bg=TemaAxion.AZUL_MARINO, fg="#AEB9C9",
                 font=(TemaAxion.FUENTE_SANS, 11)).pack(anchor="w")
        herramientas = tk.Frame(cabecera, bg=TemaAxion.AZUL_MARINO)
        herramientas.pack(side="right", padx=20)
        self._header_button(herramientas, "Nuevo ejercicio", self.nuevo_ejercicio).pack(side="left", padx=3)
        self._header_button(herramientas, "Historial", self.mostrar_historial).pack(side="left", padx=3)
        self._header_button(herramientas, "Ayuda", self.mostrar_ayuda).pack(side="left", padx=3)
        self.separador_motor = tk.Frame(herramientas, bg="#43506A", width=1, height=26)
        self.separador_motor.pack(side="left", padx=10)
        self.etiqueta_motor = tk.Label(
            herramientas, text="GAUSS-JORDAN · ARITMÉTICA EXACTA", bg=TemaAxion.AZUL_MARINO,
            fg="#DCE3EE", font=(TemaAxion.FUENTE_SANS, 10, "bold"))
        self.etiqueta_motor.pack(side="left")

        flujo_trabajo = tk.Frame(self.raiz, bg=TemaAxion.PAPEL,
                            highlightthickness=1, highlightbackground=TemaAxion.LINEA)
        flujo_trabajo.grid(row=1, column=0, sticky="ew")
        self.botones_etapas = {}
        etapas = (
            ("definir", "1. Definir sistema"),
            ("resolver", "2. Resolver paso a paso"),
            ("interpretar", "3. Interpretar y verificar"),
        )
        for clave, etiqueta in etapas:
            boton = tk.Button(
                flujo_trabajo, text=etiqueta, command=lambda etapa=clave: self.mostrar_etapa(etapa),
                relief="flat", bd=0, padx=22, pady=12, cursor="hand2",
                bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO,
                activebackground=TemaAxion.INDIGO_PALIDO,
                font=(TemaAxion.FUENTE_SANS, 11, "bold"),
            )
            boton.pack(side="left", fill="x", expand=True)
            self.botones_etapas[clave] = boton
        self.etiquetas_etapas = {clave: etiqueta for clave, etiqueta in etapas}

        controles = tk.Frame(self.raiz, bg=TemaAxion.PAPEL,
                            highlightthickness=1, highlightbackground=TemaAxion.LINEA)
        controles.grid(row=3, column=0, sticky="ew")
        self.etiqueta_estado = tk.Label(
            controles, text="Define las dimensiones e introduce los coeficientes para comenzar.",
            bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO, font=(TemaAxion.FUENTE_SANS, 10)
        )
        self.etiqueta_estado.pack(side="left", padx=20, pady=8)
        self.area_formato = tk.Frame(controles, bg=TemaAxion.PAPEL)
        self.area_formato.pack(side="right", padx=18, pady=8)
        self.etiqueta_formato = tk.Label(
            self.area_formato, text="Resultados exactos", bg=TemaAxion.PAPEL,
            fg=TemaAxion.ATENUADO, font=(TemaAxion.FUENTE_SANS, 10),
        )
        self.etiqueta_formato.pack(side="left", padx=(0, 5))
        for value, etiqueta in (("fracciones", "Fracciones"), ("decimales", "Decimales")):
            tk.Radiobutton(
                self.area_formato, text=etiqueta, value=value, variable=self.modo_visualizacion,
                command=self.actualizar_visualizacion, indicatoron=False, relief="flat",
                bg=TemaAxion.PAPEL_ALTERNO, fg=TemaAxion.INDIGO,
                selectcolor=TemaAxion.INDIGO_PALIDO, padx=8, pady=4,
                font=(TemaAxion.FUENTE_SANS, 10), cursor="hand2",
            ).pack(side="left", padx=2)
        self.etiqueta_precision = tk.Label(self.area_formato, text="Cifras", bg=TemaAxion.PAPEL,
                                        fg=TemaAxion.ATENUADO, font=(TemaAxion.FUENTE_SANS, 10))
        self.control_precision = tk.Spinbox(
            self.area_formato, from_=2, to=10, textvariable=self.precision, width=3,
            command=self.actualizar_visualizacion, justify="center", relief="solid", bd=1,
            bg=TemaAxion.PAPEL_ALTERNO, fg=TemaAxion.TINTA,
            buttonbackground=TemaAxion.INDIGO_PALIDO, font=(TemaAxion.FUENTE_SANS, 10),
        )
        self.control_precision.bind("<Return>", lambda _e: self.actualizar_visualizacion())
        self.control_precision.bind("<FocusOut>", lambda _e: self.actualizar_visualizacion())
        tk.Label(self.area_formato, text="Modo", bg=TemaAxion.PAPEL,
                 fg=TemaAxion.ATENUADO, font=(TemaAxion.FUENTE_SANS, 10)).pack(side="left", padx=(14, 5))
        for value, etiqueta in (("guiado", "Guiado"), ("rapido", "Rápido")):
            tk.Radiobutton(
                self.area_formato, text=etiqueta, value=value, variable=self.modo_uso,
                command=self.actualizar_visualizacion, indicatoron=False, relief="flat",
                bg=TemaAxion.PAPEL_ALTERNO, fg=TemaAxion.INDIGO,
                selectcolor=TemaAxion.INDIGO_PALIDO, padx=8, pady=4,
                font=(TemaAxion.FUENTE_SANS, 10), cursor="hand2",
            ).pack(side="left", padx=2)

        self.cuerpo = tk.Canvas(self.raiz, bg=TemaAxion.LIENZO, highlightthickness=0)
        self.cuerpo.grid(row=2, column=0, sticky="nsew")
        self.desplazamiento_cuerpo = BarraDesplazamientoAutomaticaAxion(
            self.raiz, orient="vertical", command=self.cuerpo.yview)
        self.desplazamiento_cuerpo.grid(row=2, column=0, sticky="nse")
        self.cuerpo.configure(yscrollcommand=self.desplazamiento_cuerpo.set)
        self.espacio_trabajo = tk.Frame(self.cuerpo, bg=TemaAxion.LIENZO)
        self.ventana_espacio_trabajo = self.cuerpo.create_window((0, 0), window=self.espacio_trabajo, anchor="nw")
        self.espacio_trabajo.bind("<Configure>", lambda _e: self.cuerpo.configure(
            scrollregion=self.cuerpo.bbox("all")))
        self.cuerpo.bind("<MouseWheel>", lambda e: self.cuerpo.yview_scroll(
            -1 if e.delta > 0 else 1, "units"))
        self.editor = EditorSistemaAxion(self.espacio_trabajo, self)
        self.cuaderno = CuadernoResolucionAxion(self.espacio_trabajo, self)
        self.mostrar_etapa("definir")
        self.raiz.bind("<F1>", lambda _e: self.mostrar_ayuda())

    def _header_button(self, parent, text, command):
        return tk.Button(parent, text=text, command=command, relief="flat",
                         bg=TemaAxion.AZUL_MARINO, fg="#DCE3EE", activebackground="#25324A",
                         activeforeground="white", padx=10, pady=7, cursor="hand2",
                         font=(TemaAxion.FUENTE_SANS, 10))

    def _distribucion_adaptable(self, event):
        if event.widget is not self.raiz:
            return
        modo = "estrecho" if event.width < 980 else "amplio"
        modo_anterior = self._layout_mode
        self._layout_mode = modo
        if modo == "estrecho":
            self.separador_motor.pack_forget()
            self.etiqueta_motor.pack_forget()
            corta = {"definir": "1. Definir", "resolver": "2. Resolver", "interpretar": "3. Interpretar"}
            for clave, boton in self.botones_etapas.items():
                boton.configure(text=corta[clave], padx=8)
            self.etiqueta_estado.pack_forget()
        else:
            if not self.separador_motor.winfo_manager():
                self.separador_motor.pack(side="left", padx=10)
                self.etiqueta_motor.pack(side="left")
            for clave, boton in self.botones_etapas.items():
                boton.configure(text=self.etiquetas_etapas[clave], padx=22)
            if not self.etiqueta_estado.winfo_manager():
                self.etiqueta_estado.pack(side="left", padx=20, pady=8)
        self.espacio_trabajo.grid_columnconfigure(0, weight=1)
        self.espacio_trabajo.grid_rowconfigure(0, weight=1)
        destino = self.editor if self.etapa_actual == "definir" else self.cuaderno
        destino.update_idletasks()
        self.cuerpo.itemconfigure(
            self.ventana_espacio_trabajo, width=max(1, event.width),
            height=max(520, event.height - 150, destino.winfo_reqheight() + 42),
        )
        if self.resultado:
            paso = self.resultado.pasos[self.cuaderno.paso_activo]
            clave_procedimiento = self.cuaderno._usa_distribucion_ancha_paso(paso, event.width)
            modo_resultado = "compacto" if event.width < 1200 else "amplio"
            procedimiento_cambio = (
                self._procedure_layout_key is not None
                and self._procedure_layout_key != clave_procedimiento
            )
            resultado_cambio = (
                self._result_layout_mode is not None
                and self._result_layout_mode != modo_resultado
            )
            self._procedure_layout_key = clave_procedimiento
            self._result_layout_mode = modo_resultado
            if self.etapa_actual == "resolver" and (procedimiento_cambio or modo_anterior != modo):
                self.cuaderno.renderizar_procedimiento()
            if resultado_cambio:
                self.cuaderno.renderizar_resultado()
                self.cuaderno.renderizar_verificacion()

    def _dirigir_rueda_raton(self, event):
        if event.widget.winfo_toplevel() is not self.raiz:
            return None
        current = event.widget
        while current is not None:
            if current in (self.editor.marco_matriz, self.editor.lienzo_matriz):
                inferior, superior_limite = self.editor.lienzo_matriz.yview()
                if inferior > 0.0 or superior_limite < 1.0:
                    self.editor.lienzo_matriz.yview_scroll(-3 if event.delta > 0 else 3, "units")
                    return "break"
            if isinstance(current, AreaDesplazableAxion) and current.vertical_habilitado:
                current.canvas.yview_scroll(-3 if event.delta > 0 else 3, "units")
                return "break"
            current = getattr(current, "master", None)
        self.cuerpo.yview_scroll(-3 if event.delta > 0 else 3, "units")
        return "break"

    def _atajo_paso(self, delta):
        if self.etapa_actual == "resolver" and self.resultado:
            self.cuaderno.cambiar_paso(delta)
        return "break"

    def mostrar_etapa(self, etapa):
        if etapa != "definir" and self.resultado is None:
            self.establecer_estado("Primero completa y resuelve un sistema.", "error")
            etapa = "definir"
        self.etapa_actual = etapa
        self.editor.grid_forget()
        self.cuaderno.grid_forget()
        destino = self.editor if etapa == "definir" else self.cuaderno
        destino.grid(row=0, column=0, sticky="nsew", padx=24, pady=18)
        self.raiz.update_idletasks()
        disponible = max(520, self.raiz.winfo_height() - 150)
        self.cuerpo.itemconfigure(
            self.ventana_espacio_trabajo, width=max(1, self.raiz.winfo_width()),
            height=max(disponible, destino.winfo_reqheight() + 42),
        )
        self.cuerpo.configure(scrollregion=self.cuerpo.bbox("all"))
        self.cuerpo.yview_moveto(0)
        if etapa == "resolver" and self.resultado:
            self.cuaderno.pestanas.select(self.cuaderno.pestana_procedimiento)
        elif etapa == "interpretar" and self.resultado:
            self.cuaderno.pestanas.select(self.cuaderno.pestana_resultado)
            self.cuaderno.pestana_resultado.canvas.yview_moveto(0)
        for clave, boton in self.botones_etapas.items():
            seleccionado = clave == etapa
            boton.configure(
                bg=TemaAxion.INDIGO if seleccionado else TemaAxion.PAPEL,
                fg="white" if seleccionado else TemaAxion.ATENUADO,
                relief="sunken" if seleccionado else "flat",
                state="normal" if clave == "definir" or self.resultado else "disabled",
            )

    def resolver(self):
        try:
            values = self.editor.obtener_valores()
        except ValueError as error:
            self.establecer_estado(str(error), "error")
            return
        self.establecer_estado("Analizando pivotes y operaciones…", "calculando")
        self.editor.boton_resolver.configure(state="disabled", text="Calculando…")
        self.raiz.update_idletasks()
        try:
            resultado = resolver_sistema(values, self.editor.clave_metodo())
        except Exception:
            self.establecer_estado("No fue posible completar el cálculo. Tus datos originales se conservaron.", "error")
            self.editor.boton_resolver.configure(state="normal", text="Resolver nuevamente")
            return
        self.resultado = resultado
        self.resultado_desactualizado = False
        self.editor.instantanea_original = [
            [formatear_numero(value) for value in row] for row in resultado.original
        ]
        self.editor.modificado = False
        self.editor.actualizar_estado()
        self.cuaderno.establecer_resultado(resultado)
        historial_guardado = self.historial.add(resultado)
        self.editor.boton_resolver.configure(
            state="normal",
            text=("Resolver con Gauss-Jordan" if self.editor.metodo.get() == "Gauss-Jordan"
                  else "Resolver con eliminación de Gauss"),
        )
        if historial_guardado:
            self.establecer_estado("Cálculo y verificación completados; ejercicio añadido al historial.", "resuelto")
        else:
            self.establecer_estado(self.historial.ultimo_error + " El resultado continúa disponible en memoria.", "error")
        if self.modo_uso.get() == "guiado":
            self.mostrar_etapa("resolver")
        else:
            self.mostrar_etapa("interpretar")

    def establecer_estado(self, text, state="inicial"):
        colores = {
            "inicial": TemaAxion.ATENUADO, "editando": TemaAxion.AMBAR,
            "listo": TemaAxion.VERDE_AZULADO, "calculando": TemaAxion.INDIGO,
            "resuelto": TemaAxion.VERDE_AZULADO, "error": TemaAxion.ROJO,
        }
        self.etiqueta_estado.configure(text=text, fg=colores.get(state, TemaAxion.ATENUADO))

    def marcar_edicion(self):
        if self.resultado:
            mismas_dimensiones = (
                len(self.editor.variables_celdas) == len(self.resultado.original)
                and len(self.editor.variables_celdas[0]) == len(self.resultado.original[0])
            )
            try:
                current = [
                    [a_fraccion(variable.get()) for variable in row]
                    for row in self.editor.variables_celdas
                ]
            except (ValueError, ZeroDivisionError):
                current = None
            mismo_metodo = self.editor.clave_metodo() == self.resultado.metodo_usado
            if mismas_dimensiones and current == self.resultado.original and mismo_metodo:
                self.resultado_desactualizado = False
                metodo = (
                    "Gauss-Jordan"
                    if self.resultado.metodo_usado == "gauss-jordan"
                    else "Eliminación de Gauss"
                )
                self.cuaderno.insignia_metodo.configure(
                    text=f"Método utilizado: {metodo}",
                    bg=TemaAxion.INDIGO_PALIDO, fg=TemaAxion.INDIGO,
                )
                self.establecer_estado(
                    "La entrada vuelve a coincidir con el sistema resuelto; el resultado está vigente.",
                    "resuelto",
                )
                return
            self.resultado_desactualizado = True
            self.cuaderno.insignia_metodo.configure(
                text="RESULTADO ANTERIOR · ENTRADA MODIFICADA",
                bg=TemaAxion.AMBAR_PALIDO, fg=TemaAxion.AMBAR,
            )
            self.establecer_estado("Entrada modificada: el resultado anterior se conserva. Vuelve a resolver.", "editando")

    def limpiar_resultado(self):
        self.resultado = None
        self.cuaderno.resultado = None
        self.cuaderno.insignia_metodo.configure(text="Sin resolver", bg=TemaAxion.PAPEL_ALTERNO,
                                              fg=TemaAxion.ATENUADO)
        self.cuaderno.renderizar_vacio()
        self.establecer_estado("Matriz limpia. Introduce todos los valores para continuar.", "inicial")

    def actualizar_visualizacion(self):
        try:
            precision = int(self.precision.get())
        except (tk.TclError, ValueError):
            precision = 4
        self.precision.set(max(2, min(10, precision)))
        if self.modo_visualizacion.get() == "decimales":
            self.etiqueta_formato.configure(text="Resultados aproximados (≈)")
            self.etiqueta_precision.pack(side="left", padx=(8, 3))
            self.control_precision.pack(side="left")
        else:
            self.etiqueta_formato.configure(text="Resultados exactos")
            self.etiqueta_precision.pack_forget()
            self.control_precision.pack_forget()
        if self.resultado:
            self.cuaderno.renderizar_todo()
        self.editor.actualizar_ecuaciones()

    def nuevo_ejercicio(self):
        if self.editor.modificado and any(
                variable.get().strip() for row in self.editor.variables_celdas for variable in row):
            if not messagebox.askyesno(
                    "Nuevo ejercicio",
                    "Hay valores que todavía no se han resuelto. ¿Deseas comenzar de nuevo?",
                    parent=self.raiz):
                return
        self.editor.reiniciar_nuevo()
        self.limpiar_resultado()
        self.establecer_estado("Nuevo ejercicio preparado. Completa la matriz para comenzar.", "inicial")
        self.mostrar_etapa("definir")

    def editar_copia_resultado(self):
        if not self.resultado:
            return
        self.editor.establecer_valores(self.resultado.original)
        self.mostrar_etapa("definir")
        self.establecer_estado(
            "Copia editable creada. El resultado permanece vigente hasta que cambies un valor.",
            "listo",
        )

    def mostrar_historial(self):
        # Programa 1/2 conserva su vista de sistemas al compartir historial con 3.
        registros = [r for r in self.historial.entradas if r.get('kind') != 'operacion']
        dialogo = tk.Toplevel(self.raiz)
        dialogo.title("Historial de AXION")
        ancho_dialogo = min(720, max(520, self.raiz.winfo_screenwidth() - 80))
        alto_dialogo = min(440, max(320, self.raiz.winfo_screenheight() - 100))
        dialogo.geometry(f"{ancho_dialogo}x{alto_dialogo}")
        dialogo.minsize(min(520, ancho_dialogo), min(320, alto_dialogo))
        dialogo.transient(self.raiz)
        dialogo.configure(bg=TemaAxion.PAPEL)
        dialogo.bind("<Escape>", lambda _e: dialogo.destroy())
        tk.Label(dialogo, text="Historial de ejercicios", bg=TemaAxion.PAPEL,
                 fg=TemaAxion.TINTA, font=(TemaAxion.FUENTE_SANS, 20, "bold")).pack(
                     anchor="w", padx=24, pady=(22, 4))
        tk.Label(dialogo, text="Hasta 50 entradas exactas. Reabrir crea una copia editable.",
                 bg=TemaAxion.PAPEL, fg=TemaAxion.ATENUADO,
                 font=(TemaAxion.FUENTE_SANS, 11)).pack(anchor="w", padx=24)
        contenedor = tk.Frame(dialogo, bg=TemaAxion.PAPEL)
        contenedor.pack(fill="both", expand=True, padx=24, pady=16)
        barra_desplazamiento = ttk.Scrollbar(contenedor)
        barra_desplazamiento.pack(side="right", fill="y")
        lista_visual = tk.Listbox(contenedor, yscrollcommand=barra_desplazamiento.set, activestyle="dotbox",
                             font=(TemaAxion.FUENTE_MONO, 11), selectmode="browse")
        lista_visual.pack(fill="both", expand=True)
        barra_desplazamiento.configure(command=lista_visual.yview)
        for elemento in registros:
            lista_visual.insert("end", f"{elemento['created_at']}   {elemento['rows']}×{elemento['variables']}   {elemento['classification']}")
        if not registros:
            lista_visual.insert("end", "Todavía no hay ejercicios guardados.")
            lista_visual.configure(state="disabled")
        acciones = tk.Frame(dialogo, bg=TemaAxion.PAPEL)
        acciones.pack(fill="x", padx=24, pady=(0, 20))

        def reabrir():
            if not registros or not lista_visual.curselection():
                return
            elemento = registros[lista_visual.curselection()[0]]
            if elemento.get("engine_version") != VERSION_MOTOR:
                messagebox.showinfo(
                    "Versión diferente",
                    "El registro se creó con otra versión del motor. Se cargará solo la entrada; "
                    "pulsa Resolver para recalcularla explícitamente.", parent=dialogo)
            self.editor.establecer_valores(elemento["matrix"])
            dialogo.destroy()
            self.mostrar_etapa("definir")
            if self.resultado and not self.resultado_desactualizado:
                self.establecer_estado(
                    "El ejercicio abierto coincide con el resultado vigente.", "resuelto")
            else:
                self.establecer_estado(
                    "Ejercicio del historial abierto como copia editable. Vuelve a resolver.",
                    "editando",
                )

        lista_visual.bind("<Return>", lambda _event: reabrir())
        lista_visual.bind("<Double-Button-1>", lambda _event: reabrir())

        tk.Button(acciones, text="Cerrar", command=dialogo.destroy, relief="flat",
                  bg=TemaAxion.PAPEL_ALTERNO, padx=16, pady=9).pack(side="right")
        tk.Button(acciones, text="Editar una copia", command=reabrir, relief="flat",
                  bg=TemaAxion.INDIGO, fg="white", padx=18, pady=9,
                  font=(TemaAxion.FUENTE_SANS, 11, "bold")).pack(side="right", padx=8)
        dialogo.after_idle(lista_visual.focus_set)

    def mostrar_ayuda(self):
        messagebox.showinfo(
            "Ayuda de AXION",
            "1. Define las dimensiones y pulsa Aplicar dimensiones.\n"
            "2. Introduce todos los coeficientes y la columna b.\n"
            "3. Revisa el sistema en la vista como ecuaciones.\n"
            "4. Conserva Gauss-Jordan para obtener la RREF.\n"
            "5. Pulsa Resolver con Gauss-Jordan y explora el procedimiento.\n\n"
            "Conceptos\nUn pivote es el primer valor no nulo de una fila reducida.\n"
            "Una variable libre corresponde a una columna de A sin pivote.\n"
            "La forma escalonada tiene ceros debajo de cada pivote; la RREF también "
            "normaliza cada pivote a 1 y crea ceros arriba.\n\n"
            "Atajos\nCtrl + Enter: resolver\nTab / Shift + Tab: cambiar de celda\n"
            "Flechas: navegar dentro del editor\nAlt + ← / →: cambiar de paso\n"
            "Ctrl + V: pegar matriz\nCtrl + Z: deshacer edición\nCtrl + S: guardar reporte\n"
            "F1: abrir esta ayuda\nEscape: cancelar edición o cerrar un diálogo",
            parent=self.raiz,
        )


def lanzar_aplicacion():
    """Compatibilidad con importaciones previas; utiliza el único arranque actual."""
    from axion_programa3 import lanzar_aplicacion as iniciar_programa3
    iniciar_programa3()
