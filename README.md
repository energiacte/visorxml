VisorXML
========

VisorXML es una aplicación web para la visualización y edición de informes de eficiencia energética en formato electrónico (XML).

La aplicación ha sido desarrollada en el marco del convenio entre el Ministerio de Fomento y el Instituto de Ciencias de la Construcción Eduardo Torroja (IETcc-CSIC), del Consejo Superior de Investigaciones Científicas (CSIC).

El código se distribuye bajo una licencia libre (MIT), que permite el uso, modificación y distribución del código original y modificado, según se especifica en los archivos LICENSE.txt y LICENSE_ES.txt.

Funcionalidad
-------------

- Validación de archivos de eficiencia energética en formato electrónico (XML)
- Avisos sobre potenciales problemas en el XML suministrado (inconsistencias, valores atípicos, etc)
- Generación y visualización del certificado de eficiencia energética
- Generación y visualización de un informe adicional de eficiencia energética
- Descarga de informes en formato PDF (con XML incrustado) y XML
- Incorporación de medidas de mejora a partir de un archivo XML base y archivos XML con medidas de mejora aplicadas
- Edición de campos del XML que no son generados mediante simulación energética
- Corrección de errores de formato en archivos XML

Instalación
-----------

La aplicación está desarrollada en lenguaje Python y Javascript para algunos aspectos del frontend. Se basa en la plataforma Django y PhantomJS para la generación de archivos PDF.

Requisitos de instalación (paquetes de sistema suponiendo Debian/jessie(stable)):

* pdfdetach (`$ sudo apt install poppler-utils`)

* nodejs (`$ sudo apt install nodejs`)
    * npm (`$ sudo apt install npm`)
    * grunt (`$ npm install -g grunt-cli`)

* python (>= 3.4) (`$ sudo apt install python3 python3-pip python3-venv python3-dev`)
    * pip
    * venv
    * dev

Pasos de instalación:

* Instalación de las dependencias de PIP en un entorno virtual (llamado `venv`):
    * Dependencias para compilación de módulos (`$ sudo aptitude install build-essential libxml2-dev libxslt-dev libffi-dev zlib1g-dev libjpeg-dev libopenjp2-7-dev`)
    * `$ python3 -m venv venv` # suponemos usuario `usuariovisorxml`
    * `$ venv/bin/python -m pip install -Ur requirements.txt`
* Crea directorios de contenido de usuario y estático
    * `$ mkdir -p visorxml/media/`
    * `$ mkdir -p visorxml/served-static/`
* Instalar las dependencias de npm:
    * `$ npm install`
* Ejecutar grunt (instalada por npm) para construir la aplicación:
    * `$ npx grunt`
* Configuración del servidor web para ejecutar la aplicación WSGI
    * apache-mod-wsgi (`$ sudo apt install apache2 libapache2-mod-wsgi-py3`)
    * Ejemplo de configuración para apache2 bajo la ruta `/visorxml` de la URL base:
        ```
        # Visor XML
        WSGIDaemonProcess visorxml python-path=/var/www/visorxml:/home/usuariovisorxml/venv/lib/python3.4/site-packages user=www-data group=www-data threads=5
        WSGIScriptReloading On
        WSGIScriptAlias /visorxml /var/www/visorxml/visorxml.wsgi process-group=visorxml

        <Directory /var/www/visorxml>
                WSGIProcessGroup visorxml
                WSGIApplicationGroup %{GLOBAL}
                Require all granted
        </Directory>
        # FIN VisorXML
        ```

