"""Operaciones manuales de Programa 3, independientes de Tk y sin dependencias.

Los operandos se copian a Fraction; ninguna operación altera las entradas.
Las formas admitidas son 1..8 por eje. ValueError identifica datos incompatibles.
"""
from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
from typing import Sequence

from axion_core import (Numero, Matriz, ResultadoCalculo, a_fraccion,
                        resolver_sistema, formatear_numero, construir_reporte, corchetes_matriz)

MAX_DIMENSION = 8
MAX_PEGADO = 4096
OPERACIONES = {
    'vector_suma': 'Sumar vectores',
    'vector_resta': 'Restar vectores',
    'vector_escalar': 'Multiplicar vector por escalar',

    'matriz_suma': 'Sumar matrices',
    'matriz_resta': 'Restar matrices',
    'matriz_escalar': 'Multiplicar matriz por escalar',
    'matriz_producto': 'Multiplicar matrices',

    'combinacion': 'Comprobar combinación',

    'propiedad_distributiva': 'Propiedad distributiva A(u + v) = Au + Av',
    'propiedad_escalar': 'Propiedad del escalar A(cu) = c(Au)',
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

def multiplicar_matriz_vector(matriz, vector):
    """Calcula A·u y devuelve el resultado como vector columna lógico."""

    matriz = validar_matriz(matriz, 'Matriz A')
    vector = validar_vector(vector, 'Vector u')

    if len(matriz[0]) != len(vector):
        raise ValueError(
            f'A tiene {len(matriz[0])} columnas y u tiene '
            f'{len(vector)} componentes. Las dimensiones deben coincidir.'
        )

    resultado = []

    for fila in matriz:
        suma = Fraction(0)

        for j in range(len(vector)):
            suma += fila[j] * vector[j]

        resultado.append(suma)

    return resultado


def verificar_propiedad_producto_matriz_vector(
    operacion,
    matriz,
    datos,
    escalar=None,
):
    """Comprueba una propiedad del producto matriz-vector."""

    matriz = validar_matriz(matriz, 'Matriz A')

    if operacion == 'propiedad_distributiva':

        if len(datos) != 2:
            raise ValueError(
                'La propiedad distributiva requiere los vectores u y v.'
            )

        u = validar_vector(datos[0], 'Vector u')
        v = validar_vector(datos[1], 'Vector v')

        if len(u) != len(v):
            raise ValueError(
                'Los vectores u y v deben tener la misma dimensión.'
            )

        if len(matriz[0]) != len(u):
            raise ValueError(
                f'A tiene {len(matriz[0])} columnas, pero los vectores '
                f'tienen {len(u)} componentes.'
            )

        # Lado izquierdo:
        # A(u + v)
        u_mas_v = sumar_vectores(u, v)
        lado_izquierdo = multiplicar_matriz_vector(matriz, u_mas_v)

        # Lado derecho:
        # Au + Av
        au = multiplicar_matriz_vector(matriz, u)
        av = multiplicar_matriz_vector(matriz, v)
        lado_derecho = sumar_vectores(au, av)

        se_cumple = lado_izquierdo == lado_derecho

        return {
            'operacion': operacion,
            'matriz': matriz,
            'u': u,
            'v': v,
            'u_mas_v': u_mas_v,
            'au': au,
            'av': av,
            'lado_izquierdo': lado_izquierdo,
            'lado_derecho': lado_derecho,
            'se_cumple': se_cumple,
        }

    if operacion == 'propiedad_escalar':

        u = validar_vector(datos, 'Vector u')
        escalar = a_fraccion(escalar)

        if len(matriz[0]) != len(u):
            raise ValueError(
                f'A tiene {len(matriz[0])} columnas, pero u tiene '
                f'{len(u)} componentes.'
            )

        # Lado izquierdo:
        # A(cu)
        cu = escalar_vector(escalar, u)
        lado_izquierdo = multiplicar_matriz_vector(matriz, cu)

        # Lado derecho:
        # c(Au)
        au = multiplicar_matriz_vector(matriz, u)
        lado_derecho = escalar_vector(escalar, au)

        se_cumple = lado_izquierdo == lado_derecho

        return {
            'operacion': operacion,
            'matriz': matriz,
            'u': u,
            'escalar': escalar,
            'cu': cu,
            'au': au,
            'lado_izquierdo': lado_izquierdo,
            'lado_derecho': lado_derecho,
            'se_cumple': se_cumple,
        }

    raise ValueError('Propiedad del producto matriz-vector no reconocida.')

def propiedad_distributiva(a, u, v):
    """
    Comprueba la propiedad distributiva:

        A(u + v) = Au + Av

    A es una matriz.
    u y v son vectores de la misma dimensión.
    """

    a = validar_matriz(a, 'Matriz A')

    u = validar_vector(u, 'Vector u')
    v = validar_vector(v, 'Vector v')

    if len(a[0]) != len(u):
        raise ValueError(
            'Las columnas de A deben coincidir con la dimensión de u.'
        )

    if len(u) != len(v):
        raise ValueError(
            'Los vectores u y v deben tener la misma dimensión.'
        )

    # u + v
    u_mas_v = sumar_vectores(u, v)

    # A(u + v)
    izquierda = multiplicar_matrices(
        a,
        [[x] for x in u_mas_v]
    )

    # Au
    au = multiplicar_matrices(
        a,
        [[x] for x in u]
    )

    # Av
    av = multiplicar_matrices(
        a,
        [[x] for x in v]
    )

    # Au + Av
    derecha = sumar_matrices(
        au,
        av
    )

    cumple = izquierda == derecha

    return {
        'propiedad': 'A(u + v) = Au + Av',
        'u_mas_v': u_mas_v,
        'izquierda': izquierda,
        'au': au,
        'av': av,
        'derecha': derecha,
        'cumple': cumple,
    }


def propiedad_escalar(a, u, escalar):
    """
    Comprueba la propiedad:

        A(cu) = c(Au)

    A es una matriz.
    u es un vector.
    c es un escalar.
    """

    a = validar_matriz(a, 'Matriz A')

    u = validar_vector(u, 'Vector u')

    escalar = a_fraccion(escalar)

    if len(a[0]) != len(u):
        raise ValueError(
            'Las columnas de A deben coincidir con la dimensión de u.'
        )

    # cu
    cu = escalar_vector(
        escalar,
        u
    )

    # A(cu)
    izquierda = multiplicar_matrices(
        a,
        [[x] for x in cu]
    )

    # Au
    au = multiplicar_matrices(
        a,
        [[x] for x in u]
    )

    # c(Au)
    derecha = escalar_matriz(
        escalar,
        au
    )

    cumple = izquierda == derecha

    return {
        'propiedad': 'A(cu) = c(Au)',
        'cu': cu,
        'izquierda': izquierda,
        'au': au,
        'derecha': derecha,
        'cumple': cumple,
        'escalar': escalar,
    }

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
    operacion: str
    a: Matriz
    b: Matriz | None
    escalar: Fraction | None
    salida: Matriz | None
    sistema: ResultadoCalculo | None = None
    propiedad: dict | None = None

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

    # =====================================================
    # VALIDAR OPERANDO A
    # =====================================================

    a = validar_matriz(
        a,
        'Vectores v' if operacion == 'combinacion' else 'Operando A / u'
    )

    # =====================================================
    # VALIDAR OPERANDO B
    # =====================================================

    b = (
        validar_matriz(
            b,
            'Objetivo b'
            if operacion == 'combinacion'
            else 'Vectores u y v'
            if operacion == 'propiedad_distributiva'
            else 'Vector u'
            if operacion == 'propiedad_escalar'
            else 'Operando B / v'
        )
        if b is not None
        else None
    )

    # =====================================================
    # PROPIEDAD DISTRIBUTIVA
    #
    # A(u + v) = Au + Av
    # =====================================================

    if operacion == 'propiedad_distributiva':

        if b is None:
            raise ValueError(
                'La propiedad distributiva requiere los vectores u y v.'
            )

        if len(b) != 2:
            raise ValueError(
                'Debes introducir exactamente dos vectores: u y v.'
            )

        # Las columnas de A deben coincidir con
        # la dimensión de los vectores.
        if len(a[0]) != len(b[0]):
            raise ValueError(
                'Las columnas de A deben coincidir con la dimensión '
                'de los vectores u y v.'
            )

        # u y v deben tener la misma dimensión.
        if len(b[0]) != len(b[1]):
            raise ValueError(
                'Los vectores u y v deben tener la misma dimensión.'
            )

        return a, b, None

    # =====================================================
    # PROPIEDAD DEL ESCALAR
    #
    # A(cu) = c(Au)
    # =====================================================

    if operacion == 'propiedad_escalar':

        if b is None:
            raise ValueError(
                'La propiedad del escalar requiere el vector u.'
            )

        if len(b) != 1:
            raise ValueError(
                'Debes introducir un único vector u.'
            )

        # Las columnas de A deben coincidir con
        # la dimensión de u.
        if len(a[0]) != len(b[0]):
            raise ValueError(
                'Las columnas de A deben coincidir con la dimensión '
                'del vector u.'
            )

        # Validar el escalar c.
        try:
            escalar = a_fraccion(escalar)
        except (ValueError, ZeroDivisionError, TypeError) as error:
            raise ValueError(
                f'Escalar c: {error}. Introduce un racional válido.'
            ) from error

        return a, b, escalar

    # =====================================================
    # VALIDAR VECTORES
    # =====================================================

    if operacion.startswith('vector_'):

        if len(a) != 1:
            raise ValueError(
                'Introduce el vector como una sola fila de componentes.'
            )

        if b is not None and len(b) != 1:
            raise ValueError(
                'Introduce el segundo vector como una sola fila de componentes.'
            )

    # =====================================================
    # VALIDAR ESCALAR
    # =====================================================

    if operacion.endswith('escalar'):

        try:
            escalar = a_fraccion(escalar)

        except (ValueError, ZeroDivisionError, TypeError) as error:
            raise ValueError(
                f'Escalar λ: {error}. '
                'Introduce un racional válido.'
            ) from error

    # =====================================================
    # COMBINACIÓN LINEAL
    # =====================================================

    elif operacion == 'combinacion':

        if b is None:
            raise ValueError(
                'Falta el vector objetivo b.'
            )

        if len(b) != 1:
            raise ValueError(
                'Objetivo b: introduce un único vector fila.'
            )

        if len(a[0]) != len(b[0]):
            raise ValueError(
                'Todos los vectores y b deben tener la misma '
                'dimensión ambiente n.'
            )

    # =====================================================
    # PRODUCTO DE MATRICES
    # =====================================================

    elif operacion == 'matriz_producto':

        if b is None:
            raise ValueError(
                'Falta la matriz B.'
            )

        if len(a[0]) != len(b):
            raise ValueError(
                f'A tiene {len(a[0])} columnas y B tiene {len(b)} filas. '
                'Para AB estas cantidades deben coincidir. '
                'Ajusta las dimensiones.'
            )

    # =====================================================
    # SUMA / RESTA DE MATRICES
    # =====================================================

    elif b is not None:

        if (len(a), len(a[0])) != (len(b), len(b[0])):
            raise ValueError(
                'Los operandos de suma/resta deben tener '
                'las mismas dimensiones.'
            )

    # =====================================================
    # RESULTADO DE LA VALIDACIÓN
    # =====================================================

    return (
        a,
        b,
        escalar if operacion.endswith('escalar') else None
    )



def calcular_operacion(operacion, a, b=None, escalar=None) -> ResultadoOperacion:
    """Calcula sobre copias validadas y captura la evidencia exacta del resultado."""

    # =========================================================
    # VALIDAR OPERANDOS
    # =========================================================

    a, b, escalar = validar_operacion(
        operacion,
        a,
        b,
        escalar
    )

    # =========================================================
    # PROPIEDAD DISTRIBUTIVA
    #
    # A(u + v) = Au + Av
    # =========================================================

    if operacion == 'propiedad_distributiva':

        propiedad = verificar_propiedad_producto_matriz_vector(
            operacion,
            a,
            b
        )

        return ResultadoOperacion(
            operacion=operacion,
            a=a,
            b=b,
            escalar=None,
            salida=None,
            sistema=None,
            propiedad=propiedad
        )

    # =========================================================
    # PROPIEDAD DEL ESCALAR
    #
    # A(cu) = c(Au)
    # =========================================================

    if operacion == 'propiedad_escalar':

        propiedad = verificar_propiedad_producto_matriz_vector(
            operacion,
            a,
            b[0],
            escalar
        )

        return ResultadoOperacion(
            operacion=operacion,
            a=a,
            b=b,
            escalar=escalar,
            salida=None,
            sistema=None,
            propiedad=propiedad
        )

    # =========================================================
    # OPERACIONES CON ESCALAR
    # =========================================================

    if operacion.endswith('escalar'):

        salida = (
            [escalar_vector(escalar, a[0])]
            if operacion.startswith('vector')
            else escalar_matriz(escalar, a)
        )

    # =========================================================
    # COMBINACIÓN LINEAL
    # =========================================================

    elif operacion == 'combinacion':

        return ResultadoOperacion(
            operacion,
            a,
            b,
            None,
            None,
            combinacion_lineal(a, b[0])
        )

    # =========================================================
    # OPERACIONES CON VECTORES
    # =========================================================

    elif operacion.startswith('vector'):

        funcion = (
            sumar_vectores
            if operacion.endswith('suma')
            else restar_vectores
        )

        salida = [
            funcion(
                a[0],
                b[0]
            )
        ]

    # =========================================================
    # OPERACIONES CON MATRICES
    # =========================================================

    else:

        funciones = {
            'matriz_suma': sumar_matrices,
            'matriz_resta': restar_matrices,
            'matriz_producto': multiplicar_matrices
        }

        salida = funciones[operacion](
            a,
            b
        )

    # =========================================================
    # RESULTADO NORMAL
    # =========================================================

    return ResultadoOperacion(
        operacion,
        a,
        b,
        escalar,
        salida
    )

def texto_tabla(matriz, modo='fracciones'):
    """Texto sin truncamientos; conserva signo y valor exacto en vista decimal."""
    if not matriz:
        return ''
    filas = [[formatear_numero(v, modo) for v in fila] for fila in matriz]
    anchos = [max(len(fila[j]) for fila in filas) for j in range(len(filas[0]))]
    return '\n'.join(
        izq + ' ' + '   '.join(v.rjust(anchos[j]) for j, v in enumerate(fila)) + ' ' + der
        for fila, (izq, der) in zip(filas, corchetes_matriz(len(filas)))
    )


def texto_vectores(vectores, modo='fracciones'):
    """Una colección de vectores no constituye una única matriz de entrada."""
    return '\n'.join(f'v{i+1} = {texto_tabla([v], modo)}' for i, v in enumerate(vectores))


def pasos_propiedad(resultado: ResultadoOperacion, modo='fracciones') -> list[str]:
    """Presenta la evidencia ya calculada; no vuelve a ejecutar la operación."""
    p = resultado.propiedad
    if p is None:
        return []
    f = lambda x: formatear_numero(x, modo)
    vector = lambda v: '(' + ', '.join(f(x) for x in v) + ')'

    def producto(nombre, entrada, salida):
        lineas = [f'{nombre} = {vector(salida)}', 'Producto de cada fila de A por el vector:']
        for i, fila in enumerate(p['matriz']):
            expresion = ' + '.join(f'({f(a)})·({f(x)})' for a, x in zip(fila, entrada))
            lineas.append(f'Componente {i+1}: {expresion} = {f(salida[i])}')
        return '\n\n'.join(lineas)

    def suma(nombre, u, v, salida):
        return f'{nombre} = {vector(salida)}\n\n' + '\n'.join(
            f'Componente {i+1}: ({f(x)}) + ({f(y)}) = {f(z)}'
            for i, (x, y, z) in enumerate(zip(u, v, salida)))

    def escala(nombre, entrada, salida):
        return f'{nombre} = {vector(salida)}\n\n' + '\n'.join(
            f'Componente {i+1}: ({f(p["escalar"])})·({f(x)}) = {f(y)}'
            for i, (x, y) in enumerate(zip(entrada, salida)))

    inicial = (f'Estado inicial · {OPERACIONES[resultado.operacion]}\n\n'
               f'A =\n{texto_tabla(p["matriz"], modo)}\n\nu = {vector(p["u"])}')
    if resultado.operacion == 'propiedad_distributiva':
        pasos = [
            inicial + f'\nv = {vector(p["v"])}',
            suma('u + v', p['u'], p['v'], p['u_mas_v']),
            'Lado izquierdo\n\n' + producto('A(u + v)', p['u_mas_v'], p['lado_izquierdo']),
            producto('Au', p['u'], p['au']),
            producto('Av', p['v'], p['av']),
            'Lado derecho\n\n' + suma('Au + Av', p['au'], p['av'], p['lado_derecho']),
        ]
    else:
        pasos = [
            inicial + f'\nc = {f(p["escalar"])}',
            escala('cu', p['u'], p['cu']),
            'Lado izquierdo\n\n' + producto('A(cu)', p['cu'], p['lado_izquierdo']),
            producto('Au', p['u'], p['au']),
            'Lado derecho\n\n' + escala('c(Au)', p['au'], p['lado_derecho']),
        ]
    pasos.append(resumen_propiedad(resultado, modo))
    return pasos


def resumen_propiedad(resultado: ResultadoOperacion, modo='fracciones') -> str:
    """Genera el resultado de la comprobación de una propiedad Ax."""

    p = resultado.propiedad

    if not p:
        return 'No hay información disponible para esta propiedad.'

    f = lambda x: formatear_numero(x, modo)

    vector = lambda x: '(' + ', '.join(
        f(valor) for valor in x
    ) + ')'
    comparacion = '\n'.join(
        f'Componente {i+1}: {f(izq)} {"=" if izq == der else "≠"} {f(der)}; '
        f'diferencia exacta: {f(izq - der)}'
        for i, (izq, der) in enumerate(zip(p['lado_izquierdo'], p['lado_derecho']))
    ) + '\n\n'

    # =========================================================
    # PROPIEDAD DISTRIBUTIVA
    # =========================================================
    if resultado.operacion == 'propiedad_distributiva':

        return (
            'PROPIEDAD DISTRIBUTIVA DEL PRODUCTO MATRIZ-VECTOR\n\n'

            'A(u + v) = Au + Av\n\n'

            f'A =\n{texto_tabla(p["matriz"], modo)}\n\n'

            f'u = {vector(p["u"])}\n'
            f'v = {vector(p["v"])}\n\n'

            f'u + v = {vector(p["u_mas_v"])}\n\n'

            'LADO IZQUIERDO\n'
            f'A(u + v) = {vector(p["lado_izquierdo"])}\n\n'

            'LADO DERECHO\n'
            f'Au = {vector(p["au"])}\n'
            f'Av = {vector(p["av"])}\n'
            f'Au + Av = {vector(p["lado_derecho"])}\n\n'

            'VERIFICACIÓN\n'
            'A(u + v) = Au + Av\n\n'

            + comparacion + (
                '✓ La propiedad se cumple.'
                if p['se_cumple']
                else '✗ La propiedad no se cumple.'
            )
        )

    # =========================================================
    # PROPIEDAD DEL ESCALAR
    # =========================================================
    if resultado.operacion == 'propiedad_escalar':

        return (
            'PROPIEDAD DEL ESCALAR DEL PRODUCTO MATRIZ-VECTOR\n\n'

            'A(cu) = c(Au)\n\n'

            f'A =\n{texto_tabla(p["matriz"], modo)}\n\n'

            f'c = {f(p["escalar"])}\n'
            f'u = {vector(p["u"])}\n\n'

            f'cu = {vector(p["cu"])}\n\n'

            'LADO IZQUIERDO\n'
            f'A(cu) = {vector(p["lado_izquierdo"])}\n\n'

            'LADO DERECHO\n'
            f'Au = {vector(p["au"])}\n'
            f'c(Au) = {vector(p["lado_derecho"])}\n\n'

            'VERIFICACIÓN\n'
            'A(cu) = c(Au)\n\n'

            + comparacion + (
                '✓ La propiedad se cumple.'
                if p['se_cumple']
                else '✗ La propiedad no se cumple.'
            )
        )

    return 'Propiedad no reconocida.'

def resumen_combinacion(resultado: ResultadoCalculo, modo='fracciones') -> str:
    """Distingue existencia/unicidad y analiza dependencia lineal del conjunto."""

    s = resultado

    f = lambda x: formatear_numero(x, modo)

    vector = lambda x: '(' + ', '.join(f(v) for v in x) + ')'

    rangos = (
        f'rango(V) = {s.rango_a}; '
        f'rango([V|b]) = {s.rango_aumentada}; '
        f'k = {s.variables}'
    )

    # ---------------------------------------------------------
    # ANÁLISIS DE DEPENDENCIA LINEAL
    #
    # Para Vc = 0:
    #
    # rango(V) = k  -> únicamente c = 0
    #               -> solución trivial
    #               -> linealmente independiente
    #
    # rango(V) < k  -> existen soluciones no nulas
    #               -> solución no trivial
    #               -> linealmente dependiente
    # ---------------------------------------------------------

    if s.rango_a == s.variables:
        tipo_solucion = "trivial"
        dependencia = "linealmente independiente"
    else:
        tipo_solucion = "no trivial"
        dependencia = "linealmente dependiente"

    analisis_dependencia = (
        f'Solución del sistema homogéneo Vc = 0: {tipo_solucion}.\n'
        f'Conjunto de vectores: {dependencia}.'
    )

    # ---------------------------------------------------------
    # SISTEMA INCONSISTENTE
    # ---------------------------------------------------------

    if s.clasificacion == 'inconsistente':
        return (
            f'No es combinación lineal.\n'
            f'{rangos}\n\n'
            f'{analisis_dependencia}\n\n'
            f'Contradicción: 0 = {f(s.fila_contradiccion[-1])}.\n'
            f'No existen coeficientes que reconstruyan b.'
        )

    # ---------------------------------------------------------
    # SOLUCIÓN ÚNICA
    # ---------------------------------------------------------

    if s.solucion_unica is not None:

        desarrollo = ' + '.join(
            f'({f(c)})·v{i+1}'
            for i, c in enumerate(s.solucion_unica)
        )

        valores = '\n'.join(
            f'Componente {l.indice_ecuacion + 1}: '
            f'{f(l.valor_izquierdo)} = '
            f'{f(l.lado_derecho)}; '
            f'diferencia {f(l.diferencia)}'
            for l in s.verificacion
        )

        return (
            f'Sí es combinación lineal: representación única.\n'
            f'{rangos}\n\n'
            f'{analisis_dependencia}\n\n'
            f'c = {vector(s.solucion_unica)}\n'
            f'b = {desarrollo}\n'
            f'Verificación Vc=b: '
            f'{"correcta" if all(l.valida for l in s.verificacion) else "fallida"}\n'
            f'{valores}'
        )

    # ---------------------------------------------------------
    # INFINITAS SOLUCIONES
    # ---------------------------------------------------------

    lineas = [
        f'Sí es combinación lineal: infinitas representaciones.\n'
        f'{rangos}',

        '',

        analisis_dependencia,

        '',

        'c = cₚ + ' +
        ' + '.join(
            f't{j+1}·d{j+1}'
            for j in range(len(s.vectores_direccion))
        ),

        f'cₚ = {vector(s.solucion_particular)}'
    ]

    for j, d in enumerate(s.vectores_direccion):
        lineas.append(
            f'd{j+1} = {vector(d)}'
        )

    for i in range(s.variables):
        lineas.append(
            f'c{i+1} = ({f(s.solucion_particular[i])})'
            + ''.join(
                f' + ({f(d[i])})·t{j+1}'
                for j, d in enumerate(s.vectores_direccion)
                if d[i]
            )
        )

    lineas.extend([
        f'{len(s.variables_libres)} parámetros reales libres: '
        f'columnas sin pivote.',

        'Los vᵢ son los vectores dados; '
        'los dⱼ son direcciones de los coeficientes.',

        f'Verificado Vcₚ=b: '
        f'{"correcto" if s.verificacion_particular else "fallido"}',

        f'Verificado Vdⱼ=0 para TODAS las direcciones: '
        f'{"correcto" if s.verificacion_direcciones else "fallido"}'
    ])

    return '\n'.join(lineas)


def reporte_operacion(r: ResultadoOperacion, modo='fracciones') -> str:
    """Exporta resultados y verificaciones efectivamente calculados."""

    partes = [
        'AXION — Álgebra lineal, paso a paso',
        OPERACIONES[r.operacion],
        f'Entrada A / matriz: {len(r.a)}×{len(r.a[0])}',
        texto_vectores(r.a, modo) if r.operacion == 'combinacion' else texto_tabla(r.a, modo)
    ]

    if r.b is not None:
        partes.extend([
            f'Entrada B / vectores: {len(r.b)}×{len(r.b[0])}',
            texto_vectores(r.b, modo) if r.operacion == 'propiedad_distributiva' else texto_tabla(r.b, modo)
        ])

    if r.escalar is not None:
        partes.append(
            'λ = ' + formatear_numero(r.escalar, modo)
        )

    # =========================================================
    # PROPIEDADES
    # =========================================================
    if r.propiedad:

        partes.extend([
            '',
            resumen_propiedad(r, modo)
        ])

        return '\n\n'.join(partes)

    # =========================================================
    # SISTEMA / COMBINACIÓN LINEAL
    # =========================================================
    if r.sistema:

        partes.extend([
            'V se construye con los vectores dados como COLUMNAS; Vc=b.',
            resumen_combinacion(r.sistema, modo),
            'Reducción reutilizada:',
            construir_reporte(r.sistema, modo)
        ])

        return '\n\n'.join(partes)

    # =========================================================
    # OPERACIONES NORMALES
    # =========================================================
    partes.extend([
        f'Cálculo exacto · resultado '
        f'{len(r.salida)}×{len(r.salida[0])}',
        texto_tabla(r.salida, modo)
    ])

    for i in range(len(r.salida)):
        for j in range(len(r.salida[0])):
            partes.append(
                r.detalle(i, j, modo)
            )

    return '\n\n'.join(partes)
