"""Motor matemático exacto y modelos educativos de AXION.

El módulo no depende de Tkinter. Todas las operaciones se realizan con
``fractions.Fraction`` y cada transformación se registra como datos
estructurados para que la interfaz no tenga que interpretar cadenas.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fractions import Fraction
import re
from typing import Sequence

Numero = int | float | str | Fraction
Matriz = list[list[Fraction]]

MAX_LONGITUD_ENTRADA = 64
MAX_DIGITOS_ENTRADA = 48
MAX_EXPONENTE = 100
MAX_ECUACIONES = 8
MAX_VARIABLES = 8
_ENTERO = r"[+-]?\d+"
_DECIMAL = r"[+-]?(?:(?:\d+(?:\.\d*)?)|(?:\.\d+))(?:[eE][+-]?\d+)?"
_PATRON_NUMERO = re.compile(rf"^(?:{_ENTERO}/{_ENTERO}|{_DECIMAL})$")


def a_fraccion(valor: Numero) -> Fraction:
    """Convierte entradas numéricas sin introducir error binario innecesario."""
    if isinstance(valor, Fraction):
        return valor
    if isinstance(valor, float):
        return Fraction(str(valor))
    if isinstance(valor, str):
        texto = valor.strip().replace(",", ".")
        if re.search(r"\s", texto):
            raise ValueError("No se admiten espacios dentro de un número")
        if not texto:
            raise ValueError("Ingresa un valor")
        if len(texto) > MAX_LONGITUD_ENTRADA:
            raise ValueError(f"El valor supera {MAX_LONGITUD_ENTRADA} caracteres")
        if not _PATRON_NUMERO.fullmatch(texto):
            raise ValueError("Formato no válido; usa entero, decimal o fracción a/b")
        if len(re.sub(r"\D", "", texto)) > MAX_DIGITOS_ENTRADA:
            raise ValueError(f"El valor supera {MAX_DIGITOS_ENTRADA} dígitos")
        exponente = re.search(r"[eE]([+-]?\d+)$", texto)
        if exponente and abs(int(exponente.group(1))) > MAX_EXPONENTE:
            raise ValueError(f"El exponente debe estar entre −{MAX_EXPONENTE} y {MAX_EXPONENTE}")
        if "/" in texto:
            texto_numerador, texto_denominador = texto.split("/", 1)
            if int(texto_denominador) == 0:
                raise ZeroDivisionError("El denominador no puede ser cero")
            numero = Fraction(int(texto_numerador), int(texto_denominador))
        else:
            numero = Fraction(texto)
        if abs(numero.numerator) > 10 ** MAX_DIGITOS_ENTRADA or numero.denominator > 10 ** MAX_DIGITOS_ENTRADA:
            raise ValueError("La magnitud del valor es demasiado grande")
        return numero
    return Fraction(valor)


def matriz_exacta(valores: Sequence[Sequence[Numero]]) -> Matriz:
    if not valores or not valores[0]:
        raise ValueError("La matriz no puede estar vacía")
    ancho = len(valores[0])
    if any(len(fila) != ancho for fila in valores):
        raise ValueError("Todas las filas deben tener la misma cantidad de valores")
    return [[a_fraccion(valor) for valor in fila] for fila in valores]


def copiar_matriz(matriz: Matriz) -> Matriz:
    return [fila[:] for fila in matriz]


def _decimal_aproximado(numero: Fraction, precision: int) -> str:
    """Redondea solo la presentación mediante enteros, sin desbordamiento float."""
    if not isinstance(precision, int) or not 0 <= precision <= 10:
        raise ValueError('La precisión decimal debe estar entre 0 y 10')
    factor = 10 ** precision
    redondeado = round(abs(numero) * factor)
    entero, resto = divmod(redondeado, factor)
    signo = '-' if numero < 0 and redondeado else ''
    decimales = str(resto).rjust(precision, '0').rstrip('0') if precision else ''
    return signo + str(entero) + ('.' + decimales if decimales else '')


def formatear_numero(valor: Numero, modo: str = "fracciones", precision: int = 4) -> str:
    numero = a_fraccion(valor)
    if numero.denominator == 1:
        return str(numero.numerator)
    exacto = f"{numero.numerator}/{numero.denominator}"
    if modo == "decimales":
        aproximado = _decimal_aproximado(numero, precision)
        return f"{exacto} ≈ {aproximado}"
    return exacto


def numero_compacto(valor: Numero, modo: str = "fracciones", precision: int = 4) -> str:
    """Formato corto para matrices; en decimal no repite la forma exacta."""
    numero = a_fraccion(valor)
    if modo == "decimales" and numero.denominator != 1:
        return "≈" + _decimal_aproximado(numero, precision)
    return formatear_numero(numero, "fracciones", precision)


@dataclass(frozen=True)
class CeldaModificada:
    fila: int
    columna: int
    antes: Fraction
    despues: Fraction


@dataclass
class PasoFila:
    indice: int
    titulo: str
    objetivo: str
    tipo_operacion: str
    notacion_operacion: str
    fila_origen: int | None
    fila_destino: int | None
    multiplicador: Fraction | None
    columna_objetivo: int | None
    posicion_pivote: tuple[int, int] | None
    valor_pivote: Fraction | None
    matriz_antes: Matriz
    matriz_despues: Matriz
    celdas_modificadas: list[CeldaModificada] = field(default_factory=list)
    explicacion_breve: str = ""
    explicacion_formal: str = ""


@dataclass(frozen=True)
class LineaVerificacion:
    indice_ecuacion: int
    coeficientes: tuple[Fraction, ...]
    lado_derecho: Fraction
    terminos_sustituidos: tuple[Fraction, ...]
    valor_izquierdo: Fraction
    diferencia: Fraction
    valida: bool


@dataclass
class ResultadoCalculo:
    original: Matriz
    variables: int
    metodo_solicitado: str
    metodo_usado: str
    pasos: list[PasoFila]
    escalonada: Matriz
    rref: Matriz
    matriz_final: Matriz
    columnas_pivote: list[int]
    posiciones_pivote: list[tuple[int, int]]
    posiciones_pivote_aumentada: list[tuple[int, int]]
    columnas_pivote_aumentada: list[int]
    pivote_contradiccion: tuple[int, int] | None
    rango_a: int
    rango_aumentada: int
    clasificacion: str
    variables_basicas: list[int]
    variables_libres: list[int]
    columnas_no_pivote_a: list[int] = field(default_factory=list)
    solucion_unica: list[Fraction] | None = None
    solucion_particular: list[Fraction] | None = None
    vectores_direccion: list[list[Fraction]] = field(default_factory=list)
    verificacion_particular: bool | None = None
    verificacion_direcciones: bool | None = None
    fila_contradiccion: list[Fraction] | None = None
    verificacion: list[LineaVerificacion] = field(default_factory=list)
    conclusion: str = ""


def _celdas_modificadas(antes: Matriz, despues: Matriz) -> list[CeldaModificada]:
    return [
        CeldaModificada(i, j, antes[i][j], despues[i][j])
        for i in range(len(antes))
        for j in range(len(antes[0]))
        if antes[i][j] != despues[i][j]
    ]


def _subindice(numero: int) -> str:
    tabla = str.maketrans("0123456789-", "₀₁₂₃₄₅₆₇₈₉₋")
    return str(numero).translate(tabla)


def nombre_fila(indice: int) -> str:
    return f"F{_subindice(indice + 1)}"


def _agregar_paso(
    pasos: list[PasoFila], *, titulo: str, objetivo: str, tipo_operacion: str,
    notacion: str, fila_origen: int | None, fila_destino: int | None,
    multiplicador: Fraction | None, posicion_pivote: tuple[int, int] | None,
    valor_pivote: Fraction | None, antes: Matriz, despues: Matriz,
    sencilla: str, formal: str, columna_objetivo: int | None = None,
) -> None:
    pasos.append(PasoFila(
        indice=len(pasos) + 1,
        titulo=titulo,
        objetivo=objetivo,
        tipo_operacion=tipo_operacion,
        notacion_operacion=notacion,
        fila_origen=fila_origen,
        fila_destino=fila_destino,
        multiplicador=multiplicador,
        columna_objetivo=(posicion_pivote[1] if posicion_pivote is not None else columna_objetivo),
        posicion_pivote=posicion_pivote,
        valor_pivote=valor_pivote,
        matriz_antes=copiar_matriz(antes),
        matriz_despues=copiar_matriz(despues),
        celdas_modificadas=_celdas_modificadas(antes, despues),
        explicacion_breve=sencilla,
        explicacion_formal=formal,
    ))


def _eliminacion_hacia_adelante(matriz: Matriz, variables: int, pasos: list[PasoFila]):
    trabajo = copiar_matriz(matriz)
    posiciones_pivote: list[tuple[int, int]] = []
    fila_pivote = 0
    for columna in range(variables):
        if fila_pivote >= len(trabajo):
            break
        candidatos = [fila for fila in range(fila_pivote, len(trabajo)) if trabajo[fila][columna] != 0]
        if not candidatos:
            continue
        mejor = max(candidatos, key=lambda fila: abs(trabajo[fila][columna]))
        if mejor != fila_pivote:
            antes = copiar_matriz(trabajo)
            trabajo[fila_pivote], trabajo[mejor] = trabajo[mejor], trabajo[fila_pivote]
            _agregar_paso(
                pasos, titulo="Intercambio de filas",
                objetivo=f"Colocar un valor distinto de cero en la columna x{_subindice(columna + 1)}.",
                tipo_operacion="swap", notacion=f"{nombre_fila(fila_pivote)} ↔ {nombre_fila(mejor)}",
                fila_origen=mejor, fila_destino=fila_pivote, multiplicador=None,
                posicion_pivote=(fila_pivote, columna), valor_pivote=trabajo[fila_pivote][columna],
                antes=antes, despues=trabajo,
                sencilla=(f"El valor disponible en {nombre_fila(fila_pivote)} es cero o no es el mejor "
                        f"pivote. Intercambiamos {nombre_fila(fila_pivote)} y {nombre_fila(mejor)}."),
                formal="Intercambiar dos filas es una operación elemental que conserva el conjunto solución.",
            )

        pivote = trabajo[fila_pivote][columna]
        iguales = copiar_matriz(trabajo)
        _agregar_paso(
            pasos, titulo=f"Selección del pivote {len(posiciones_pivote) + 1}",
            objetivo=f"Usar este elemento para eliminar los demás valores de la columna x{_subindice(columna + 1)}.",
            tipo_operacion="pivot", notacion=f"a{_subindice(fila_pivote + 1)}{_subindice(columna + 1)} = {formatear_numero(pivote)}",
            fila_origen=fila_pivote, fila_destino=fila_pivote, multiplicador=None,
            posicion_pivote=(fila_pivote, columna), valor_pivote=pivote,
            antes=iguales, despues=iguales,
            sencilla=(f"Seleccionamos el valor {formatear_numero(pivote)} de la fila {fila_pivote + 1}, "
                    f"columna {columna + 1}, como pivote."),
            formal="Un pivote identifica una variable básica y dirige las eliminaciones de su columna.",
        )

        if pivote != 1:
            antes = copiar_matriz(trabajo)
            factor = Fraction(1, 1) / pivote
            trabajo[fila_pivote] = [valor * factor for valor in trabajo[fila_pivote]]
            _agregar_paso(
                pasos, titulo="Normalización de la fila pivote",
                objetivo="Convertir el pivote en 1 para simplificar las eliminaciones.",
                tipo_operacion="scale",
                notacion=f"{nombre_fila(fila_pivote)} ← ({formatear_numero(factor)}){nombre_fila(fila_pivote)}",
                fila_origen=fila_pivote, fila_destino=fila_pivote, multiplicador=factor,
                posicion_pivote=(fila_pivote, columna), valor_pivote=Fraction(1),
                antes=antes, despues=trabajo,
                sencilla=(f"Multiplicamos todos los valores de {nombre_fila(fila_pivote)} por "
                        f"{formatear_numero(factor)} para que el pivote sea 1."),
                formal="Multiplicar una fila por un escalar distinto de cero produce una matriz equivalente por filas.",
            )

        for destino in range(fila_pivote + 1, len(trabajo)):
            factor = trabajo[destino][columna]
            if factor == 0:
                continue
            antes = copiar_matriz(trabajo)
            trabajo[destino] = [
                trabajo[destino][j] - factor * trabajo[fila_pivote][j]
                for j in range(variables + 1)
            ]
            _agregar_paso(
                pasos, titulo="Eliminación debajo del pivote",
                objetivo=f"Crear un cero en la fila {destino + 1}, columna {columna + 1}.",
                tipo_operacion="replace",
                notacion=(f"{nombre_fila(destino)} ← {nombre_fila(destino)} − "
                          f"({formatear_numero(factor)}){nombre_fila(fila_pivote)}"),
                fila_origen=fila_pivote, fila_destino=destino, multiplicador=factor,
                posicion_pivote=(fila_pivote, columna), valor_pivote=trabajo[fila_pivote][columna],
                antes=antes, despues=trabajo,
                sencilla=(f"Restamos {formatear_numero(factor)} veces {nombre_fila(fila_pivote)} a "
                        f"{nombre_fila(destino)} para convertir el valor de esa columna en cero."),
                formal="El reemplazo de una fila por ella misma más un múltiplo de otra conserva el conjunto solución.",
            )
        posiciones_pivote.append((fila_pivote, columna))
        fila_pivote += 1
    return trabajo, posiciones_pivote


def _paso_inicial(matriz: Matriz, pasos: list[PasoFila]) -> None:
    """Registra la entrada como el primer momento del recorrido educativo."""
    instantanea = copiar_matriz(matriz)
    _agregar_paso(
        pasos, titulo="Matriz aumentada inicial",
        objetivo="Reconocer la matriz [A|b] antes de aplicar operaciones elementales.",
        tipo_operacion="initial", notacion="Inicio: [A|b]",
        fila_origen=None, fila_destino=None, multiplicador=None,
        posicion_pivote=None, valor_pivote=None, antes=instantanea, despues=instantanea,
        sencilla="Esta es una copia exacta de la entrada. Todavía no se ha modificado ninguna fila.",
        formal=("Cada fila representa una ecuación y la última columna es el vector b. "
                "Buscaremos pivotes de izquierda a derecha."),
    )


def _reemplazo_expandido(antes: Matriz, origen: int, destino: int, factor: Fraction) -> str:
    """Describe componente a componente F_destino - factor·F_origen, incluida b."""
    partes = []
    for actual, valor_pivote in zip(antes[destino], antes[origen]):
        partes.append(
            f"{formatear_numero(actual)} − ({formatear_numero(factor)})·({formatear_numero(valor_pivote)})"
        )
    resultados = [
        formatear_numero(actual - factor * valor_pivote)
        for actual, valor_pivote in zip(antes[destino], antes[origen])
    ]
    return "[" + ",  ".join(partes) + "] = [" + ",  ".join(resultados) + "]"


def _rref_gauss_jordan(
    matriz: Matriz, variables: int, pasos: list[PasoFila] | None = None,
) -> tuple[Matriz, list[tuple[int, int]]]:
    """Calcula manualmente la RREF de toda [A|b], incluida una posible columna pivote b.

    El algoritmo usa únicamente operaciones elementales sobre listas anidadas:
    intercambio, normalización y reemplazo de filas. Explorar también la última
    columna garantiza que una contradicción se normalice como ``[0 … 0 | 1]``.
    """
    trabajo = copiar_matriz(matriz)
    pivotes: list[tuple[int, int]] = []
    fila_pivote = 0
    columnas = variables + 1
    for columna in range(columnas):
        if fila_pivote >= len(trabajo):
            break
        candidatos = [fila for fila in range(fila_pivote, len(trabajo)) if trabajo[fila][columna] != 0]
        if not candidatos:
            if pasos is not None and columna < variables:
                iguales = copiar_matriz(trabajo)
                _agregar_paso(
                    pasos, titulo=f"Columna {columna + 1} sin pivote",
                    objetivo=f"Comprobar si la columna de x{_subindice(columna + 1)} contiene un candidato.",
                    tipo_operacion="skip", notacion=f"Columna {columna + 1}: sin pivote",
                    fila_origen=None, fila_destino=None, multiplicador=None,
                    posicion_pivote=None, valor_pivote=None, antes=iguales, despues=iguales,
                    columna_objetivo=columna,
                    sencilla=(f"Desde la fila {fila_pivote + 1} todos los valores de esta columna son cero; "
                            "la columna se omite y puede corresponder a una variable libre."),
                    formal="Omitir una columna sin candidato no transforma la matriz.",
                )
            continue

        mejor = max(candidatos, key=lambda fila: abs(trabajo[fila][columna]))
        if mejor != fila_pivote:
            antes = copiar_matriz(trabajo)
            trabajo[fila_pivote], trabajo[mejor] = trabajo[mejor], trabajo[fila_pivote]
            if pasos is not None:
                etiqueta = "b" if columna == variables else f"x{_subindice(columna + 1)}"
                _agregar_paso(
                    pasos, titulo="Intercambio de filas",
                    objetivo=f"Colocar un candidato distinto de cero en la columna {etiqueta}.",
                    tipo_operacion="swap", notacion=f"{nombre_fila(fila_pivote)} ↔ {nombre_fila(mejor)}",
                    fila_origen=mejor, fila_destino=fila_pivote, multiplicador=None,
                    posicion_pivote=(fila_pivote, columna), valor_pivote=trabajo[fila_pivote][columna],
                    antes=antes, despues=trabajo,
                    sencilla=f"Intercambiamos {nombre_fila(fila_pivote)} y {nombre_fila(mejor)} para continuar la reducción.",
                    formal="Intercambiar ecuaciones no altera el conjunto de soluciones.",
                )

        pivote = trabajo[fila_pivote][columna]
        if pasos is not None:
            iguales = copiar_matriz(trabajo)
            etiqueta = "b (columna aumentada)" if columna == variables else f"x{_subindice(columna + 1)}"
            _agregar_paso(
                pasos, titulo="Selección de pivote" if columna < variables else "Detección de contradicción",
                objetivo=f"Usar la fila {fila_pivote + 1} como referencia en la columna {etiqueta}.",
                tipo_operacion="pivot", notacion=(
                    f"a{_subindice(fila_pivote + 1)}{_subindice(columna + 1)} = {formatear_numero(pivote)}"
                ),
                fila_origen=fila_pivote, fila_destino=fila_pivote, multiplicador=None,
                posicion_pivote=(fila_pivote, columna), valor_pivote=pivote,
                antes=iguales, despues=iguales,
                sencilla=(f"El elemento de la fila {fila_pivote + 1}, columna {columna + 1}, "
                        f"se elige como pivote{' de la columna aumentada b' if columna == variables else ''}."),
                formal=("Un pivote en b representa una fila contradictoria, no una variable básica."
                        if columna == variables else
                        "El pivote de A identifica una variable básica y dirige la eliminación de su columna."),
            )

        if pivote != 1:
            antes = copiar_matriz(trabajo)
            escala = Fraction(1, 1) / pivote
            trabajo[fila_pivote] = [valor * escala for valor in trabajo[fila_pivote]]
            if pasos is not None:
                _agregar_paso(
                    pasos, titulo="Normalización de la fila pivote",
                    objetivo="Convertir el pivote en 1 operando sobre la fila completa, incluida b.",
                    tipo_operacion="scale",
                    notacion=f"{nombre_fila(fila_pivote)} ← ({formatear_numero(escala)}){nombre_fila(fila_pivote)}",
                    fila_origen=fila_pivote, fila_destino=fila_pivote, multiplicador=escala,
                    posicion_pivote=(fila_pivote, columna), valor_pivote=Fraction(1),
                    antes=antes, despues=trabajo,
                    sencilla=(f"Multiplicamos cada componente de {nombre_fila(fila_pivote)} por "
                            f"{formatear_numero(escala)}; el pivote queda igual a 1."),
                    formal="Multiplicar una ecuación por un escalar no nulo conserva sus soluciones.",
                )

        for destino in range(len(trabajo)):
            if destino == fila_pivote:
                continue
            factor = trabajo[destino][columna]
            if factor == 0:
                continue
            antes = copiar_matriz(trabajo)
            trabajo[destino] = [
                trabajo[destino][j] - factor * trabajo[fila_pivote][j]
                for j in range(columnas)
            ]
            if pasos is not None:
                titulo = "Eliminación sobre el pivote" if destino < fila_pivote else "Eliminación debajo del pivote"
                nota_signo = (
                    f"Como el factor {formatear_numero(factor)} es negativo, restarlo equivale a sumar. "
                    if factor < 0 else ""
                )
                _agregar_paso(
                    pasos, titulo=titulo,
                    objetivo=f"Crear un cero en la fila {destino + 1}, columna {columna + 1}.",
                    tipo_operacion="replace",
                    notacion=(f"{nombre_fila(destino)} ← {nombre_fila(destino)} − "
                              f"({formatear_numero(factor)}){nombre_fila(fila_pivote)}"),
                    fila_origen=fila_pivote, fila_destino=destino, multiplicador=factor,
                    posicion_pivote=(fila_pivote, columna), valor_pivote=trabajo[fila_pivote][columna],
                    antes=antes, despues=trabajo,
                    sencilla=(f"{nota_signo}Aplicamos la operación a todos los coeficientes y también a b."),
                    formal=(f"{_reemplazo_expandido(antes, fila_pivote, destino, factor)}. "
                            "Sumar a una ecuación un múltiplo de otra conserva el sistema equivalente."),
                )
        pivotes.append((fila_pivote, columna))
        fila_pivote += 1
    return trabajo, pivotes


def es_rref(matriz: Sequence[Sequence[Numero]]) -> bool:
    """Comprueba las cuatro condiciones de la forma escalonada reducida."""
    trabajo = matriz_exacta(matriz)
    pivote_anterior = -1
    cero_encontrado = False
    for indice_fila, fila in enumerate(trabajo):
        no_cero = next((columna for columna, valor in enumerate(fila) if valor != 0), None)
        if no_cero is None:
            cero_encontrado = True
            continue
        if cero_encontrado or no_cero <= pivote_anterior or fila[no_cero] != 1:
            return False
        if any(trabajo[otro][no_cero] != 0 for otro in range(len(trabajo)) if otro != indice_fila):
            return False
        pivote_anterior = no_cero
    return True


def _rangos(matriz: Matriz, variables: int) -> tuple[int, int]:
    rango_a = sum(any(valor != 0 for valor in fila[:variables]) for fila in matriz)
    rango_aumentada = sum(any(valor != 0 for valor in fila) for fila in matriz)
    return rango_a, rango_aumentada


def _sustitucion_hacia_atras(
    escalonada: Matriz, pivotes: list[tuple[int, int]], variables: int,
) -> list[Fraction]:
    solucion = [Fraction(0) for _ in range(variables)]
    for fila, columna in reversed(pivotes):
        conocido = sum(escalonada[fila][j] * solucion[j] for j in range(columna + 1, variables))
        solucion[columna] = (escalonada[fila][-1] - conocido) / escalonada[fila][columna]
    return solucion


def _solucion_parametrica(
    rref: Matriz, pivotes: list[tuple[int, int]], variables: int,
) -> tuple[list[Fraction], list[int], list[list[Fraction]]]:
    columnas_pivote = [columna for _, columna in pivotes]
    columnas_libres = [columna for columna in range(variables) if columna not in columnas_pivote]
    particular = [Fraction(0) for _ in range(variables)]
    for fila, columna in pivotes:
        particular[columna] = rref[fila][-1]
    direcciones: list[list[Fraction]] = []
    for libre in columnas_libres:
        direccion = [Fraction(0) for _ in range(variables)]
        direccion[libre] = Fraction(1)
        for fila, columna in pivotes:
            direccion[columna] = -rref[fila][libre]
        direcciones.append(direccion)
    return particular, columnas_libres, direcciones


def _verificar_unica(matriz: Matriz, solucion: list[Fraction]) -> list[LineaVerificacion]:
    verificacion = []
    for indice, fila in enumerate(matriz):
        terminos = tuple(fila[j] * solucion[j] for j in range(len(solucion)))
        izquierdo = sum(terminos, Fraction(0))
        verificacion.append(LineaVerificacion(
            indice_ecuacion=indice,
            coeficientes=tuple(fila[:-1]),
            lado_derecho=fila[-1],
            terminos_sustituidos=terminos,
            valor_izquierdo=izquierdo,
            diferencia=izquierdo - fila[-1],
            valida=izquierdo == fila[-1],
        ))
    return verificacion


def resolver_sistema(
    valores: Sequence[Sequence[Numero]], metodo: str = "gauss-jordan",
) -> ResultadoCalculo:
    original = matriz_exacta(valores)
    variables = len(original[0]) - 1
    if variables < 1:
        raise ValueError("La matriz aumentada necesita al menos una variable y la columna b")
    if len(original) > MAX_ECUACIONES or variables > MAX_VARIABLES:
        raise ValueError(
            f"AXION admite como máximo {MAX_ECUACIONES} ecuaciones y "
            f"{MAX_VARIABLES} variables"
        )
    normalizada = metodo.strip().lower().replace("_", "-")
    alias_metodos = {
        "automático": "automatico", "auto": "automatico",
        "eliminación de gauss": "gauss", "eliminacion de gauss": "gauss",
        "gauss-jordan": "gauss-jordan", "jordan": "gauss-jordan",
    }
    normalizada = alias_metodos.get(normalizada, normalizada)
    if normalizada not in {"automatico", "gauss", "gauss-jordan"}:
        raise ValueError("Método no reconocido")
    metodo_usado = "gauss-jordan" if normalizada == "automatico" else normalizada
    pasos: list[PasoFila] = []
    _paso_inicial(original, pasos)
    if metodo_usado == "gauss-jordan":
        rref, pivotes_aumentada = _rref_gauss_jordan(original, variables, pasos)
        escalonada, _ = _eliminacion_hacia_adelante(original, variables, [])
    else:
        escalonada, _ = _eliminacion_hacia_adelante(original, variables, pasos)
        rref, pivotes_aumentada = _rref_gauss_jordan(original, variables)
    pivotes = [(fila, columna) for fila, columna in pivotes_aumentada if columna < variables]
    rango_a, rango_aumentada = _rangos(rref, variables)
    columnas_pivote = [columna for _, columna in pivotes]
    columnas_pivote_aumentada = [columna for _, columna in pivotes_aumentada]
    basicas = columnas_pivote[:]
    columnas_no_pivote = [columna for columna in range(variables) if columna not in columnas_pivote]
    contradiccion = next(
        (fila[:] for fila in rref if all(valor == 0 for valor in fila[:variables]) and fila[-1] != 0),
        None,
    )
    pivote_contradiccion = next(
        ((fila, columna) for fila, columna in pivotes_aumentada if columna == variables), None
    )
    resultado = ResultadoCalculo(
        original=copiar_matriz(original), variables=variables,
        metodo_solicitado=normalizada, metodo_usado=metodo_usado, pasos=pasos,
        escalonada=copiar_matriz(escalonada), rref=copiar_matriz(rref),
        matriz_final=copiar_matriz(rref if metodo_usado == "gauss-jordan" else escalonada),
        columnas_pivote=columnas_pivote, posiciones_pivote=pivotes,
        posiciones_pivote_aumentada=pivotes_aumentada,
        columnas_pivote_aumentada=columnas_pivote_aumentada,
        pivote_contradiccion=pivote_contradiccion,
        rango_a=rango_a, rango_aumentada=rango_aumentada,
        clasificacion="", variables_basicas=basicas, variables_libres=[],
        columnas_no_pivote_a=columnas_no_pivote,
        fila_contradiccion=contradiccion,
    )
    if contradiccion is not None:
        resultado.clasificacion = "inconsistente"
        resultado.conclusion = (
            "La reducción contiene una igualdad imposible. Ningún conjunto de valores "
            "puede satisfacer simultáneamente todas las ecuaciones."
        )
    elif rango_a == variables:
        resultado.clasificacion = "unica"
        resultado.solucion_unica = (
            [rref[fila][-1] for fila in range(variables)]
            if metodo_usado == "gauss-jordan"
            else _sustitucion_hacia_atras(escalonada, pivotes, variables)
        )
        resultado.verificacion = _verificar_unica(original, resultado.solucion_unica)
        resultado.conclusion = (
            "Existe un pivote para cada variable y los rangos coinciden con el número "
            "de variables; por eso la solución es única."
        )
    else:
        resultado.clasificacion = "infinitas"
        particular, columnas_libres, direcciones = _solucion_parametrica(rref, pivotes, variables)
        resultado.solucion_particular = particular
        resultado.variables_libres = columnas_libres
        resultado.vectores_direccion = direcciones
        resultado.verificacion_particular = all(
            sum(fila[j] * particular[j] for j in range(variables)) == fila[-1]
            for fila in original
        )
        resultado.verificacion_direcciones = all(
            all(sum(fila[j] * direccion[j] for j in range(variables)) == 0
                for fila in original)
            for direccion in direcciones
        )
        resultado.conclusion = (
            "El sistema es consistente y contiene variables libres. Cada parámetro real "
            "genera una solución diferente."
        )
    return resultado


def texto_matriz(
    matriz: Matriz, modo: str = "fracciones", precision: int = 4,
    prefijo_fila: bool = False,
) -> str:
    variables = len(matriz[0]) - 1
    renderizado = [[numero_compacto(valor, modo, precision) for valor in fila] for fila in matriz]
    anchos = [max(len(renderizado[i][j]) for i in range(len(renderizado))) for j in range(variables + 1)]
    lineas = []
    for i, fila in enumerate(renderizado):
        izquierdo = "  ".join(fila[j].rjust(anchos[j]) for j in range(variables))
        derecho = fila[-1].rjust(anchos[-1])
        prefijo = f"{nombre_fila(i)}  " if prefijo_fila else ""
        lineas.append(f"{prefijo}⎡ {izquierdo}  │  {derecho} ⎤")
    return "\n".join(lineas)


def texto_ecuacion(fila: Sequence[Numero], modo: str = "fracciones", precision: int = 4) -> str:
    valores = [a_fraccion(valor) for valor in fila]
    terminos: list[str] = []
    for indice, coeficiente in enumerate(valores[:-1]):
        if coeficiente == 0:
            continue
        magnitud = abs(coeficiente)
        texto_coeficiente = "" if magnitud == 1 else numero_compacto(magnitud, modo, precision)
        variable = f"x{_subindice(indice + 1)}"
        termino = f"{texto_coeficiente}{variable}"
        if not terminos:
            terminos.append(("−" if coeficiente < 0 else "") + termino)
        else:
            terminos.append((" − " if coeficiente < 0 else " + ") + termino)
    return ("".join(terminos) or "0") + f" = {numero_compacto(valores[-1], modo, precision)}"


def texto_ecuaciones(matriz: Matriz, modo: str = "fracciones", precision: int = 4) -> str:
    return "\n".join(texto_ecuacion(fila, modo, precision) for fila in matriz)


def lineas_parametricas(
    resultado: ResultadoCalculo, modo: str = "fracciones", precision: int = 4,
) -> list[str]:
    if resultado.solucion_particular is None:
        return []
    lineas = []
    for variable in range(resultado.variables):
        expresion = numero_compacto(resultado.solucion_particular[variable], modo, precision)
        for parametro, vector in enumerate(resultado.vectores_direccion, start=1):
            coeficiente = vector[variable]
            if coeficiente == 0:
                continue
            signo = " + " if coeficiente > 0 else " − "
            magnitud = abs(coeficiente)
            texto_coeficiente = "" if magnitud == 1 else numero_compacto(magnitud, modo, precision)
            expresion += f"{signo}{texto_coeficiente}t{_subindice(parametro)}"
        lineas.append(f"x{_subindice(variable + 1)} = {expresion}")
    lineas.append(";  ".join(f"t{_subindice(i + 1)} ∈ ℝ" for i in range(len(resultado.vectores_direccion))))
    return lineas


def texto_forma_vectorial(
    resultado: ResultadoCalculo, modo: str = "fracciones", precision: int = 4,
) -> str:
    """Expresa una familia paramétrica como x = x₀ + t₁v₁ + …"""
    if resultado.solucion_particular is None:
        return ""

    def vector(valores):
        return "[" + ", ".join(numero_compacto(valor, modo, precision) for valor in valores) + "]ᵀ"

    expresion = f"x = {vector(resultado.solucion_particular)}"
    for indice, direccion in enumerate(resultado.vectores_direccion, start=1):
        expresion += f" + t{_subindice(indice)}{vector(direccion)}"
    return expresion


def construir_reporte(
    resultado: ResultadoCalculo, modo: str = "fracciones", precision: int = 4,
) -> str:
    etiqueta_metodo = "Gauss-Jordan" if resultado.metodo_usado == "gauss-jordan" else "Eliminación de Gauss"
    representacion = (
        "fracciones exactas"
        if modo == "fracciones"
        else f"decimales aproximados (≈), {precision} cifras; el cálculo interno permanece exacto"
    )
    secciones = [
        "AXION — Resolución de sistema lineal",
        f"Representación: {representacion}",
        "",
        "1. SISTEMA ORIGINAL",
        texto_ecuaciones(resultado.original, modo, precision),
        "",
        "2. MATRIZ AUMENTADA ORIGINAL [A|b]",
        texto_matriz(resultado.original, modo, precision),
        "",
        "3. MÉTODO UTILIZADO",
        etiqueta_metodo,
        "",
        "4. PROCEDIMIENTO COMPLETO",
    ]
    for paso in resultado.pasos:
        secciones.extend([
            f"Paso {paso.indice:02d} — {paso.titulo}", paso.notacion_operacion,
            paso.explicacion_breve, texto_matriz(paso.matriz_despues, modo, precision), "",
        ])
    secciones.extend([
        "5. MATRIZ ESCALONADA", texto_matriz(resultado.escalonada, modo, precision), "",
        "6. MATRIZ ESCALONADA REDUCIDA", texto_matriz(resultado.rref, modo, precision), "",
        "7. ANÁLISIS DE RANGOS",
        f"rango(A) = {resultado.rango_a}\nrango([A|b]) = {resultado.rango_aumentada}", "",
        "8. CLASIFICACIÓN", resultado.clasificacion.upper(), "",
        "9. VARIABLES",
        "Básicas: " + (", ".join(f"x{_subindice(i + 1)}" for i in resultado.variables_basicas) or "ninguna"),
        ("Libres: no aplica; el sistema es inconsistente" if resultado.clasificacion == "inconsistente" else
         "Libres: " + (", ".join(f"x{_subindice(i + 1)}" for i in resultado.variables_libres) or "ninguna")),
        "Pivotes de A: " + (", ".join(str(i + 1) for i in resultado.columnas_pivote) or "ninguno"),
        "Pivotes de [A|b]: " + (", ".join(
            "b" if i == resultado.variables else str(i + 1)
            for i in resultado.columnas_pivote_aumentada) or "ninguno"),
        "", "10. SOLUCIÓN",
    ])
    if resultado.solucion_unica is not None:
        secciones.append("\n".join(
            f"x{_subindice(i + 1)} = {formatear_numero(valor, modo, precision)}"
            for i, valor in enumerate(resultado.solucion_unica)
        ))
    elif resultado.clasificacion == "infinitas":
        secciones.append("\n".join(lineas_parametricas(resultado, modo, precision)))
        secciones.append("Forma vectorial:\n" + texto_forma_vectorial(resultado, modo, precision))
    else:
        secciones.append("No existe solución.")
    secciones.extend(["", "11. VERIFICACIÓN"])
    if resultado.verificacion:
        for elemento in resultado.verificacion:
            secciones.append(
                f"Ecuación {elemento.indice_ecuacion + 1}: "
                f"{formatear_numero(elemento.valor_izquierdo, modo, precision)} = "
                f"{formatear_numero(elemento.lado_derecho, modo, precision)}  "
                f"diferencia = {formatear_numero(elemento.diferencia, modo, precision)}  "
                f"{'✓' if elemento.valida else '✕'}"
            )
    elif resultado.clasificacion == "inconsistente" and resultado.fila_contradiccion:
        secciones.append(f"Contradicción: 0 = {formatear_numero(resultado.fila_contradiccion[-1], modo, precision)}")
    else:
        secciones.append("La solución particular y las direcciones satisfacen el sistema correspondiente.")
    secciones.extend(["", "12. CONCLUSIÓN", resultado.conclusion])
    return "\n".join(secciones)
