#!/usr/bin/env python
# encoding: utf8

"""Aplicación VisorXML"""

from flask import Flask
from flask.ext.bootstrap import Bootstrap
from flask.ext.uploads import configure_uploads
from visorxml.models import datafiles

app = Flask(__name__, instance_relative_config=True)
app.config.from_object('visorxml.default_settings')
app.config.from_pyfile('visorxml.cfg')
Bootstrap(app)
configure_uploads(app, (datafiles,))

import visorxml.views
