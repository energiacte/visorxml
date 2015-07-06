#!/usr/bin/env python
# encoding: utf8

"""Vistas de la aplicación VisorXML"""
#import locale
#locale.setlocale(locale.LC_ALL, 'es_ES.UTF-8')

import os
import base64
import datetime
import hashlib
from flask import (request, session, #g, abort, flash
                   redirect, url_for, render_template,
                   send_file, make_response)
from flask_weasyprint import HTML, CSS, render_pdf
from visorxml import app
from visorxml.models import XMLFileForm, datafiles
from visorxml.informes import InformeXML, analize, ALERT

@app.route('/')
def index():
    "Página de presentación"
    return render_template("index.html")

@app.route('/validador/', methods=['GET', 'POST'])
def validador():
    "Valida archivos de informe en XML"
    #TODO: recoger y validar archivos con medidas de mejora
    #TODO: guardar archivos usando hash y así evitar guardar storedfilename
    #TODO: En vez de un informe tendremos una lista de informes,
    #TODO: con el informe base y los de las medidas de mejora.
    #TODO: En vez de guardar en la sesión del usuario los datos, usamos los hashes de archivos almacenados en una BBDD
    #TODO: Guardamos solamente el nuevo archivo si no coincide con el de la actual sesión
    form = XMLFileForm()
    if form.validate_on_submit() and not form.errors:
        data = request.files['base']
        xmldata = data.read()
        data.seek(0) # rebobinamos tras leer       
        session['base_name'] = data.filename
        hashkey = hashlib.md5(xmldata).hexdigest()
        if (session.get('base_hashkey') != hashkey
            or not os.path.exists(datafiles.path(session['base_storedname']))):
            session['base_hashkey'] = hashkey
            session['base_storedname'] = datafiles.save(data)
            #data.seek(0) # rebobinamos el stream después de guardar
        informe = InformeXML(xmldata)
        session['base_validationerrors'] = informe.validate()
        session['base_info'] = analize(informe)
        # Guardamos datos en el registro
        with open(app.config['LOG_FILE'], 'a') as logfile:
            dt = datetime.datetime.strftime(datetime.datetime.now(), '%Y-%m-%d %H:%M:%S')
            haserrors = "ERROR" if session['base_validationerrors'] else "OK"
            logfile.write("%s, %s, %s, %s, %s\n" % (dt,
                                                    request.remote_addr,
                                                    session['base_name'],
                                                    session['base_storedname'],
                                                    haserrors))
        return redirect(url_for('validador'))
        #session['base_info'] = ''n
    return render_template('validador.html',
                           form=form)

@app.route('/visor/', methods=['GET', 'POST'])
def visor():
    "Visualiza archivos de informe en XML"
    if (session.get('base_storedname')
        and not session.get('base_validationerrors')
        and os.path.exists(datafiles.path(session['base_storedname']))):
        with open(datafiles.path(session['base_storedname'])) as xmlfile:
            informe = InformeXML(xmlfile.read())
    else:
        return redirect(url_for('validador'))
    return render_template('visor.html',
                           informe=informe,
                           modo='data') # modo = raw,text,html,data

@app.route('/pdf/')
def getpdf():
    "Informe en formato PDF"
    if (session.get('base_storedname')
        and not session.get('base_validationerrors')
        and os.path.exists(datafiles.path(session['base_storedname']))):
        with open(datafiles.path(session['base_storedname'])) as xmlfile:
            informe = InformeXML(xmlfile.read())
        html = render_template('visor.html', informe=informe, modo='data print')
        #HTML(string=html).write_pdf('/home/pachi/salida.pdf', stylesheets=[CSS(string='#fotos img {width:5cm;}')])
        pdf_filename = session['base_name'].rsplit('.xml', 1)[0] + '.pdf'
        resp = make_response(render_pdf(HTML(string=html),
                                        download_filename=pdf_filename))
        # cookie bandera para jquery.fileDownload.js
        resp.set_cookie('fileDownload', 'true', path='/')
        return resp
    else:
        return redirect(url_for('validador'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    "Devuelve el contenido del archivo en el directorio de uploads"
    filedata = datafiles.path(filename)
    return send_file(filedata)

@app.template_filter('asnum')
def asnum(value):
    "Devuelve un valor numérico con dos decimales"
    try:
        val = float(value)
        res = '{:0.2f}'.format(val).replace('.', ',') if val <= ALERT else '-'
    except:
        res = '-'
    return res

@app.template_filter('aspct')
def aspct(value):
    "Devuelve un porcentaje a partir del tanto por uno"
    try:
        val = 100.0 * float(value)
        res = '{:0.2f}'.format(val).replace('.', ',') if val <= ALERT else '-'
    except:
        res = '-'
    return res

@app.template_filter('asint')
def asint(value):
    "Devuelve un valor entero"
    try:
        val = int(value)
        res = '{0:d}'.format(int(val)) if val <= ALERT else '-'
    except:
        res = '-'
    return res

@app.template_filter('ascalif')
def ascalif(value):
    return value if value else '-'

@app.template_filter('difwith')
def difwith(valuedest, valueorig):
    try:
        res1 = float(valueorig) - float(valuedest)
        res2 = 100.0 * res1 / float(valueorig)
        return '{:0.2f}<br />({:0.2f}%)'.format(res1, res2).replace('.', ',')
    except:
        return '-'

@app.template_filter('escalasvg')
def escalasvg(value, informe, tipoescala='EnergiaPrimariaNoRenovable'):
    """Devuelve imagen de la escala y su calificación como SVG inline"""

    SVGTEXT = """<svg xmlns='http://www.w3.org/2000/svg' width="185" height="120">
<g id="layer1" stroke="none">
<path d="m 184,{ypos:d} -53,0 -11,7 11,7 53,0 z" fill="#black" />
<text x="180" y="{ypostxt:d}" id="calif" style="font-size:12px;font-weight:bold;text-align:end;text-anchor:end;fill:white;font-family:Arial">
{califnum} {calif}</text>
<path d="m 0,0 67,0 7,7 -7,7 -67,0 z" fill="#00a651" />
<path d="m 0,17 74,0 7,7 -7,7 -74,0 z" fill="#4cb847" />
<path d="m 0,34 81,0 7,7 -7,7 -81,0 z" fill="#bfd630" />
<path d="m 0,51 88,0 7,7 -7,7 -88,0 z" fill="#fff100" />
<path d="m 0,68 95,0 7,7 -7,7 -95,0 z" fill="#feb811" />
<path d="m 0,85 102,0 7,7 -7,7 -102,0 z" fill="#f36f23" />
<path d="m 0,102 109,0 7,7 -7,7 -109,0 z" fill="#ee1c25" />
<text x="55" y="11" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">A</text>
<text x="5" y="11" style="font-size:9px;font-weight:bold;fill:white;font-family:Arial">&#60; {limits[A]:.2f}</text>
<text x="62" y="28" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">B</text>
<text x="5" y="28" style="font-size:9px;font-weight:bold;fill:white;font-family:Arial">{limits[A]:.2f} - {limits[B]:.2f}</text>
<text x="69" y="45" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">C</text>
<text x="5" y="45" style="font-size:9px;font-weight:bold;fill:white;font-family:Arial">{limits[B]:.2f} - {limits[C]:.2f}</text>
<text x="76" y="62" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">D</text>
<text x="5" y="62" style="font-size:9px;font-weight:bold;fill:white;font-family:Arial">{limits[C]:.2f} - {limits[D]:.2f}</text>
<text x="83" y="79" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">E</text>
<text x="5" y="79" style="font-size:9px;font-weight:bold;fill:white;font-family:Arial">{limits[D]:.2f} - {limits[E]:.2f}</text>
<text x="90" y="96" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">F</text>
<text x="5" y="96" style="font-size:9px;font-weight:bold;fill:white;font-family:Arial">{limits[E]:.2f} - {limits[F]:.2f}</text>
<text x="97" y="113" style="font-size:12px;font-weight:bold;fill:white;font-family:Arial">G</text>
<text x="5" y="113" style="font-size:9px;font-weight:bold;fill:white;font-family:Arial">&#8805; {limits[F]:.2f}</text>
</g>
</svg>"""

    SVGERROR = """<svg xmlns='http://www.w3.org/2000/svg' width="175" height="120">
<g id="layer1" stroke="none">
<path d="m 2 2 173 0 0 118 -173 0 z" stroke="gray" fill="none" />
<path d="m 2 2 173 118 M 0 118 l 178 -118" stroke="gray" fill="none" />
<text x="85" y="60" id="calif" style="font-size:12px;font-weight:bold;text-align:center;text-anchor:middle;fill:black;font-family:Arial">Sin valor para calificación</text>
</g>
</svg>
"""

    def _getcalif(value, escala):
        """Calcula letra para el valor, dentro de una escala"""
        for letra in 'A B C D E F'.split():
            limsup = getattr(escala, letra)
            if value < limsup:
                calif = letra
                break
        else: # caso de salir sin break del for
            calif = 'G'
        return calif

    if tipoescala == 'EnergiaPrimariaNoRenovable':
        escala = informe.data.Calificacion.EnergiaPrimariaNoRenovable.EscalaGlobal
    elif tipoescala == 'EmisionesCO2':
        escala = informe.data.Calificacion.EmisionesCO2.EscalaGlobal
    elif tipoescala == 'DemandaCalefaccion':
        escala = informe.data.Calificacion.Demanda.EscalaCalefaccion
    elif tipoescala == 'DemandaRefrigeracion':
        escala = informe.data.Calificacion.Demanda.EscalaRefrigeracion
        
    try:
        value = float(value)
        califnum = "{0:.2f}".format(value).replace('.', ',') if value else ''
        calif = _getcalif(value, escala)
        catlimits = {letra: getattr(escala, letra) for letra in 'A B C D E F'.split()}
        ypos = 17 * {'A':0, 'B':1, 'C':2, 'D':3, 'E':4, 'F':5, 'G':6}[calif]
        svgdata = SVGTEXT.format(ypos=ypos,
                                 ypostxt=ypos + 11,
                                 califnum=califnum,
                                 calif=calif,
                                 limits=catlimits)
    except:
        ypos, ypostxt, califnum, calif = None, None, None, None
        svgdata = SVGERROR

    return "data:image/svg+xml;charset=utf-8;base64," + base64.b64encode(svgdata)
