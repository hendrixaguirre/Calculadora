# AXION — Validación de Programa 3

> Registro histórico de la validación inicial, anterior a la depuración.
> Los nombres de rutas reflejan la estructura de aquel momento. La revisión
> actual está en `DEPURACION.md`; las mediciones de geometría se consolidaron
> en `evidencia/geometria.json`.

Fecha: 17 de septiembre de 2026. Grupo 5. Esta revisión distingue pruebas
ejecutadas, inspección visual y comprobaciones todavía no realizadas.

## Inspección y continuidad

Se leyeron los módulos reales `axion_core.py`, `axion_ui.py`, `axion_storage.py`,
los lanzadores de Programa 1 y 2, `test_programa.py` y la documentación previa.
Todos estaban sin seguimiento en Git; no se hicieron resets ni borrados.
La copia local `evidencia/base_programa2.zip` conserva los archivos principales
antes de modificarlos. Se contrastó la consigna original de dos páginas ubicada
en Descargas: `Tarea 3 (Elaboracion Programa 3_Python).pdf`.

La línea base actual fue **80 pruebas aprobadas**, no las 44 del antecedente.
Registro: `evidencia/baseline_programa2.log` (13.822 s).

## Archivos implementados y motivo

| Archivo | Cambio |
|---|---|
| `axion_operaciones.py` | Validaciones comunes, operaciones manuales de vectores/matrices, producto con tres bucles, adaptador Ax=b, vectores como columnas para combinación, resultados estructurados, detalle bajo demanda y reportes. |
| `axion_workbench.py` | Editores ttk, borradores por operación, tres etapas, selección de celda/componente, invalidez tras editar, pegado TSV atómico, dimensiones, deshacer, desplazamiento y exportaciones. |
| `axion_programa3.py` | Extiende AplicacionAxion con cuatro módulos y navegación; conserva el cuaderno de sistemas y unifica historial/atajos. |
| `axion_core.py` | Rechaza espacios internos ambiguos; marca aproximaciones y formatea racionales grandes mediante enteros sin desbordar float. El algoritmo de eliminación se conserva. |
| `axion_ui.py` | Valida dimensiones manuales, amplía celdas de resultados largos y permite que Programa 1/2 comparta un historial que incluye nuevas operaciones. |
| `axion_storage.py` | Integra operaciones en JSON local validado con versiones, límites y escritura atómica; conserva registros de sistemas. |
| `Programa 3_Grupo 5.py` | Lanzador académico, con diagnóstico si falta Tk o sesión gráfica. |
| `test_programa3.py` | 34 pruebas nuevas con unittest; mantiene las 80 anteriores sin eliminar casos. |
| `validar_visual_programa3.py` | Herramienta opcional de QA para abrir escenarios reales, registrar geometría y medir el entorno. Usa historial temporal. |
| `README.md` | Uso actual, contrato de entrada, límites, atajos y distinción entre dependencias de app y herramientas documentales. Conserva referencia histórica de Programa 2. |
| `QA_PROGRAMA3.md` | Este registro de cierre verificable. |
| `evidencia/` | Logs, capturas reales, geometría, mediciones y generador documental separado de AXION. |
| `entrega/Informe_Programa 3_Grupo 5.pdf` | PDF real de 7 páginas, renderizado y revisado. Explicación técnica: páginas 2–3. |

## Requisitos implementados

- Vectores: suma, resta y producto por escalar; componentes exactas e inspección.
- Matrices: suma/resta con formas iguales, escalar y producto rectangular AB.
  Se rechaza la incompatibilidad antes de construir resultados.
- Combinación: n y k independientes, V con vectores como columnas, mismo motor
  de sistemas, respuesta de existencia/unicidad y parametrización. Se verifican
  la particular y **todas** las direcciones, no solo una elección de parámetros.
- Sistemas: se conserva Gauss y Gauss-Jordan, rectangularidad, pivotes/rangos,
  familias, operaciones registradas y RREF completa en inconsistencia.
- Fracciones exactas y presentación aproximada identificada; ningún cálculo
  algebraico usa bibliotecas externas ni APIs. Importar el motor no abre Tk.
- Borradores por módulo/operación; resultado anterior identificado al editar.
- Edición reversible, confirmación antes de reducir valores, pegado completo
  validado antes de aplicar, y restauración exacta de ejercicios resueltos.
- Historial local acotado y exportaciones TXT/HTML autocontenidas. El HTML no se
  presenta como PDF; el informe académico se produce por separado.

## Comandos ejecutados y resultados

```powershell
python --version
python -m unittest -q
python -m unittest -v test_programa3
python -m unittest -v
python -m py_compile axion_core.py axion_operaciones.py axion_ui.py axion_workbench.py axion_programa3.py axion_storage.py "Programa 3_Grupo 5.py" test_programa3.py
git diff --check
python evidencia/medir_programa3.py
python validar_visual_programa3.py --escenario ocho --geometria 1024x768 --cerrar 1
python validar_visual_programa3.py --escenario producto --geometria 1280x720 --cerrar 1
python validar_visual_programa3.py --escenario producto --geometria 1366x768 --cerrar 1
python validar_visual_programa3.py --escenario producto --geometria 1920x1080 --cerrar 1
python validar_visual_programa3.py --escenario ocho --geometria 820x720 --cerrar 1
```

Suite ampliada: **114 pruebas, 0 fallos, 0 omisiones**, 63.689 s en la ejecución
detallada; otra ejecución completa terminó en 70.300 s. Los tiempos incluyen
creación/destrucción de ventanas Tk y varían con la actividad gráfica del equipo.
Registros: `evidencia/pruebas_detalladas.log` y `evidencia/pruebas_completas.log`.
La compilación terminó sin errores. `git diff --check` no informó errores,
pero los archivos siguen sin seguimiento: ese comando no representa una revisión
del contenido de los archivos nuevos.

Los casos A–K del encargo se ejecutaron, incluidos AB=[[58,64],[139,154]],
c=(2,3), la imposibilidad con b=(2,3,6), la familia c=(3,0)+t(-2,1),
la solución (2,3,-1) y la RREF inconsistente [[1,1,0],[0,0,1]].
Además: dimensiones 1 y 8, identidad/cero, distributividad, negativos y fracciones,
inmutabilidad, columnas sin pivote, intercambios, sistemas rectangulares,
reconstrucción de pasos, familias completas, corruptos/permisos y estados de UI.
Un comando independiente confirmó que importar `axion_operaciones` no carga
`tkinter` en `sys.modules`.

## Entorno y rendimiento

- Windows 11, compilación 10.0.26200; Python 3.14.6; Tcl/Tk 8.6.15.
- App con DPI awareness: pantalla informada 1920×1080, Tk scaling 1.6683087.
- `GetDpiForWindow`: **120 DPI, Windows 125 %**. No se alteró el escalado.
- La prueba inicial sin DPI awareness informó pantalla virtualizada 1536×864 y
  Tk scaling 1.334647; no es otro escalado físico de Windows.
- Producto A 2×3 por B 3×2: media de cálculo **0.04367 ms**, 1000 repeticiones.
- Renderizado de vistas sobre widgets ya existentes: **3.64143 ms**, 10
  repeticiones. Excluye inicio de la app e historial. `rendimiento.json` contiene
  mediciones y método; no son garantías para otros casos/equipos.

## Revisión visual real

Se inspeccionaron capturas de ventanas Tk reales mediante control de escritorio:

| Evidencia | Lo observado |
|---|---|
| `multiplicacion.png` | Resultado 2×2 y selección c[1,2], productos 8+20+36=64; fila y columna identificadas. |
| `incompatibilidad.png` | A 2×3, B 2×2 y mensaje explícito de incompatibilidad; sin resultado parcial. |
| `combinacion_lineal.png` | Sí existe, coeficientes (2,3), rangos 2 y 2 y comprobación por componente. |
| `familia.png` | Sí existe con infinitas representaciones, particular/dirección y comprobación de toda la familia. |
| `vectores.png` | Suma (2,3,2) y desarrollo (1/2)+(3/2)=2. |
| `sistemas.png` | Cuaderno heredado, clasificación inconsistente, contradicción y rangos diferenciados. |
| `ocho_820x720.png` | Editor 8×8, cambio de operando en ventana estrecha y desplazamiento. |
| `fracciones_1024x768.png` | Fracción extensa visible completa y desplazamiento local. |

La revisión detectó y corrigió recortes en acciones y detalle: se reservaron filas
fijas para controles del resultado y se añadió desplazamiento al editor. En
anchos estrechos se alterna el operando sin destruirlo. Las matrices extensas
se recorren localmente; no se reduce toda la tipografía para que quepan.

Capturas académicas: área cliente **1366×900**. También se inspeccionaron ventanas
1280×720, 1024×768 y 820×720. Se registró geometría para 1366×768 y 1920×1080;
esto no equivale a revisión visual completa. Un cliente de 1920×1080 excede el
área útil al añadir los bordes del sistema operativo. Los JSON conservan tamaño
cliente real y escala. Los escenarios de QA usan el código productivo; el título
QA identifica el ejercicio abierto, no una pantalla simulada.

Se probó Ctrl+Enter con el motor real (abre Paso 1) y Alt+Derecha (avanza a Paso 2).
La suite prueba navegación, selección, edición, invalidación, deshacer y cambios
de formato. Queda pendiente completar manualmente todas las rutas sin ratón,
probar lectores de pantalla y escalados físicos 100 %, 150 % y 200 %.
No se declara accesibilidad integral ni compatibilidad comprobada fuera de Windows.

## Informe y paquete

Datos confirmados: Grupo 5; docente José Munguia; Fanor Velasquez S,
Hendrix Aguirre y Jarold Montealto. No se inventaron apellidos adicionales.
El nombre del ZIP usa Velasquez y Aguirre para los dos campos de apellidos de la
convención indicada; la portada incluye a los tres integrantes.

Informe PDF verdadero: portada; dos páginas técnicas; tres páginas de capturas
en horizontal para facilitar lectura; ejecución/validación. Se revisaron sus
siete páginas renderizadas con Poppler y se corrigieron glifos de subíndices.
El generador usa herramientas documentales preinstaladas del entorno; no forma
parte de la calculadora ni del paquete fuente. El código de la app es estándar.

ZIP comprobado: se extrajo en una carpeta temporal con espacios y acentos;
las 114 pruebas aprobaron y el lanzador real abrió Tk y completó el mainloop
con cierre automático (código de salida 0). La revisión AST de dependencias
confirmó solo biblioteca estándar en los módulos entregados. No se requieren
rutas absolutas del equipo. Registro local: `evidencia/pruebas_zip.log`. No se ha publicado ni enviado ningún archivo a Moodle u otro servicio.
