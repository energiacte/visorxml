#!/usr/bin/env python
#encoding:utf-8
#
# Copyright (c) 2015 Ministerio de Fomento
#                    Instituto de Ciencias de la Construcción Eduardo Torroja (IETcc-CSIC)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#

import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SECRET_KEY = '#kt=jt)e0s%+hd#s7r%h*dlycro9%t0&jcghn8tw@soc$_p!sr'

DEBUG = True

ALLOWED_HOSTS = []

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'jquery',
    'djangoformsetjs',
    'visorxml',
    'generadorxml'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.security.SecurityMiddleware',
)

ROOT_URLCONF = 'visorxml.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, '..', 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'visorxml.wsgi.application'

DATABASES = {
}

SESSION_ENGINE = 'django.contrib.sessions.backends.signed_cookies'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': "[%(asctime)s] %(levelname)s %(message)s",
            'datefmt': "%d/%b/%Y %H:%M:%S"
        }
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(BASE_DIR, '..', 'visorxml.log'),
            'formatter': 'verbose'
        },
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'propagate': True,
            'level': 'DEBUG',
        },
        'visorxml': {
            'handlers': ['file'],
            'level': 'DEBUG',
        },
    }
}

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, '..', 'served-static') # A donde va collectstatic
STATICFILES_DIRS = (
    os.path.join(BASE_DIR, '..', 'static'),
) # Donde se buscan cosas para collectstatic

MEDIA_ROOT = os.path.join(BASE_DIR, '..', 'media')
MEDIA_URL = '/media/'

# VISOR_XML SETTINGS
VERSION = '1.0'

XSDPATH2 = os.path.join(BASE_DIR, '..', 'static', 'docs', 'DatosEnergeticosDelEdificioSchema20.xsd')
XSDPATH1 = os.path.join(BASE_DIR, '..', 'static', 'docs', 'DatosEnergeticosDelEdificioSchema10.xsd')
XSDPATH_MINI  = os.path.join(BASE_DIR,'..', 'generadorxml', 'doc', 'DatosEnergeticosDelEdificioMini10.xsd')
MINI_XML_PATH = os.path.join(BASE_DIR,'..', 'generadorxml', 'doc', 'baseXML.xml')

from django.utils.translation import ugettext_lazy as _

LOCALE_PATHS = (
    os.path.join(BASE_DIR, '..', 'locale'),
)

LANGUAGES = [
    ('es', _('Castellano')),
    ('ca', _('Catalán')),
    ('eu', _('Euskera')),
    ('gl', _('Gallego')),
]
