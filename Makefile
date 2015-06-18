SHELL := /bin/bash

RUSER:=pachi
RHOST:=recoletos

VENV:=~/.virtualenvs/visorxml
SITEDIR:=${VENV}/lib/python2.7/site-packages

run:
	if [ `echo ${VIRTUAL_ENV}|grep visorxml` ]; then echo 'Entorno virtual activo'; else . ${VENV}/bin/activate; fi && \
	PYTHONPATH=. ./visorxml/runserver.py;
#	. ${VENV}/bin/activate; \
#	PYTHONPATH=. ./visorxml/runserver.py;

venv: requirements.txt
	test -d ${VENV} || virtualenv --no-site-packages ${VENV}
	. ${VENV}/bin/activate; pip install -r requirements.txt
#	touch ${VENV}/bin/activate
#	touch requirements.txt

updateenv: venv
	. ${VENV}/bin/activate; \
		pip install -Ur requirements.txt; \
		cp requirements.txt requirements.txt.bak; \
		pip freeze > requirements.txt

#Para instalar añadir a la configuración activa del sitio en apache lo siguiente (sin virtualhost)
#
# <VirtualHost *>
#    ##ServerName validador.codigotecnico.org
#     WSGIDaemonProcess www-data user=www-data group=www-data threads=5
#     WSGIScriptAlias /visorxml/ /var/www/visorxml/visorxml.wsgi
#     WSGIScriptReloading On
#     <Directory /var/www/visorxml>
#         WSGIProcessGroup www-data
#         WSGIApplicationGroup %{GLOBAL}
#         Order deny,allow
#         Allow from all
#     </Directory>
# </VirtualHost>

# NOTE: El archivo visorxml/visorxml.wsgi incluye la ruta al entorno virtual en ${VENV}
# sudo apt-get install python-pip python-dev build-essential
# sudo pip install --upgrade pip
# sudo apt-get install libapache2-mod-wsgi
#	aptitude install libxml2-dev libxslt-dev libffi-dev
#	Hay que hacer pip install -U -r requirements.txt en el host destino con el entorno activado, para instalar todo
upload:
	scp -r requirements.txt $(RUSER)@$(RHOST):~
	ssh -t -A $(RUSER)@$(RHOST) "mkdir -p ${VENV}/var/visorxml-instance/"
	scp visorxml/visorxml.wsgi $(RUSER)@$(RHOST):~
	ssh -t -A $(RUSER)@$(RHOST) "sudo mkdir -p /var/www/visorxml && \
								 mkdir -p ${SITEDIR}/visorxml/uploads && \
								 sudo mv visorxml.wsgi /var/www/visorxml/ && \
								 sudo chown www-data:www-data /var/www/visorxml/visorxml.wsgi && \
								 sudo chown -R www-data:www-data ${SITEDIR}/visorxml/uploads && \
								 sudo touch ${SITEDIR}/visorxml/visorxmlfiles.log && \
								 sudo chown www-data:www-data ${SITEDIR}/visorxml/visorxmlfiles.log && \
								 sudo chmod -R ug+rw ${SITEDIR}/visorxml/uploads"
	scp -r visorxml/ $(RUSER)@$(RHOST):${SITEDIR}
	scp -r instance/visorxml.cfg $(RUSER)@$(RHOST):${VENV}/var/visorxml-instance/visorxml.cfg

remoteclean:
	ssh -t -A $(RUSER)@$(RHOST) "find ${SITEDIR}/visorxml/uploads -iname '*.xml' -exec rm -rf '{}' \; && \
								 cp /dev/null ${SITEDIR}/visorxml/uploads/visorxmlfiles.log"

clean:
	find visorxml/uploads -iname '*.xml' -exec rm -rf '{}' \;
	cp /dev/null visorxml/uploads/visorxmlfiles.log

.PHONY: run
