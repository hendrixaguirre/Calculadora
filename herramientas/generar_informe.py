"""Herramienta documental local; NO es dependencia ni módulo de AXION.

Se ejecuta únicamente con las bibliotecas PDF ya incluidas en el entorno de
trabajo de Codex. El ZIP académico no incluye este generador.
"""
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.utils import ImageReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'entrega'
OUT.mkdir(exist_ok=True)
pdfmetrics.registerFont(TTFont('Lectura',r'C:\Windows\Fonts\arial.ttf'))
pdfmetrics.registerFont(TTFont('Titulo',r'C:\Windows\Fonts\arialbd.ttf'))
pdfmetrics.registerFont(TTFont('Codigo',r'C:\Windows\Fonts\consola.ttf'))
pdfmetrics.registerFontFamily('Lectura',normal='Lectura',bold='Titulo',italic='Lectura',boldItalic='Titulo')
INK=HexColor('#172033'); BLUE=HexColor('#1D4ED8'); MUTED=HexColor('#536073')
STYLE=ParagraphStyle('body',fontName='Lectura',fontSize=11,leading=16,textColor=INK,spaceAfter=10)
C=canvas.Canvas(str(OUT/'Informe_Programa 3_Grupo 5.pdf'),pagesize=A4)
C.setTitle('AXION - Programa 3 - Grupo 5')
C.setAuthor('Fanor Velasquez S; Hendrix Aguirre; Jarold Montealto')
page=0

def notacion(texto):
    # Arial no incluye todos los subíndices Unicode: usar notación textual legible.
    return texto.translate(str.maketrans({'₁':'1','₂':'2','ₖ':'k','ₚ':'_p','ⱼ':'_j'}))

def nueva(titulo, subtitulo='', horizontal=False):
    global page,W,H,Y
    if page:
        C.showPage()
    page+=1
    W,H=landscape(A4) if horizontal else A4
    C.setPageSize((W,H))
    C.setFillColor(BLUE); C.rect(0,H-8,W,8,fill=1,stroke=0)
    C.setFillColor(MUTED); C.setFont('Titulo',9)
    C.drawString(42,H-34,'AXION / UAM - FIA / ÁLGEBRA LINEAL')
    C.setFillColor(INK); C.setFont('Titulo',23 if not horizontal else 19)
    C.drawString(42,H-70,titulo)
    if subtitulo:
        C.setFont('Lectura',10); C.setFillColor(MUTED); C.drawString(42,H-90,notacion(subtitulo))
    C.setStrokeColor(HexColor('#D7DCE2')); C.line(42,36,W-42,36)
    C.setFont('Lectura',9); C.setFillColor(MUTED)
    C.drawString(42,22,'Programa 3 · Grupo 5 · 17 de septiembre de 2026')
    C.drawRightString(W-42,22,str(page))
    Y=H-118

def par(texto, after=10, size=11):
    global Y
    st=ParagraphStyle('p',parent=STYLE,fontSize=size,leading=size*1.45)
    p=Paragraph(notacion(texto),st)
    _,h=p.wrap(W-84,H)
    if Y-h < 48:
        raise RuntimeError(f'Página {page} sin espacio: {texto[:70]}')
    p.drawOn(C,42,Y-h)
    Y-=h+after

def titulo(texto):
    global Y
    Y-=6
    C.setFont('Titulo',14); C.setFillColor(BLUE); C.drawString(42,Y,texto)
    Y-=23

def codigo(texto):
    global Y
    lineas=texto.splitlines()
    alto=15*len(lineas)+22
    C.setFillColor(HexColor('#F1F4F8')); C.roundRect(42,Y-alto,W-84,alto,6,fill=1,stroke=0)
    C.setFillColor(INK); C.setFont('Codigo',10)
    for linea in lineas:
        Y-=15; C.drawString(53,Y,linea)
    Y-=25

nueva('Programa 3', 'Operaciones algebraicas, combinación lineal y ecuaciones matriciales')
C.setFillColor(INK); C.setFont('Titulo',46); C.drawString(42,Y-47,'AXION')
Y-=80
par('Álgebra lineal, paso a paso',size=17,after=38)
titulo('Universidad Americana (UAM)')
par('Facultad de Ingeniería y Arquitectura (FIA)<br/>Asignatura: Álgebra Lineal (MTM0120)<br/>Proyecto integrador: Calculadora de Álgebra Lineal',after=25)
titulo('Grupo 5')
par('<b>Docente:</b> José Munguia<br/><br/><b>Integrantes:</b><br/>Fanor Velasquez S<br/>Hendrix Aguirre<br/>Jarold Montealto',after=30)
par('Modalidad grupal, con defensa/exposición individual. Los nombres y el grupo fueron confirmados por el equipo; se conserva su escritura.',size=10)
par('Base académica: <i>Tarea 3 (Elaboracion Programa 3_Python).pdf</i>, UAM/FIA, páginas 1 y 2. La explicación técnica ocupa las dos páginas siguientes. Las capturas son de la aplicación de escritorio ejecutada en Windows.',size=10)

nueva('Cómo se construye AB', 'Explicación técnica · página 1 de 2')
titulo('1. Dimensiones y significado de una celda')
par('Sea A una matriz de m filas y n columnas, y B una matriz de n filas y p columnas. El producto AB existe porque cada fila de A y cada columna de B tienen n elementos. El resultado C contiene una celda por cada par fila-columna: por eso su forma es m×p. No se exige que A ni B sean cuadradas.')
par('AXION valida primero que ambas matrices sean rectangulares y no vacías y que las columnas de A coincidan con las filas de B. Si A tiene 3 columnas y B tiene 2 filas, el cálculo se detiene: no se truncan datos ni se publica un producto parcial.')
titulo('2. Tres bucles, tres responsabilidades')
par('El índice <b>i</b> del bucle exterior recorre las m filas de A. Para una fila fija, <b>j</b> recorre las p columnas de B. Para cada pareja (i,j), <b>r</b> recorre las n posiciones compartidas y acumula A[i][r]·B[r][j]. Los índices del código comienzan en 0; la interfaz los muestra desde 1.')
codigo('salida = []\nfor i in range(m):\n    fila = []\n    for j in range(p):\n        acumulador = Fraction(0)\n        for r in range(n):\n            acumulador += a[i][r] * b[r][j]\n        fila.append(acumulador)\n    salida.append(fila)')
par('Fragmento del algoritmo implementado en <b>axion_operaciones.py</b>, función <b>multiplicar_matrices</b>. Antes de estos bucles se validan los operandos y se obtienen m, n y p. Cada fila del resultado es una lista nueva: modificar una fila no modifica las otras.',size=10)
titulo('3. Por qué el acumulador comienza en cero')
par('El cero es la identidad de la suma. Cada celda necesita su propio acumulador: si se reutilizara el total de otra columna, se mezclarían productos distintos. Después de recorrer r, el acumulador contiene exactamente los n productos que corresponden a C[i][j].')

nueva('Del algoritmo a la explicación', 'Explicación técnica · página 2 de 2')
titulo('4. Un ejemplo rectangular completo')
codigo('A = [[1, 2, 3],       B = [[7,  8],\n     [4, 5, 6]]            [9, 10],\n                           [11,12]]\n\nA: 2 x 3       B: 3 x 2       C: 2 x 2\n\nc[1,1] = 1*7 + 2*9  + 3*11 = 58\nc[1,2] = 1*8 + 2*10 + 3*12 = 64\nc[2,1] = 4*7 + 5*9  + 6*11 = 139\nc[2,2] = 4*8 + 5*10 + 6*12 = 154')
par('Para c[1,2], se fija la primera fila de A y la segunda columna de B. El bucle interior genera 8, 20 y 36; su suma es 64. La interfaz permite seleccionar cualquier celda y muestra esta fila, esta columna, los productos parciales y su suma a partir de la instantánea exacta del cálculo.')
titulo('5. Precisión y costo del recorrido')
par('El número de multiplicaciones es m·n·p. El resultado almacena m·p valores. La explicación de una celda se prepara al seleccionarla y no conserva una copia completa de las matrices por cada producto elemental. Dentro del límite visible de 8 por eje, esto evita un registro desproporcionado para una operación sencilla.')
par('Las entradas decimales se convierten directamente desde texto a <b>Fraction</b>, sin pasar por float. Por ejemplo, diez veces (0.1, 0.2) produce exactamente (1, 2). Fracciones y decimales son opciones de presentación; el símbolo ≈ identifica una aproximación. No se redondea para clasificar ni comprobar soluciones.')
titulo('6. Relación con Vc=b y Ax=b')
par('Para decidir si b es combinación de v₁,…,vₖ, AXION forma V colocando los vectores como <b>columnas</b>. El mismo motor de eliminación de sistemas resuelve Vc=b. Rangos distintos implican imposibilidad; si el rango común es k, los coeficientes son únicos; si es menor que k, existen k−rango(V) parámetros libres.')
par('Para una familia c=cₚ+Σtⱼdⱼ, se verifica Vcₚ=b y Vdⱼ=0 para cada dirección. Comprobar solo una elección de parámetros sería insuficiente. Fraction representa racionales y Tkinter presenta la interfaz: la consigna no los nombra expresamente y ninguno sustituye los algoritmos manuales.',size=10)

def captura(tit,sub,nombre):
    nueva(tit,sub,True)
    imagen=ImageReader(str(ROOT/'docs'/'evidencia'/nombre))
    iw,ih=imagen.getSize()
    ancho=min(W-84,(H-151)*iw/ih)
    alto=ancho*ih/iw
    C.drawImage(imagen,(W-ancho)/2,48,width=ancho,height=alto,mask='auto')

captura('Prueba 1 · Multiplicación exitosa','A: 2×3; B: 3×2. Resultado: [[58, 64], [139, 154]]. Celda seleccionada: c[1,2]=64.','multiplicacion.png')
captura('Prueba 2 · Dimensiones incompatibles','A: [[1,2,3],[4,5,6]]; B: [[1,2],[3,4]]. Se rechaza AB porque 3 columnas no coinciden con 2 filas.','incompatibilidad.png')
captura('Prueba 3 · Combinación lineal','v₁=(1,0,1), v₂=(0,1,1), b=(2,3,5). Representación única: b=2v₁+3v₂; verificación exacta.','combinacion_lineal.png')

nueva('Ejecución y validación', 'Información de entrega · adicional a la explicación técnica')
titulo('Ejecutar sin conexión')
codigo('python "Programa 3_Grupo 5.py"\npython -m unittest -v')
par('Mantén todos los archivos axion_*.py junto al lanzador. AXION utiliza únicamente Python estándar, incluido tkinter/ttk y fractions.Fraction. No instala paquetes, no necesita cuentas y no realiza llamadas a servicios externos. Requiere una instalación de Python con Tcl/Tk y una sesión gráfica operativa.')
titulo('Qué se comprobó')
par('Línea base: <b>80 pruebas aprobadas</b>. Suite ampliada: <b>114 pruebas aprobadas, 0 fallos y 0 omisiones</b>. Incluye los casos A–K del encargo, propiedades e instantáneas independientes, clasificación y RREF, editores, pegado atómico, deshacer, estados de resultados, historial y exportación TXT/HTML. Los casos A–K son referencias del encargo de implementación; no se atribuyen al PDF del docente.')
par('Entorno: Windows 11, Python 3.14.6 y Tcl/Tk 8.6.15. Se capturaron ventanas reales de AXION y se revisaron producto, incompatibilidad, combinación lineal, matrices 8×8 y fracciones largas. Ctrl+Enter abrió el estado inicial guiado y Alt+Derecha avanzó un paso. Las capturas académicas corresponden a un área cliente de 1366×900.')
par('Medición local del producto 2×3 por 3×2: cálculo medio de <b>0.044 ms</b> en 1,000 repeticiones; renderizado de vistas sobre widgets existentes de <b>3.641 ms</b> en 10 repeticiones. Este último excluye iniciar la aplicación y guardar historial. Son mediciones de este equipo, no garantías universales.')
titulo('Límites y distinciones')
par('Se admiten 1–8 elementos por eje, 8×8 para A y hasta 8×9 para la aumentada, 64 caracteres y 48 dígitos por número y 4096 caracteres por pegado. Las entradas representan racionales dentro de R; no expresiones, irracionales simbólicos ni complejos. Los espacios dentro de un número se rechazan. En tablas nuevas, Tab separa columnas y la coma solo significa decimal.')
par('Se comprobó geometría solicitada de 1024×768, 1280×720, 1366×768, 1920×1080 y 820×720. La prueba de geometría no equivale a inspección visual completa: 1920×1080 de área cliente rebasa el área útil al añadir los bordes. No se probaron físicamente escalados de Windows al 100 %, 150 % ni 200 %, ni lectores de pantalla. El informe no declara accesibilidad integral.',size=10)
C.save()
print(OUT/'Informe_Programa 3_Grupo 5.pdf')
