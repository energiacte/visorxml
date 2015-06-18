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
        # Limitar tamaño?: image.thumbnail((1500, 1500), Image.ANTIALIAS)
        return b64data
    except Exception:
        return ''

if __name__ == '__main__':
    test1 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="
    test2 = "iVBORw0KGgoAAAANSUhEUgAAAAUAAAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO9TXL0Y4OHwAAAABJRU5ErkJggg=="
    test3 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAIAAAD8GO2jAAAA4UlEQVR4nO2VvQ2DMBCFn6PswASewLPY2yD2sDyEj3/Pl+DGrfd1yp26W7V8B/Aggg==" #Imagen incompleta
    test4 = "data:image/jpg;base64,/9j/4AAQSkZJRgABAQEASABIAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wgARCAAFAAUDAREAAhEBAxEB/8QAFAABAAAAAAAAAAAAAAAAAAAAB//EABUBAQEAAAAAAAAAAAAAAAAAAAcJ/9oADAMBAAIQAxAAAAFHFqa//8QAFRABAQAAAAAAAAAAAAAAAAAABgX/2gAIAQEAAQUCAgUlxJ//xAAfEQACAQQCAwAAAAAAAAAAAAAEBQYBAgMHEyQSFBX/2gAIAQMBAT8B2ztmFxeF6ebt9PRiVhSuMXMkyZlcqoLEBaKowT8xZ7MYY4qj1xMRReqKsx8awfr+PHjH/8QAHREAAQQCAwAAAAAAAAAAAAAABAECAwUREgYTIv/aAAgBAgEBPwGhobE2x5COPyE0CQA1ISCIUn3sH95rO6bQ2F220L3+3zLmZ3rOVd//xAAfEAACAgAHAQAAAAAAAAAAAAADBQEEAgYHEhMUIxH/2gAIAQEABj8C1EXr9RHiGyheRTZMqcX+fMJ++8D3bvC8pkgsEpnP7nu4990vr934y//EABcQAQADAAAAAAAAAAAAAAAAAAEAEUH/2gAIAQEAAT8hey7MoJ1SXKfD/9oADAMBAAIAAwAAABC//8QAFhEBAQEAAAAAAAAAAAAAAAAAAQAR/9oACAEDAQE/EEAftu7v33fynb//xAAVEQEBAAAAAAAAAAAAAAAAAAABAP/aAAgBAgEBPxBOFTLTmYY/9//EABYQAQEBAAAAAAAAAAAAAAAAAAEAEf/aAAgBAQABPxAAyoe60AsMgUP/2Q=="
    
    img = base642img(test1)
    print "* Objeto imagen desde URI (png):", img
    img = base642img(test4)
    print "* Objeto imagen desde URI (jpg):", img
    #img3.show()
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

    print "* Codificación desde nombre de archivo (png):", img2base64('mytest.png')

    print "* Codificación desde nombre de archivo (jpg):", img2base64('mytest.jpg')

    img2 = base642img(test3)
    print "* Cadena con imagen incompleta o corrupta: ", img2











