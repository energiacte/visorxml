# encoding: utf8
"""Variables de configuración generales de la aplicación.
En la configuración de instancia se fijan las variables que no deben
guardarse en el sistema de control de versiones."""

import os

DEBUG = True # Turns on debugging features in Flask
UPLOADS_DEFAULT_DEST = os.path.join(os.path.dirname(__file__), 'uploads')
LOG_FILE = os.path.join(os.path.dirname(__file__), 'uploads/visorxmlfiles.log')
ALLOWED_EXTENSIONS = set(['txt', 'xml', 'ctexml']) # extensiones válidas
MAX_CONTENT_LENGTH = 16 * 1024 * 1024 # máxima longitud de archivo 16MB
