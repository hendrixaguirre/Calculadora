"""Modo consola de sistemas, conservado sin depender de Tkinter."""
from axion_core import a_fraccion, construir_reporte, resolver_sistema
from axion_operaciones import dimension


def leer_dimension(mensaje):
    """Solicita entre 1 y 8 ecuaciones o incógnitas antes de crear la matriz."""
    while True:
        try:
            return dimension(input(mensaje).strip())
        except ValueError as error:
            print(error)


def leer_numero(mensaje):
    """Lee un coeficiente racional exacto y vuelve a solicitar datos inválidos."""
    while True:
        try:
            return a_fraccion(input(mensaje))
        except (ValueError, ZeroDivisionError) as error:
            print(f'Entrada inválida: {error}. Usa un entero, decimal o fracción.')


def resolver_interactivamente():
    """Forma [A|b], aplica el motor común y presenta su reporte educativo."""
    print('AXION — Sistemas Ax=b, paso a paso')
    filas = leer_dimension('Número de ecuaciones (1–8): ')
    variables = leer_dimension('Número de variables (1–8): ')
    matriz = []
    for i in range(filas):
        fila = []
        for j in range(variables):
            fila.append(leer_numero(f'Ecuación {i+1}, coeficiente x{j+1}: '))
        fila.append(leer_numero(f'Ecuación {i+1}, término b: '))
        matriz.append(fila)
    eleccion = input('Método [A=Automático, G=Gauss, J=Gauss-Jordan] (A): ').strip().lower()
    metodo = {'g': 'gauss', 'j': 'gauss-jordan'}.get(eleccion, 'automatico')
    print(construir_reporte(resolver_sistema(matriz, metodo)))
