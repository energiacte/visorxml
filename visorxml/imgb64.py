#!/usr/bin/env python
#encoding:utf8

"""Utilidades de manejo de archivos de imagen en codificación base64

http://stackoverflow.com/questions/19908975/loading-base64-string-into-python-image-library
http://stackoverflow.com/questions/3715493/encoding-an-image-file-with-base64
"""

import cStringIO
import base64
import PIL.Image

def img2base64(filename):
    """Cadena de datos en base64 a partir de archivo de imagen"""
    with open(filename, "rb") as image_file:
        b64string = base64.b64encode(image_file.read())
    return b64string.decode()

def base642img(b64data):
    """Recupera datos de imagen codificados en una URI o cadena en base64

    data:[<MIME-type>][;charset=<encoding>][;base64],<data>
    """
    try:
        data = b64data.split(',', 1)[1] if b64data.startswith('data:') else b64data
        image_string = cStringIO.StringIO(base64.b64decode(data))
        image = PIL.Image.open(image_string)
        image.load()
        return image
    except Exception:
        return None

def base64check(b64data):
    """Comprueba si se define una imagen válida"""
    try:
        data = b64data.split(',', 1)[1] if b64data.startswith('data:') else b64data
        image_string = cStringIO.StringIO(base64.b64decode(data))
        image = PIL.Image.open(image_string)
        image.load()
        return b64data
    except Exception:
        return ''

if __name__ == '__main__':
    test1 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="
    test2 = "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="
    test3 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAA4UlEQVR4nO2VvQ2DMBCFn6PswASewLPY2yD2sDyEj3/Pl+DGrfd1yp26W7V8B/Aggg=="

    img = base642img(test1)
    print "* Objeto imagen desde URI:", img
    #img.show()

    img = base642img(test2)
    print "* Objeto imagen desde datos en base64:", img

    print "* Guardando imagen"
    img.save('mytest.png')

    print "* Codificación de la imagen como cadena base64:",
    output = cStringIO.StringIO()
    img.save(output, 'png')
    contents = output.getvalue()
    encodedbuf = base64.b64encode(contents)
    print encodedbuf

    print "* Codificación desde nombre de archivo:", img2base64('mytest.png')

    img2 = base642img(test3)
    print "* Cadena con imagen incompleta o corrupta: ", img2











