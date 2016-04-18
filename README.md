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

* pdfdetach (`$ sudo aptitude install poppler-utils`)

* nodejs (`$ sudo aptitude install nodejs`)
    * npm (`$ sudo aptitude install npm`)
    * bower (`$ npm install -g bower`)
    * grunt (`$ npm install -g grunt-cli`)

* python (>= 3.4) (`$ sudo aptitude install python3`)
    * pip (`$ sudo aptitude install python3-pip`)

Pasos de instalación:

* Instalar las dependencias de PIP en un entorno virtual (llamado `venvvisorxml`):
    * Dependencias para compilación de módulos (`$ sudo aptitude install build-essential python3-dev libxml2-dev libxslt-dev libffi-dev zlib1g-dev libjpeg-dev libopenjp-2-7-dev`)
    * `$ pyvenv venvvisorxml` # suponemos usuario `usuariovisorxml`
    * `$ pip install -r requirements.txt`
* Instalar las dependencias de bower:
    * git para acceso a repositorios (`$ sudo aptitude install git`)
        * NOTA: si un firewall bloquea URLs de git, indicar uso de https: (`$ git config --global url."https://".insteadOf git://`)
    * `$ bower install`
* Instalar las dependencias de npm:
    * `$ npm install`
* Ejecutar grunt para construir la aplicación:
    * `$ grunt`
* Configuración del servidor web para ejecutar la aplicación WSGI
    * apache-mod-wsgi (`$ sudo aptitude install apache2 libapache2-mod-wsgi-py3`)
    * Ejemplo de configuración para apache2 bajo la ruta `/visorxml` de la URL base:
        ```
        # Visor XML
        WSGIDaemonProcess visorxml python-path=/var/www/visorxml:/home/usuariovisorxml/venvvisorxml/lib/python3.4/site-packages user=www-data group=www-data threads=5
        WSGIScriptReloading On
        WSGIScriptAlias /visorxml /var/www/visorxml/visorxml.wsgi process-group=visorxml

        <Directory /var/www/visorxml>
                WSGIProcessGroup visorxml
                WSGIApplicationGroup %{GLOBAL}
                Require all granted
        </Directory>
        # FIN VisorXML
        ```

