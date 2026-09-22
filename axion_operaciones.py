"""Operaciones manuales de Programa 3, independientes de Tk y sin dependencias.

Los operandos se copian a Fraction; ninguna operación altera las entradas.
Las formas admitidas son 1..8 por eje. ValueError identifica datos incompatibles.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from axion_core import (Numero, Matriz, ResultadoCalculo, a_fraccion,
                        resolver_sistema, formatear_numero, construir_reporte)

MAX_DIMENSION = 8
MAX_PEGADO = 4096
OPERACIONES = {
    'vector_suma': 'Sumar vectores', 'vector_resta': 'Restar vectores',
    'vector_escalar': 'Multiplicar vector por escalar',
    'matriz_suma': 'Sumar matrices', 'matriz_resta': 'Restar matrices',
    'matriz_escalar': 'Multiplicar matriz por escalar',
    'matriz_producto': 'Multiplicar matrices', 'combinacion': 'Comprobar combinación',
}


def dimension(valor) -> int:
    """Una dimensión es un entero positivo, nunca una fracción ni un booleano."""
    if isinstance(valor, bool) or not str(valor).isascii() or not str(valor).isdigit():
        raise ValueError('La dimensión debe ser un entero entre 1 y 8')
    numero = int(valor)
    if not 1 <= numero <= MAX_DIMENSION:
        raise ValueError('La dimensión debe estar entre 1 y 8')
    return numero


def validar_matriz(valores: Sequence[Sequence[Numero]], nombre='Matriz A') -> Matriz:
    """Valida forma rectangular no vacía y convierte cada celda con su ubicación."""
    if not isinstance(valores, (list, tuple)) or not valores:
        raise ValueError(f'{nombre}: introduce una matriz no vacía')
    if not all(isinstance(f, (list, tuple)) for f in valores) or not valores[0]:
        raise ValueError(f'{nombre}: cada fila debe contener valores')
    dimension(len(valores))
    dimension(len(valores[0]))
    salida = []
    for i, fila in enumerate(valores):
        if len(fila) != len(valores[0]):
            raise ValueError(f'{nombre}, fila {i+1}: iguala la longitud de todas las filas')
        nueva = []
        for j, valor in enumerate(fila):
            try:
                nueva.append(a_fraccion(valor))
            except (ValueError, ZeroDivisionError, TypeError, OverflowError) as error:
                raise ValueError(f'{nombre}, fila {i+1}, columna {j+1}: {error}. '
                                 'Usa un entero, decimal finito o fracción con denominador distinto de 0') from error
        salida.append(nueva)
    return salida


def validar_vector(valores: Sequence[Numero], nombre='Vector u') -> list[Fraction]:
    """Un vector de Rⁿ se representa por n racionales, con 1 ≤ n ≤ 8."""
    return validar_matriz([valores], nombre)[0]


def sumar_vectores(u, v):
    """Devuelve u+v, sumando componentes del mismo índice; exige igual dimensión."""
    u, v = validar_vector(u), validar_vector(v, 'Vector v')
    if len(u) != len(v):
        raise ValueError('Vectores u y v: sus dimensiones deben coincidir')
    salida = []
    for i in range(len(u)):
        salida.append(u[i] + v[i])
    return salida


def restar_vectores(u, v):
    """Devuelve u−v componente a componente; no trunca vectores incompatibles."""
    u, v = validar_vector(u), validar_vector(v, 'Vector v')
    if len(u) != len(v):
        raise ValueError('Vectores u y v: sus dimensiones deben coincidir')
    salida = []
    for i in range(len(u)):
        salida.append(u[i] - v[i])
    return salida


def escalar_vector(escalar, u):
    """Devuelve λu: multiplica cada componente por el mismo racional λ."""
    u, escalar = validar_vector(u), a_fraccion(escalar)
    salida = []
    for i in range(len(u)):
        salida.append(escalar * u[i])
    return salida


def _suma_resta(a, b, signo):
    """Suma Aᵢⱼ + signo·Bᵢⱼ; signo=1 suma y signo=−1 resta, en formas iguales."""
    a, b = validar_matriz(a), validar_matriz(b, 'Matriz B')
    if (len(a), len(a[0])) != (len(b), len(b[0])):
        raise ValueError('Matrices A y B: suma y resta requieren las mismas filas y columnas')
    salida = []
    for i in range(len(a)):
        fila = []
        for j in range(len(a[0])):
            fila.append(a[i][j] + signo * b[i][j])
        salida.append(fila)
    return salida


def sumar_matrices(a, b):
    """(A+B)ᵢⱼ=Aᵢⱼ+Bᵢⱼ; exige formas iguales y produce una matriz independiente."""
    return _suma_resta(a, b, 1)


def restar_matrices(a, b):
    """(A−B)ᵢⱼ=Aᵢⱼ−Bᵢⱼ; exige formas iguales y conserva ambos operandos."""
    return _suma_resta(a, b, -1)


def escalar_matriz(escalar, a):
    """(λA)ᵢⱼ=λAᵢⱼ: dos recorridos, uno por fila y otro por columna."""
    a, escalar = validar_matriz(a), a_fraccion(escalar)
    salida = []
    for i in range(len(a)):
        fila = []
        for j in range(len(a[0])):
            fila.append(escalar * a[i][j])
        salida.append(fila)
    return salida


def multiplicar_matrices(a, b):
    """Calcula AB para A m×n y B n×p, con exactamente tres bucles algebraicos.

    i selecciona la fila de A; j la columna de B; r recorre sus n pares.
    Cada C[i][j] tiene un acumulador cero propio. Devuelve m×p racionales.
    La incompatibilidad se rechaza antes de construir cualquier resultado.
    """
    a, b = validar_matriz(a), validar_matriz(b, 'Matriz B')
    m, n, p = len(a), len(a[0]), len(b[0])
    if n != len(b):
        raise ValueError(f'A tiene {n} columnas y B tiene {len(b)} filas. '
                         'Para AB estas cantidades deben coincidir. Ajusta las dimensiones')
    salida = []
    for i in range(m):
        fila = []
        for j in range(p):
            acumulador = Fraction(0)
            for r in range(n):
                acumulador += a[i][r] * b[r][j]
            fila.append(acumulador)
        salida.append(fila)
    return salida


def resolver_ax_b(a, b, metodo='gauss-jordan') -> ResultadoCalculo:
    """Construye [A|b] (b no es incógnita) y reutiliza la eliminación existente."""
    a, b = validar_matriz(a), validar_vector(b, 'Vector b')
    if len(a) != len(b):
        raise ValueError('Vector b: su longitud debe ser igual al número de filas de A')
    aumentada = []
    for i in range(len(a)):
        aumentada.append(a[i][:] + [b[i]])
    return resolver_sistema(aumentada, metodo)


def combinacion_lineal(vectores, b) -> ResultadoCalculo:
    """Coloca v₁,…,vₖ como COLUMNAS de V n×k y resuelve Vc=b.

    La clasificación y la verificación de la particular y todas las direcciones
    proceden del mismo motor de Ax=b. Dependencia no implica inconsistencia.
    """
    vectores = validar_matriz(vectores, 'Vectores dados (uno por fila)')
    b = validar_vector(b, 'Objetivo b')
    if len(vectores[0]) != len(b):
        raise ValueError('Todos los vectores y b deben tener la misma dimensión ambiente n')
    v = []
    for i in range(len(b)):
        fila = []
        for j in range(len(vectores)):
            fila.append(vectores[j][i])
        v.append(fila)
    return resolver_ax_b(v, b)


def interpretar_tabla(texto, nombre='Matriz A') -> list[list[str]]:
    """TSV estricto: Tab separa columnas; salto separa filas; coma solo decimal.

    Valida completamente antes de devolver datos; un vacío nunca es cero.
    """
    if len(texto) > MAX_PEGADO:
        raise ValueError('El pegado supera 4096 caracteres; divide la entrada')
    filas = [fila.split('\t') for fila in texto.strip('\r\n').splitlines()]
    validar_matriz(filas, nombre)
    return [[celda.strip() for celda in fila] for fila in filas]


@dataclass
class ResultadoOperacion:
    """Instantánea exacta; los detalles por celda se generan bajo demanda."""
    operacion: str
    a: Matriz
    b: Matriz | None
    escalar: Fraction | None
    salida: Matriz | None
    sistema: ResultadoCalculo | None = None

    def detalle(self, i, j, modo='fracciones') -> str:
        if self.salida is None or not (0 <= i < len(self.salida) and 0 <= j < len(self.salida[0])):
            raise ValueError('Selecciona una celda existente del resultado')
        f = lambda x: formatear_numero(x, modo)
        if self.operacion == 'matriz_producto':
            terminos, parciales = [], []
            for r in range(len(self.a[0])):
                terminos.append(f'({f(self.a[i][r])})·({f(self.b[r][j])})')
                parciales.append(f(self.a[i][r] * self.b[r][j]))
            return (f'Fila {i+1} de A × columna {j+1} de B\n'
                    f'c[{i+1},{j+1}] = ' + ' + '.join(terminos) + '\n'
                    '= ' + ' + '.join(f'({p})' for p in parciales) + f' = {f(self.salida[i][j])}')
        if self.escalar is not None:
            expresion = f'({f(self.escalar)})·({f(self.a[i][j])})'
        else:
            signo = '+' if self.operacion.endswith('suma') else '−'
            expresion = f'({f(self.a[i][j])}) {signo} ({f(self.b[i][j])})'
        return f'Componente [{i+1},{j+1}]: {expresion} = {f(self.salida[i][j])}'


def validar_operacion(operacion, a, b=None, escalar=None):
    """Valida operandos y compatibilidad sin efectuar operaciones algebraicas.

    El historial solo necesita este contrato; abrirlo no debe repetir cálculos.
    Devuelve copias racionales de A, B y λ.
    """
    if operacion not in OPERACIONES:
        raise ValueError('Operación no reconocida')
    a = validar_matriz(a, 'Vectores v' if operacion == 'combinacion' else 'Operando A / u')
    b = validar_matriz(b, 'Objetivo b' if operacion == 'combinacion' else 'Operando B / v') if b is not None else None
    if operacion.startswith('vector_') and (len(a) != 1 or (b is not None and len(b) != 1)):
        raise ValueError('Introduce cada vector como una sola fila de componentes')
    if operacion.endswith('escalar'):
        try:
            escalar = a_fraccion(escalar)
        except (ValueError, ZeroDivisionError, TypeError) as error:
            raise ValueError(f'Escalar λ: {error}. Introduce un racional válido') from error
    elif b is None:
        raise ValueError('Falta el segundo operando')
    elif operacion == 'combinacion':
        if len(b) != 1:
            raise ValueError('Objetivo b: introduce un único vector fila')
        if len(a[0]) != len(b[0]):
            raise ValueError('Todos los vectores y b deben tener la misma dimensión ambiente n')
    elif operacion == 'matriz_producto':
        if len(a[0]) != len(b):
            raise ValueError(f'A tiene {len(a[0])} columnas y B tiene {len(b)} filas. '
                             'Para AB estas cantidades deben coincidir. Ajusta las dimensiones')
    elif (len(a), len(a[0])) != (len(b), len(b[0])):
        raise ValueError('Los operandos de suma/resta deben tener las mismas dimensiones')
    return a, b, escalar if operacion.endswith('escalar') else None


def calcular_operacion(operacion, a, b=None, escalar=None) -> ResultadoOperacion:
    """Calcula sobre copias validadas y captura la evidencia exacta del resultado."""
    a, b, escalar = validar_operacion(operacion, a, b, escalar)
    if operacion.endswith('escalar'):
        salida = [escalar_vector(escalar, a[0])] if operacion.startswith('vector') else escalar_matriz(escalar, a)
    elif operacion == 'combinacion':
        return ResultadoOperacion(operacion, a, b, None, None, combinacion_lineal(a, b[0]))
    elif operacion.startswith('vector'):
        funcion = sumar_vectores if operacion.endswith('suma') else restar_vectores
        salida = [funcion(a[0], b[0])]
    else:
        funciones = {'matriz_suma': sumar_matrices, 'matriz_resta': restar_matrices,
                     'matriz_producto': multiplicar_matrices}
        salida = funciones[operacion](a, b)
    return ResultadoOperacion(operacion, a, b, escalar, salida)


def texto_tabla(matriz, modo='fracciones'):
    """Texto sin truncamientos; conserva signo y valor exacto en vista decimal."""
    return '\n'.join('[ ' + '   '.join(formatear_numero(v, modo) for v in fila) + ' ]' for fila in matriz)


def resumen_combinacion(resultado: ResultadoCalculo, modo='fracciones') -> str:
    """Distingue existencia/unicidad y muestra evidencia de toda la familia."""
    s = resultado
    f = lambda x: formatear_numero(x, modo)
    vector = lambda x: '(' + ', '.join(f(v) for v in x) + ')'
    rangos = f'rango(V) = {s.rango_a}; rango([V|b]) = {s.rango_aumentada}; k = {s.variables}'
    if s.clasificacion == 'inconsistente':
        return f'No es combinación lineal.\n{rangos}\nContradicción: 0 = {f(s.fila_contradiccion[-1])}.\nNo existen coeficientes que reconstruyan b.'
    if s.solucion_unica is not None:
        desarrollo = ' + '.join(f'({f(c)})·v{i+1}' for i, c in enumerate(s.solucion_unica))
        valores = '\n'.join(f'Componente {l.indice_ecuacion+1}: {f(l.valor_izquierdo)} = {f(l.lado_derecho)}; diferencia {f(l.diferencia)}' for l in s.verificacion)
        return (f'Sí es combinación lineal: representación única.\n{rangos}\n'
                f'c = {vector(s.solucion_unica)}\nb = {desarrollo}\n'
                f'Verificación Vc=b: {"correcta" if all(l.valida for l in s.verificacion) else "fallida"}\n{valores}')
    lineas = [f'Sí es combinación lineal: infinitas representaciones.\n{rangos}',
              'c = cₚ + ' + ' + '.join(f't{j+1}·d{j+1}' for j in range(len(s.vectores_direccion))),
              f'cₚ = {vector(s.solucion_particular)}']
    for j, d in enumerate(s.vectores_direccion):
        lineas.append(f'd{j+1} = {vector(d)}')
    for i in range(s.variables):
        lineas.append(f'c{i+1} = ({f(s.solucion_particular[i])})' + ''.join(f' + ({f(d[i])})·t{j+1}' for j, d in enumerate(s.vectores_direccion) if d[i]))
    lineas.extend([f'{len(s.variables_libres)} parámetros reales libres: columnas sin pivote.',
                  'Los vᵢ son los vectores dados; los dⱼ son direcciones de los coeficientes.',
                  f'Verificado Vcₚ=b: {"correcto" if s.verificacion_particular else "fallido"}',
                  f'Verificado Vdⱼ=0 para TODAS las direcciones: {"correcto" if s.verificacion_direcciones else "fallido"}'])
    return '\n'.join(lineas)


def reporte_operacion(r: ResultadoOperacion, modo='fracciones') -> str:
    """Exporta únicamente resultados y verificaciones efectivamente calculados."""
    partes = ['AXION — Álgebra lineal, paso a paso', OPERACIONES[r.operacion],
              f'Entrada A / vectores: {len(r.a)}×{len(r.a[0])}', texto_tabla(r.a, modo)]
    if r.b is not None:
        partes.extend([f'Entrada B / b: {len(r.b)}×{len(r.b[0])}', texto_tabla(r.b, modo)])
    if r.escalar is not None:
        partes.append('λ = ' + formatear_numero(r.escalar, modo))
    if r.sistema:
        partes.extend(['V se construye con los vectores dados como COLUMNAS; Vc=b.',
                       resumen_combinacion(r.sistema, modo),
                       'Reducción reutilizada (x en el reporte siguiente representa c):',
                       construir_reporte(r.sistema, modo)])
    else:
        partes.extend([f'Cálculo exacto · resultado {len(r.salida)}×{len(r.salida[0])}', texto_tabla(r.salida, modo)])
        for i in range(len(r.salida)):
            for j in range(len(r.salida[0])):
                partes.append(r.detalle(i, j, modo))
    return '\n\n'.join(partes)
