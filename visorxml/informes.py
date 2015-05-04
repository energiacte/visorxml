#!/usr/bin/env python
# encoding: utf8

"""Definición de entidades para el análisis de informes de resultados en XML"""

import os
import numbers
import lxml.etree
from lxml.html.clean import clean_html
from pygments import highlight
from pygments.lexers.html import XmlLexer
from pygments.formatters import HtmlFormatter
from .imgb64 import base64check


TAGS = {
    'TOPLEVEL': (
        'DatosDelCertificador', 'IdentificacionEdificio',
        'DatosGeneralesyGeometria', 'DatosEnvolventeTermica',
        'InstalacionesTermicas', 'InstalacionesIluminacion', #Es lista
        'Demanda', 'Consumo', 'CondicionesFuncionamientoyOcupacion', # Es lista
        'EmisionesCO2', 'Calificacion', 'MedidasDeMejora',
        'PruebasComprobacionesInspecciones', 'DatosPersonalizados'),
    'LIST': (
        'InstalacionesIluminacion', 'CondicionesFuncionamientoyOcupacion', # Toplevels que son lista
        'CerramientosOpacos', 'Capas', 'HuecosyLucernarios', #EnvolventeTermica
        'GeneradoresDeCalefaccion', 'GeneradoresDeRefrigeracion',
        'InstalacionesACS', 'SistemasSecundariosCalefaccionRefrigeracion',
        'TorresyRefrigeracion', 'VentilacionyBombeo', #InstalacionesTermicas
        'MedidasDeMejora', #MedidasDeMejora
        'PruebasComprobacionesInspecciones'), #PruebasComprobacionesInspecciones
    'BUNCH': (
        'PorcentajeSuperficieAcristalada', #DatosGeneralesyGeometria
        'Elemento', 'Capa', #EnvolventeTermica
        'Espacio', #Instalaciones
        'EdificioObjeto', 'EdificioDeReferencia', 'Exigencias', #Demanda
        'FactoresdePaso', 'FinalAPrimariaNoRenovable', 'FinalAEmisiones',
        'EnergiaFinalVectores', 'GasNatural', 'GasoleoC', 'GLP', 'Carbon',
        'BiomasaOtros', 'BiomasaPellet', 'ElectricidadPeninsular',
        'ElectricidadBaleares', 'ElectricidadCanarias',
        'ElectricidadCeutayMelilla', 'Biocarburante',
        'EnergiaPrimariaNoRenovable', #Consumo
        'EmisionesCO2', 'Demanda', 'Medida', 'CalificacionDemanda',
        'CalificacionEnergiaPrimariaNoRenovable',
        'CalificacionEmisionesCO2', #Calificacion
        'Sistema', #SistemasSecundariosCalefaccionRefrigeracion
        'Visita', #PruebasComprobacionesInspecciones
        'EscalaGlobal', 'EscalaCalefaccion', 'EscalaRefrigeracion'), # v2
    'INT': (
        'NumeroDePlantasBajoRasante',
        'PorcentajeSuperficieHabitableCalefactada',
        'PorcentajeSuperficieHabitableRefrigerada',
        'N', 'NE', 'E', 'SE', 'S', 'SO', 'O', 'NO'), # DatosGenerales # XXX: E es también un float!
    'FLOAT': (
        'SuperficieHabitable', 'VolumenEspacioHabitable', 'Compacidad',
        'DensidadFuentesInternas', 'VentilacionUsoResidencial',
        'VentilacionTotal', #DatosGenerales
        'Superficie', 'Transmitancia', 'FactorSolar', 'PotenciaNominal',
        'RendimientoNominal', #Elemento
        'Espesor', 'ConductividadTermica', 'ResistenciaTermica',
        'Densidad', 'FactorResistenciaVapor', 'CalorEspecifico', #Capa
        'PotenciaCalor', 'PotenciaFrio', 'RendimientoCalor',
        'RendimientoFrio', 'ConsumoDeEnergia', #Sistema
        'PotenciaTotalInstalada', #InstalacionesIluminacion
        'PotenciaInstalada', 'VEEI', 'IluminanciaMedia', #Espacio
        'Conjunta', 'Calefaccion08', 'Refrigeracion08', 'Conjunta08',
        'Ahorro08', 'GlobalDiferenciaSituacionInicial', #Demanda
        'LimiteCalefaccionVivienda', 'LimiteRefrigeracionVivienda',
        'LimiteAhorroOtrosUsos', 'LimiteViviendaGlobalEPNR', #Exigencias
        'DemandaDiariaACS', 'RendimientoEstacional',
        'ConsumoElectrico', 'ConsumoOtros',
        'TotalConsumoElectrico', 'TotalConsumoOtros', 'A', 'B', 'C', 'D', 'E', 'F'), #v2 #XXX: E es también un int
    'FLOAT_OR_TEXT': (
        'Global', 'Calefaccion', 'Refrigeracion', 'ACS', 'Iluminacion'),
    'TEXT': (
        'NombreyApellidos', 'NIF', 'RazonSocial', 'NIFEntidad',
        'Domicilio', 'Municipio', 'CodigoPostal', 'Provincia',
        'ComunidadAutonoma', 'Email', 'Titulacion', 'Fecha', #Certificador
        'NombreDelEdificio', 'Direccion', 'ZonaClimatica', 'AnoConstruccion',
        'ReferenciaCatastral', 'TipoDeEdificio', 'NormativaVigente',
        'Procedimiento', 'AlcanceInformacionXML', #IdentificacionEdificio
        'NumeroDePlantasSobreRasante', #DatosGeneralesyGeometria
        'Nombre', 'Tipo', 'ModoDeObtencion', 'ModoDeObtencionFactorSolar',
        'ModoDeObtencionTransmitancia', 'VectorEnergetico', #Elemento
        'Material', #Capa
        'ZonaAsociada', 'EnfriamientoEvaporativo', 'RecuperacionEnergia',
        'EnfriamientoGratuito', 'TipoControl', 'ServicioAsociado', #Sistema
        'NivelDeAcondicionamiento', 'PerfilDeUso', #Espacio
        'Iluminacion', #EmisionesCO2
        'Descripcion', 'FechaVisita', 'Datos', #Medida
        'Telefono'), #v2
    'IMG': ('Imagen', 'Plano'),
}

XSDPATH = os.path.join(
    os.path.dirname(__file__),
    'static/validador/DatosEnergeticosDelEdificioSchema.xsd')
XSDPATH1 = os.path.join(
    os.path.dirname(__file__),
    'static/validador/DatosEnergeticosDelEdificioSchemav1.xsd')

class Bunch(dict):
    "Contenedor genérico"
    def __init__(self, **kwds):
        dict.__init__(self, kwds)
        self.__dict__ = self
    def __str__(self):
        state = [u"%s=%r" % (attribute, value)
                 for (attribute, value)
                 in self.__dict__.items()]
        return u'\n'.join(state)

class InformeXML(object):
    """Clase que representa un informe de evaluación energética en XML"""
    TAGS = TAGS
    xmlparser = lxml.etree.XMLParser(resolve_entities=False, # no sustituye unicode a entidades
                                     remove_blank_text=True,
                                     ns_clean=True, # limpia namespaces
                                     remove_comments=True)

    def __init__(self, xmldata):
        self.xml = xmldata
        self._xmltree = None
        self._data = None
        self.xmlschema = None

    def validate(self):
        """Valida el informe XML según el esquema XSD"""
        # http://lxml.de/validation.html
        if self.version == '1':
            self.xmlschema = lxml.etree.XMLSchema(lxml.etree.parse(open(XSDPATH1)))
        else:
            self.xmlschema = lxml.etree.XMLSchema(lxml.etree.parse(open(XSDPATH)))
        self.xmlschema.validate(self.xmltree)
        errors = [(error.line, error.message.encode("utf-8"))
                  for error in self.xmlschema.error_log]
        return errors

    @property
    def xmltree(self):
        """Árbol lxml de entidades XML"""
        if self._xmltree is None:
            self._xmltree = lxml.etree.XML(self.xml,
                                           parser=self.xmlparser)
        return self._xmltree

    @property
    def version(self):
        """Version del esquema usado en el informe XML"""
        return self.xmltree.get('version')

    @property
    def imagen(self):
        img = self.xmltree.find('.//Imagen')
        return base64check(img.text) if (img is not None and img.text) else None

    @property
    def plano(self):
        img = self.xmltree.find('.//Plano')
        return base64check(img.text) if (img is not None and img.text) else None

    @property
    def superficieacondicionada(self):
        "Superficie habitable acondicionada"
        dg = self.data.DatosGeneralesyGeometria
        return (dg.SuperficieHabitable *
                float(max(dg.PorcentajeSuperficieHabitableCalefactada,
                          dg.PorcentajeSuperficieHabitableRefrigerada)))
    @property
    def superficies(self):
        return dict((e.Espacio, e.Superficie) for e in self.data.CondicionesFuncionamientoyOcupacion)

    @property
    def potenciamediailum(self):
        """Suma de las superficies de los espacios iluminados"""
        eiluminados = dict((e.Nombre, e) for e in self.data.InstalacionesIluminacion if e.get('Nombre', None))
        superficies = self.superficies
        supiluminada = sum(superficies[e] for e in eiluminados)
        return sum(1.0*superficies[e]*eiluminados[e].PotenciaInstalada / supiluminada for e in eiluminados)

    @property
    def emisionesdatos(self):
        "Datos de emisiones totales para vectores eléctricos y no eléctricos"
        vectores = self.data.Consumo.EnergiaFinalVectores
        factores = self.data.Consumo.FactoresdePaso.FinalAEmisiones
        emisioneselec = sum([sum([vectores.get(vector).get(servicio)
                                  for servicio in vectores.get(vector)]) * factores.get(vector)
                             for vector in vectores if 'Elec' not in vector])
        emisionesnoelec = sum([sum([vectores.get(vector).get(servicio)
                                    for servicio in vectores.get(vector)]) * factores.get(vector)
                               for vector in vectores if 'Elec' in vector])
        return {'EmisionesElec': emisioneselec, 'EmisionesNoElec': emisionesnoelec}

    @property
    def finalservicios(self):
        "Datos de energía final por servicios"
        finalporvectores = self.data.Consumo.EnergiaFinalVectores
        print finalporvectores
        efinal = {}
        for vector in finalporvectores:
            data = finalporvectores[vector]
            print "vector: ", vector, "data: ", data
            for servicio in data:
                efinal[servicio] = efinal.get(servicio, 0.0) + data[servicio]
        return efinal

    @property
    def data(self):
        """Objeto etree correspondiente al informe XML"""
        if self._data is None:
            self._data = self._parsetree(self.xmltree)
        return self._data

    @property
    def astext(self):
        """Contenido del informe como texto"""
        #print lxml.etree.tostring(child, encoding='unicode')
        data = [self.version,]
        for section in self.TAGS['TOPLEVEL']:
            data.append(u'%s\n' % section +
                        u'=' * len(section) +
                        u'\n' + str(self.data.get(section)) +
                        u"\n")
        data.append(u'Potenciamediailum\n===========\n' +
                    str(self.potenciamediailum) +
                    u"\n")
        return '\n'.join(data)

    @property
    def ashtml(self):
        """Contenido del informe como HTML resaltado"""
        return highlight(self.xml,
                         XmlLexer(),
                         HtmlFormatter(noclasses=True))

    def _parsetree(self, xmltree):
        """Genera un objeto a partir de la descripción XML"""
        def parseCDATA(element):
            """Genera imagen a partir de CDATA

            http://en.wikipedia.org/wiki/Data_URI_scheme

            <img src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAUA
            AAAFCAYAAACNbyblAAAAHElEQVQI12P4//8/w38GIAXDIBKE0DHxgljNBAAO
            9TXL0Y4OHwAAAABJRU5ErkJggg==" alt="Red dot" />

            FF, Opera, Chrome, Safari, IE8, IE9 soportan este protocolo.
            IE8 no admite más de 32kB de datos.
            """
            return element.text

        obj = Bunch()
        for child in xmltree:
            tag, text = child.tag, child.text
            if tag == 'InstalacionesIluminacion':
                obj[tag] = [self._parsetree(elem) for elem in child if elem.tag != 'PotenciaTotalInstalada']
                obj[tag].append(Bunch(**{'PotenciaTotalInstalada': float(child.find('PotenciaTotalInstalada').text)}))
            # Algunos toplevel son listas, por eso va esto antes
            elif tag in self.TAGS['LIST']:
                obj[tag] = [self._parsetree(elem) for elem in child]
            elif tag in self.TAGS['BUNCH'] or tag in self.TAGS['TOPLEVEL']:
                if tag == 'DatosPersonalizados':
                    obj[tag] = child #lxml.etree.tostring(child)
                # Nombre de espacio dentro de un espacio en CondicionesFuncionamientoyOcupacion
                elif tag == 'Espacio' and text:
                    obj[tag] = text
                elif tag in ['FinalAEmisiones', 'FinalAPrimariaNoRenovable']:
                    obj[tag] = Bunch(**dict((elem.tag, float(elem.text)) for elem in child))
                else:
                    obj[tag] = self._parsetree(child)
            elif tag in self.TAGS['FLOAT_OR_TEXT']:
                if not text: continue
                try:
                    obj[tag] = float(text)
                except ValueError:
                    obj[tag] = text
            elif tag in self.TAGS['INT']:
                if not text: continue
                try:
                    obj[tag] = int(text)
                except ValueError:
                    obj[tag] = 9999999999
            elif tag in self.TAGS['FLOAT']:
                if not text: continue
                try:
                    obj[tag] = float(text)
                except ValueError:
                    obj[tag] = 9999999999.99
            elif tag in self.TAGS['IMG']:
                if not text: continue
                obj[tag] = parseCDATA(child)
            elif tag in self.TAGS['TEXT']:
                if not text: continue
                # El campo "Descripcion" en las medidas puede ser HTML
                if text.startswith('data:/text/html,'):
                    text = text.lstrip('data:/text/html,')
                    text = clean_html(text)
                obj[tag] = text
            else:
                raise Exception("ERROR en etiqueta: %s, o contenido incorrecto: %s" % (tag, text))
        return obj

def analize(informe):
    """Analiza contenidos de un Informe XML en busca de posibles errores"""
    dd = informe.data
    zci =  dd.IdentificacionEdificio.ZonaClimatica[:-1]
    zcv = dd.IdentificacionEdificio.ZonaClimatica[-1]
    esvivienda = 'Vivienda' in dd.IdentificacionEdificio.TipoDeEdificio

    info = []
    if (sum(informe.superficies.values()) > dd.DatosGeneralesyGeometria.SuperficieHabitable):
        info.append(('ERROR', u'Superficies habitable menor que suma de la superficie de los espacios'))
    if zcv not in '1234':
        info.append(('ERROR', u'Zona climática de verano incorrecta'))
    if zci not in ['A', 'B', 'C', 'D', 'E', 'alfa', 'alpha']:
        info.append(('ERROR', u'Zona climática de invierno incorrecta'))

    plano_ = dd.DatosGeneralesyGeometria.get('Plano', None)
    if not plano_:
        info.append(('AVISO', u'Sin datos de plano'))
    elif not base64check(plano_):
        info.append(('AVISO', u'Datos de plano incorrectos'))

    imagen_ = dd.DatosGeneralesyGeometria.get('Imagen', None)
    if not imagen_:
        info.append(('AVISO', u'Sin datos de imagen'))
    elif not base64check(imagen_):
        info.append(('AVISO', u'Datos de imagen incorrectos'))

    if ((0 > dd.DatosGeneralesyGeometria.PorcentajeSuperficieHabitableCalefactada > 100)
        or (0 > dd.DatosGeneralesyGeometria.PorcentajeSuperficieHabitableRefrigerada > 100)):
        info.append(('ERROR', u'Porcentajes de superficies acondicionadas fuera de rango'))

    if esvivienda:
        # Sin chequear
        if (zcv == '1'
            and (dd.Demanda.EdificioDeReferencia.Refrigeracion
                 or dd.EmisionesCO2.Calificacion.EmisionesCO2.Refrigeracion
                 or dd.Calificacion.EmisionesCO2.Refrigeracion
                 or dd.Calificacion.Demanda.Refrigeracion
                 or dd.Calificacion.EnergiaPrimariaNoRenovable.Refrigeracion)):
            info.append(('ERROR', u'Zona sin demanda de refrigeración de referencia'))
        # Sin chequear
        if (zci in ('alpha', 'alfa', 'a')
            and (dd.Demanda.EdificioDeReferencia.Calefaccion
                 or dd.EmisionesCO2.Calificacion.EmisionesCO2.Calefaccion
                 or dd.Calificacion.EmisionesCO2.Calefaccion
                 or dd.Calificacion.Demanda.Calefaccion
                 or dd.Calificacion.EnergiaPrimariaNoRenovable.Calefaccion)):
            info.append(('ERROR', u'Zona sin demanda de calefacción de referencia'))

    if not esvivienda:
        if not informe.data.InstalacionesTermicas.get('SistemasSecundariosCalefaccionRefrigeracion', None):
            info.append(('AVISO', u'No se han definido sistemas secundarios de calefacción y/o refrigeración'))
        if not informe.data.InstalacionesTermicas.get('VentilacionyBombeo'):
            info.append(('AVISO', u'No se han definido sistemas de ventilación y bombeo'))

    def _visit(res, ckey, obj):
        "Incluye en res la lista de valores numéricos con sus etiquetas"
        if isinstance(obj, numbers.Number):
            res.append((obj, ckey))
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                _visit(res, ckey, item)
        elif isinstance(obj, (Bunch,)):
            for key in obj:
                _visit(res, key, obj[key])

    values = []
    _visit(values, 'root', informe.data)
    suspects = [key for (value, key) in values if value > 9999999]
    if suspects:
        info.append(('AVISO', u'Valores numéricos erróneos en : %s' % ', '.join(set(suspects))))

    return info

