import base64

from django import template

from visorxml.reports import ALERT

register = template.Library()

def _getcalif(report, value, scale_type):
    """Calcula letra para el valor, dentro de una escala"""

    if scale_type == 'EnergiaPrimariaNoRenovable':
        scale = report.data.Calificacion.EnergiaPrimariaNoRenovable.EscalaGlobal
    elif scale_type == 'EmisionesCO2':
        scale = report.data.Calificacion.EmisionesCO2.EscalaGlobal
    elif scale_type == 'DemandaCalefaccion':
        scale = report.data.Calificacion.Demanda.EscalaCalefaccion
    elif scale_type == 'DemandaRefrigeracion':
        scale = report.data.Calificacion.Demanda.EscalaRefrigeracion

    calif = 'G'
    for letra in 'A B C D E F'.split():
        limsup = getattr(scale, letra)
        if value < limsup:
            calif = letra
            break

    catlimits = {letra: getattr(scale, letra) for letra in 'A B C D E F'.split()}

    return calif, catlimits


@register.simple_tag
def scalevalue(value, report, scale_type='EnergiaPrimariaNoRenovable'):
    """Devuelve el valor de la escala aplicable al valor que se pasa por parámetro"""
    calif, catlimits = _getcalif(report, value, scale_type)

    return calif


@register.simple_tag
def escalasvg(value, report, scale_type='EnergiaPrimariaNoRenovable'):
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

    try:
        value = float(value)
        califnum = "{0:.2f}".format(value).replace('.', ',') if value else ''
        calif, catlimits = _getcalif(report, value, scale_type)

        ypos = 17 * {
            'A': 0,
            'B': 1,
            'C': 2,
            'D': 3,
            'E': 4,
            'F': 5,
            'G': 6
        }[calif]
        svgdata = SVGTEXT.format(ypos=ypos,
                                 ypostxt=ypos + 11,
                                 califnum=califnum,
                                 calif=calif,
                                 limits=catlimits)
    except:
        ypos, ypostxt, califnum, calif = None, None, None, None
        svgdata = SVGERROR

    encoded_string = base64.b64encode(svgdata.encode('utf-8'))
    return "data:image/svg+xml;charset=utf-8;base64,{}".format(encoded_string.decode())

@register.filter
def asnum(value):
    "Devuelve un valor numérico con dos decimales"
    try:
        val = float(value)
        res = '{:0.2f}'.format(val).replace('.', ',') if val <= ALERT else '-'
    except:
        res = '-'
    return res

@register.filter
def asint(value):
    "Devuelve un valor entero"
    try:
        val = int(value)
        res = '{0:d}'.format(int(val)) if val <= ALERT else '-'
    except:
        res = '-'
    return res

@register.filter
def aspct(value):
    "Devuelve un porcentaje a partir del tanto por uno"
    try:
        val = 100.0 * float(value)
        res = '{:0.2f}'.format(val).replace('.', ',') if val <= ALERT else '-'
    except:
        res = '-'
    return res

@register.filter
def difwith(valuedest, valueorig):
    try:
        res1 = float(valueorig) - float(valuedest)
        res2 = 100.0 * res1 / float(valueorig)
        return '{:0.2f}<br />({:0.2f}%)'.format(res1, res2).replace('.', ',')
    except:
        return '-'
