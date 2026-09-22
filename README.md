# AXION — Programa 3 · Grupo 5

Calculadora de álgebra lineal con aritmética racional exacta y explicación paso a
paso. Incluye vectores, matrices, combinación lineal y sistemas Ax=b.
Funciona sin conexión y utiliza solo la biblioteca estándar de Python.

## Iniciar

```powershell
python "Programa 3_Grupo 5.py"
```

Requiere Python con Tcl/Tk y una sesión gráfica. Entorno comprobado: Windows 11,
Python 3.14.6 y Tcl/Tk 8.6.15. Mantén los archivos `axion_*.py` junto al lanzador.
Para resolver sistemas desde la consola, sin importar Tk:

```powershell
python "Programa 3_Grupo 5.py" --cli
```

## Uso

- Selecciona el espacio de trabajo y la operación.
- Define las dimensiones y pulsa **Aplicar**; completa las celdas o carga un ejemplo.
- Calcula para consultar el resultado y su procedimiento.
- Cada operación conserva su borrador y último resultado durante la sesión.
- Puedes guardar resultados en el historial y exportar el informe HTML.

Se admiten enteros, decimales y fracciones. Los tamaños van de 1 a 8 por eje;
el editor de sistemas admite la columna aumentada adicional. Los cálculos usan
`Fraction`, sin convertir los datos a coma flotante ni ejecutar texto introducido.
El historial se guarda en `%LOCALAPPDATA%/AXION` en Windows, con un máximo de
50 entradas. La limpieza del proyecto no modifica ese historial.

Atajos: `Ctrl+Enter` calcula, `Ctrl+Z` deshace, `Ctrl+S` guarda el reporte TXT,
`Alt+Izquierda/Derecha` recorre pasos y `F1` abre la ayuda.

## Organización del proyecto

| Ubicación | Contenido |
| --- | --- |
| `Programa 3_Grupo 5.py` | Único punto de entrada, gráfico o `--cli` |
| `axion_core.py` | Resolución exacta de sistemas y pasos matemáticos |
| `axion_operaciones.py` | Operaciones y validación de vectores y matrices |
| `axion_ui.py`, `axion_workbench.py`, `axion_programa3.py` | Interfaz y editores |
| `axion_storage.py` | Historial y exportación HTML |
| `axion_cli.py` | Entrada y salida por consola |
| `tests/` | Pruebas automatizadas |
| `herramientas/` | Empaquetado, mediciones, revisión visual y generación del informe |
| `docs/` | Registro de revisión, evidencias y archivo histórico de Programa 2 |
| `entrega/` | Informe PDF y ZIP listo para entregar |

Los siete módulos `axion_*.py` tienen responsabilidades activas y se necesitan
para conservar las funciones actuales. Las versiones anteriores se conservan
reunidas en `docs/archivo_programa2.zip`.

## Comprobación y entrega

Desde la raíz del proyecto o del ZIP extraído:

```powershell
python -B -m unittest -v
```

Las pruebas de interfaz necesitan Tcl/Tk y una sesión gráfica.
Para reconstruir la entrega desde el proyecto de desarrollo:

```powershell
python -B herramientas/empaquetar_programa3.py
```

El empaquetador verifica dependencias, extrae el ZIP en una ruta con espacios y
acentos, ejecuta las pruebas y abre brevemente el lanzador real. Sustituye la
entrega anterior solo si todas las comprobaciones terminan correctamente.
El ZIP incluye el lanzador, los módulos, las pruebas, este README y el informe
PDF; las herramientas y evidencias de desarrollo permanecen en el proyecto.

Consulta `docs/DEPURACION.md` para los cambios de limpieza. La validación inicial
se conserva en `docs/QA_PROGRAMA3.md`; la comprobación vigente del ZIP se registra
en `docs/evidencia/verificacion_zip.json` y `docs/evidencia/pruebas_zip.log`.
