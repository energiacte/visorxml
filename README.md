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
- Descarga de informes en formato PDF
- Incorporación de medidas de mejora a partir de un archivo XML base y archivos XML con medidas de mejora aplicadas
- Edición de campos del XML que no son generados mediante simulación energética

Instalación
-----------

La aplicación está desarrollada en lenguaje Python y Javascript para algunos aspectos del frontend. Se basa en la plataforma Django y PhantomJS para la generación de archivos PDF.

Requisitos de instalación:

* nodejs
    * npm
    * bower
    * grunt

* python (>= 3.4)
    * pip

Pasos de instalación:

* Instalar las dependencias de PIP:
    * `$ pip install -r requirements.txt`
* Instalar las dependencias de bower:
    * `$ bower`
* Instalar las dependencias de npm:
    * `$ npm install`
* Ejecutar grunt para construir la aplicación:
    * `$ grunt`
* Configuración del servidor web para ejecutar la aplicación WSGI

