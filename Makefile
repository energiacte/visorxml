run:
	DJANGO_SETTINGS_MODULE=visorxml.settings.development PATH=$(abspath ./node_modules/.bin):${PATH} venv/bin/python visorxml/manage.py runserver

collectstatic:
	grunt
	DJANGO_SETTINGS_MODULE=visorxml.settings.development venv/bin/python visorxml/manage.py collectstatic --noinput --clear

compilelang:
	cd visorxml && ../venv/bin/django-admin compilemessages

updatelang:
	cd visorxml && ../venv/bin/django-admin makemessages -a

createlang:
	cd visorxml && ../venv/bin/django-admin makemessages -l es -l gl -l ca -l eu

install:
	python3 -m venv venv
	venv/bin/python -m pip install -Ur requirements.txt
	mkdir -p visorxml/media/
	mkdir -p visorxml/served-static/
	npm install
	grunt

installpackages:
	sudo aptitude install python3 python3-pip nodejs npm poppler-utils gettext build-essential python3-dev libxml2-dev libxslt-dev libffi-dev zlig1g-dev  libjpeg-dev libopenjp-2-7-dev
	sudo npm install -g grunt-cli

