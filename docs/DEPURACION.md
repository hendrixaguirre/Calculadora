# Depuración de AXION

La revisión conserva las funciones de Programa 3 y ordena el proyecto para
mantenerlo y entregarlo sin archivos auxiliares mezclados con el programa.

## Código

- Eliminada la rutina privada `_eliminacion_hacia_atras`, sin llamadas. Gauss
  conserva su sustitución hacia atrás y Gauss-Jordan utiliza su reducción RREF.
- Eliminadas importaciones sin uso y la función redundante para convertir
  fracciones a texto. Las pruebas importan explícitamente lo que utilizan.
- Extraída la validación de operaciones para que cargar el historial compruebe
  los datos sin resolver nuevamente cada combinación lineal almacenada.
- Unificado el arranque gráfico y conservada la compatibilidad de la función
  pública de inicio anterior. La consola se abre con el único lanzador actual
  y `--cli`; su código vive en `axion_cli.py` y no importa Tk.

## Archivos

- Pruebas en `tests/`, herramientas en `herramientas/` y revisión en `docs/`.
- Versiones anteriores, sus lanzadores y documentación reunidos en
  `archivo_programa2.zip`, con nueve archivos y comprobación de integridad.
- Eliminadas cachés de Python, renders de revisión, registros intermedios
  duplicados y una copia repetida de la base anterior. Las trece mediciones de
  geometría se conservan juntas en `evidencia/geometria.json`.
- README actualizado y reglas para ignorar nuevas cachés y archivos temporales.
- Entrega reducida al código activo, pruebas, README e informe PDF. El
  empaquetador comprueba el contenido extraído antes de sustituir el ZIP.

## Comprobación

Antes de los cambios aprobaron las 114 pruebas existentes (39,109 segundos).
Se conservaron todas y se añadieron tres regresiones para verificar el arranque
por consola, sus límites de dimensión y la carga del historial sin recalcular.
El registro vigente de ejecución y arranque del ZIP está en
`evidencia/pruebas_zip.log` y `evidencia/verificacion_zip.json`.

Resultado final: 117 pruebas aprobadas, sin fallos ni omisiones, ejecutadas
sobre el ZIP extraído. El lanzador real completó el arranque y cierre gráfico
con código 0. Los 16 archivos Python del proyecto compilan y la herramienta
de revisión visual conserva su entrada por consola tras el cambio de carpeta.
El ZIP contiene 14 archivos frente a los 43 anteriores. El proyecto queda en
37 archivos, excluyendo los metadatos internos de Git.

No se modificaron los datos del historial del usuario. El informe PDF y las
capturas conservan la validación inicial: esta depuración no cambia el diseño
de la interfaz ni los resultados matemáticos esperados.
