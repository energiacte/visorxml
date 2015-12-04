XMLReport (reports.py) -> La función 'analize' llevárnoslo a XMLReports, para poder gestionar las notificaciones
(warnings y errores) con más comodidad

Añadir valores especiales para poder mostrar en el informe cuándo un campo calculado es erróneo.

Ver la posibilidad de generar PDFs híbridos con el XML empotrado

- Hacer editables más campos administrativos
- Edición enriquecida de algunos campos de texto (memorias)
- Sustituir sinimagen.png por SVG
- Evitar excepciones al crear medida de mejora cuando no existan datos suficientes (hacer testfile)
- Marcar los XML modificados añadiendo cadena en <Procedimiento>: p.e. + visorxml1.0_20151107
- Espaciador al final de los informes
- Cambiar cadena de visorxml 1.0 -> VisorXML v1.0
- Los campos editables deben abarcar el ancho de su celda

IDEAS para versiones posteriores
================================

- PDF híbridos
    1. Empaquetar archivos
        - `pdftk informe.pdf attach_file informe.xml output informe_xml.pdf`
    2. Desempaquetar archivos
        1. `pdftk  informe_xml.pdf  unpack_files`
        2. `pdfdetach -list informe_xml.pdf; pdfdetach -save 1 informe_xml.pdf` o `pdfdetach -saveall informe_xml.pdf`, usando `pdfdetach`de poppler-utils
- Posibilidad de añadir anexo de justificación de soluciones singulares
- Traducción de la interfaz a lenguas cooficiales
- Permitir añadir o eliminar bloques de "visitas, inspecciones o comprobaciones", con botones de añadir o eliminar inline (overlay)
- Comprobación y mejora de capacidades de edición de texto enriquecido (con imágenes) en secciones CDATA (controlar tamaño de imagen, sanear y serializar a CDATA)
- Comprobar tamaños/resolución de imágenes en campos de imagen (igual ya está).

- Eliminar página intermedia de selección de archivos, evitando validación previa independiente
    - mover la entrada de archivo XML a parte superior de informe de certificación
    - mover entrada de XML adicionales a zona de bloques de medidas de mejora (noprint), eliminando (botón de) validación expresa
    - uso de mensajes, avisos y errores en bloques inline que se muestran al ir seleccionando archivos (no se imprimen).
- Marcar imágenes editables con un overlay (lápiz). ¿Hacer lo mismo para los otros campos?
- Mover el botón de descarga de XML al encabezado
- Añadir icono de descarga a los botones de descarga de PDF y XML (flecha abajo o similar)
- Permitir eliminar medidas de mejora

- Implementación de sistema para firma y registro, con un formulario intermedio adicional, si fuese necesario (¿Interfaz REST para gestionar los registros?)
- Nuevas comprobaciones de tipo energético (predimensionado)
- Comprobaciones básicas adicionales:
    - rendimientos anómalos (p.e. > 500%)
    - número total de plantas = 0
    - no hay definidos puentes térmicos
    - no hay definidos circuitos de bombas o ventiladores en edificios terciarios (para Calener GT)
    - no hay demanda de ACS definida
- Indicar en informe adicional el nivel de cumplimiento cuando haya restricciones DB-HE con ticks o cruces
- Integrar testsuite para funciones de validación, generación de medidas de mejora, parseado, etc, independiente de la interfaz web
- Informe de costes a partir de datos de precios (usar precios de medios de referencia?) y consumos finales
- Poner en color distinto cuando el XML ha sido modificado por el visorxml

