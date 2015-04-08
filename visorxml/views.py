#!/usr/bin/env python
# encoding: utf8

"""Vistas de la aplicación VisorXML"""
#import locale
#locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

import base64
import datetime
import hashlib
from flask import (request, session, #g, abort, flash
                   redirect, url_for, render_template,
                   send_file)
from visorxml import app
from visorxml.models import XMLFileForm, datafiles
from visorxml.informes import InformeXML, analize

@app.route('/')
def index():
    "Página de presentación"
    return render_template("index.html")

@app.route('/validador/', methods=['GET', 'POST'])
def validador():
    "Valida archivos de informe en XML"
    form = XMLFileForm()
    if form.validate_on_submit() and not form.errors:
        filedata = request.files['file']
        session['filename'] = filedata.filename
        #XXX: usar, no la sesión del usuario sino los hashes de archivos almacenados en una BBDD
        #Guardamos solamente el nuevo archivo si no coincide con el de la actual sesión
        hashkey = hashlib.md5(filedata.read()).hexdigest()
        filedata.seek(0) # rebobinamos tras leer
        if session.get('hashkey') != hashkey:
            session['hashkey'] = hashkey
            session['storedfilename'] = datafiles.save(filedata)
            filedata.seek(0) # rebobinamos el stream después de guardar
        informe = InformeXML(filedata.read())
        errors = informe.validate()
        info = analize(informe)
        session['validationerrors'] = errors
        session['info'] = info
        # Guardamos datos en el registro
        with open(app.config['LOG_FILE'], 'a') as logfile:
            dt = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
            haserrors = "ERROR" if errors else "OK"
            logfile.write("%s, %s, %s, %s, %s\n" % (dt,
                                                    request.remote_addr,
                                                    session['filename'],
                                                    session['storedfilename'],
                                                    haserrors))
        return redirect(url_for('validador'))
    #session['info'] = ''
    return render_template('validador.html',
                           form=form)

@app.route('/visor/', methods=['GET', 'POST'])
def visor():
    "Visualiza archivos de informe en XML"
    if session.get('storedfilename') and not session.get('validationerrors'):
        with open(datafiles.path(session['storedfilename'])) as xmlfile:
            informe = InformeXML(xmlfile.read())
    else:
        informe = None
    return render_template('visor.html',
                           informe=informe,
                           modo='data') # modo = raw,text,html,data

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    "Devuelve el contenido del archivo en el directorio de uploads"
    filedata = datafiles.path(filename)
    return send_file(filedata)

@app.template_filter('escalasvg')
def escalasvg(value, calif='G'):
    """Devuelve imagen de la escala y su calificación como SVG inline"""
    califnum = ("%.2f" % value).replace('.', ',') if value else ''
    calif = calif or 'G'
    ypos = 17 * {'A':0, 'B':1, 'C':2, 'D':3, 'E':4, 'F':5, 'G':6}[calif]
    ypostxt = ypos + 11

    SVGTEXT = """<svg xmlns='http://www.w3.org/2000/svg' width="175" height="120">
  <g id="layer1" stroke="none">
    <path d="m 174,{ypos:d} -53,0 -11,7 11,7 53,0 z" fill="#black" />
    <text x="170" y="{ypostxt:d}" id="calif" style="font-size:12px;font-weight:bold;text-align:end;text-anchor:end;fill:white;font-family:Arial">
    {califnum} {calif}
    </text>
    <path d="m 0,0 57,0 7,7 -7,7 -57,0 z" fill="#00a651" />
    <path d="m 0,17 64,0 7,7 -7,7 -64,0 z" fill="#4cb847" />
    <path d="m 0,34 71,0 7,7 -7,7 -71,0 z" fill="#bfd630" />
    <path d="m 0,51 78,0 7,7 -7,7 -78,0 z" fill="#fff100" />
    <path d="m 0,68 85,0 7,7 -7,7 -85,0 z" fill="#feb811" />
    <path d="m 0,85 92,0 7,7 -7,7 -92,0 z" fill="#f36f23" />
    <path d="m 0,102 99,0 7,7 -7,7 -99,0 z" fill="#ee1c25" />
    <text x="45" y="11" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">A</text>
    <text x="52" y="28" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">B</text>
    <text x="59" y="45" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">C</text>
    <text x="66" y="62" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">D</text>
    <text x="73" y="79" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">E</text>
    <text x="80" y="96" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">F</text>
    <text x="87" y="113" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">G</text>
  </g>
</svg>"""
    svgdata = SVGTEXT.format(ypos=ypos,
                             ypostxt=ypostxt,
                             califnum=califnum,
                             calif=calif)
    return "data:image/svg+xml;charset=utf-8;base64," + base64.b64encode(svgdata)
