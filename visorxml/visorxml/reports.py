#!/usr/bin/env python
# encoding: utf8

"""Definición de entidades para el análisis de informes de resultados en XML"""

import os.path
import hashlib
import numbers
from collections import OrderedDict, defaultdict
from decimal import Decimal

from django.conf import settings

import lxml.etree
from lxml.html.clean import clean_html

from .imgb64 import base64check

XSDPATH2 = settings.XSDPATH2
XSDPATH1 = settings.XSDPATH1

VECTORES = ('GasNatural GasoleoC GLP Carbon BiomasaPellet BiomasaOtros '
            'ElectricidadPeninsular ElectricidadBaleares '
            'ElectricidadCanarias ElectricidadCeutayMelilla Biocarburante').split()
SERVICIOS = 'Global Calefaccion Refrigeracion ACS Iluminacion'.split()
NIVELESESCALA = 'A B C D E F'.split()
ALERTINT = 9999999999
ALERTFLOAT = ALERTINT + 0.99
ALERT = ALERTINT / 100


class Bunch(OrderedDict):
    """Contenedor genérico"""

    def __init__(self, *args, **kwds):
        super(Bunch, self).__init__()

    def __str__(self):
        state = ['%s=%s' % (attribute, value)
                 for (attribute, value) in self.__dict__.items()
                 if not attribute.startswith('_OrderedDict')]
        return '\n'.join(state)


def astext(tree, path):
    element = tree.find(path)
    if element is None or not element.text:
        return '-'
    txt = element.text
    if txt and txt.startswith('data:text/html,'):
        txt = txt.lstrip('data:text/html,').strip()
        txt = clean_html(txt) if txt else ''
    return txt


def asint(tree, path):
    element = tree.find(path)
    if element is None or not element.text:
        return None
    try:
        val = int(element.text)
    except ValueError:
        val = ALERTINT
    return val


def asfloat(tree, path):
    element = tree.find(path)
    if element is None or not element.text:
        return None
    try:
        val = float(element.text)
    except ValueError:
        val = ALERTFLOAT
    return val


class XMLReport(object):
    def __init__(self, xml_strings):
        '''
        xml_strings es una lista de tuplas. Las tuplas son de la forma (nombre_fichero, contenido)
        '''
        self.xml_parser = lxml.etree.XMLParser(resolve_entities=False,  # no sustituye unicode a entidades
                                               remove_blank_text=True,
                                               ns_clean=True,  # limpia namespaces
                                               remove_comments=True)

        self.xmlschema = None
        self.errors = {
            'extra_files_errors': None,
            'validation_errors': [],
            'info': None
        }
        self._data = None
        self._xml_strings = xml_strings

        self.xmltree = self.get_xmltree()
        if self.xmltree is not None:
            self.calculate_improvement_measures()
            self._parsetree()

            self.validate()
            self.analize()

    def save_to_file(self, filename=None):
        xml_string = lxml.etree.tostring(self.xmltree, pretty_print=True)
        if filename is None:
            filename = hashlib.md5(xml_string).hexdigest()

        path = settings.MEDIA_ROOT

        with open(os.path.join(path, filename), 'wb') as output_file:
            output_file.write(xml_string)

        return filename

    def update_element(self, element, value):
        path = './%s' % '/'.join(element.split('.'))
        try:
            self.xmltree.find(path).text = value

            procedimiento = self.xmltree.find('./IdentificacionEdificio/Procedimiento')
            if procedimiento is not None and 'visorxml' not in procedimiento.text:
                procedimiento.text += ' - visorxml %s' % settings.VERSION

            base_xml_filename, base_xml_string = self._xml_strings[0]
            self.save_to_file(base_xml_filename)
        except AttributeError:
            pass

    def update_image(self, section, value):
        path = './DatosGeneralesyGeometria/%s' % section
        try:
            element = self.xmltree.find(path)
            if element is None:
                parent = self.xmltree.find('./DatosGeneralesyGeometria')
                element = lxml.etree.SubElement(parent, section)

            element.text = lxml.etree.CDATA('data:image/png;base64,%s' % value.decode("utf-8"))

            procedimiento = self.xmltree.find('./IdentificacionEdificio/Procedimiento')
            if procedimiento is not None and 'visorxml' not in procedimiento.text:
                procedimiento.text += ' - visorxml %s' % settings.VERSION

            base_xml_filename, base_xml_string = self._xml_strings[0]
            self.save_to_file(base_xml_filename)
        except AttributeError as e:
            print('cacola', e)
            pass

    def get_XML_value(self, xml_tree, path, default_value=0):
        try:
            return xml_tree.find(path).text
        except AttributeError:
            return default_value

    def get_xmltree(self):
        # Get the base XML data
        base_xml_filename, base_xml_string = self._xml_strings[0]
        try:
            base_xml_tree = lxml.etree.XML(base_xml_string, parser=self.xml_parser)
            return base_xml_tree
        except lxml.etree.XMLSyntaxError:
            error = (None, 'El archivo "<strong>%s</strong>" no está correctamente formateado' % base_xml_filename)
            self.errors['validation_errors'].append(error)
            return None

    def calculate_improvement_measures(self):
        # Loop over the xml strings list, except the first element, which is the base file
        for improvement_xml_filename, improvement_xml_string in self._xml_strings[1:]:
            try:
                improvement_xml_tree = lxml.etree.XML(improvement_xml_string, parser=self.xml_parser)
            except lxml.etree.XMLSyntaxError:
                error = (None, 'El archivo "<strong>%s</strong>" no está correctamente formateado' % improvement_xml_filename)
                self.errors['validation_errors'].append(error)
                continue

            improvement_xml_fragment = lxml.etree.Element('Medida')

            lxml.etree.SubElement(improvement_xml_fragment, 'Nombre').text = 'NOMBRE'
            lxml.etree.SubElement(improvement_xml_fragment, 'Descripcion').text = 'DESCRIPCION'
            lxml.etree.SubElement(improvement_xml_fragment, 'CosteEstimado').text = 'COSTE ESTIMADO'
            lxml.etree.SubElement(improvement_xml_fragment, 'OtrosDatos').text = 'OTROS DATOS'

            self.check_building_properties(improvement_xml_filename,
                                           improvement_xml_tree)

            self.improvement_fragment_add_demanda(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_calificacion_demanda(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_energia_final(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_energia_primaria_no_renovable(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_calificacion_energia_primaria_no_renovable(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_emisiones_co2(improvement_xml_tree, improvement_xml_fragment)
            self.improvement_fragment_add_calificacion_emisiones_co2(improvement_xml_tree, improvement_xml_fragment)

            self.append_improvement_fragment(improvement_xml_fragment)

    def check_building_properties(self, improvement_xml_filename, improvement_xml_tree):
        attrs_to_check = {
            './IdentificacionEdificio/Direccion': 'Direccion',
            './IdentificacionEdificio/Municipio': 'Municipio',
            './IdentificacionEdificio/CodigoPostal': 'CodigoPostal',
            './IdentificacionEdificio/Provincia': 'Provincia',
            './IdentificacionEdificio/ComunidadAutonoma': 'ComunidadAutonoma',
            './IdentificacionEdificio/ZonaClimatica': 'ZonaClimatica',
            './IdentificacionEdificio/ReferenciaCatastral': 'ReferenciaCatastral'
        }

        errors = []
        for attr, attr_name in attrs_to_check.items():
            main_tree_value = self.xmltree.find(attr).text
            value = improvement_xml_tree.find(attr).text
            if main_tree_value != value:
                errors.append('"%s" no coincide con el archivo base' % attr_name)

        if len(errors) > 0:
            if self.errors['extra_files_errors'] is None:
                self.errors['extra_files_errors'] = {}
            self.errors['extra_files_errors'][improvement_xml_filename] = errors

    def improvement_fragment_add_demanda(self, improvement_xml_tree, improvement_xml_fragment):
        base_demanda = Decimal(self.get_XML_value(self.xmltree,
                                                  './Demanda/EdificioObjeto/Global'))
        improvement_demanda = Decimal(self.get_XML_value(improvement_xml_tree,
                                                         './Demanda/EdificioObjeto/Global'))
        diff = improvement_demanda - base_demanda

        improvement_calefaccion = Decimal(self.get_XML_value(improvement_xml_tree,
                                                             './Demanda/EdificioObjeto/Calefaccion'))
        improvement_refrigeracion = Decimal(self.get_XML_value(improvement_xml_tree,
                                                               './Demanda/EdificioObjeto/Refrigeracion'))

        element = lxml.etree.SubElement(improvement_xml_fragment, 'Demanda')
        lxml.etree.SubElement(element, 'Global').text = '%s' % improvement_demanda
        lxml.etree.SubElement(element, 'GlobalDiferenciaSituacionInicial').text = '%s' % diff
        lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % improvement_calefaccion
        lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % improvement_refrigeracion

    def improvement_fragment_add_calificacion_demanda(self, improvement_xml_tree, improvement_xml_fragment):
        calefaccion = self.get_XML_value(improvement_xml_tree, './Calificacion/Demanda/Calefaccion')
        refrigeracion = self.get_XML_value(improvement_xml_tree, './Calificacion/Demanda/Refrigeracion')

        element = lxml.etree.SubElement(improvement_xml_fragment, 'CalificacionDemanda')
        lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % calefaccion
        lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % refrigeracion

    def improvement_fragment_add_energia_final(self, improvement_xml_tree, improvement_xml_fragment):
        servicios = defaultdict(int)
        for vec in VECTORES:
            for servicio in SERVICIOS:
                servicios[servicio] += Decimal(self.get_XML_value(improvement_xml_tree,
                                                                  './Consumo/EnergiaFinalVectores/%s/%s' % (vec, servicio)))

        element = lxml.etree.SubElement(improvement_xml_fragment, 'EnergiaFinal')
        for servicio, valor in servicios.items():
            lxml.etree.SubElement(element, servicio).text = '%s' % valor

    def improvement_fragment_add_energia_primaria_no_renovable(self,
                                                               improvement_xml_tree,
                                                               improvement_xml_fragment):
        element = lxml.etree.SubElement(improvement_xml_fragment, 'EnergiaPrimariaNoRenovable')

        energia_global = Decimal(self.get_XML_value(improvement_xml_tree, './Consumo/EnergiaPrimariaNoRenovable/Global'))
        energia_global_base = Decimal(self.get_XML_value(self.xmltree, './Consumo/EnergiaPrimariaNoRenovable/Global'))
        energia_calefaccion = Decimal(self.get_XML_value(improvement_xml_tree, './Consumo/EnergiaPrimariaNoRenovable/Calefaccion'))
        energia_refrigeracion = Decimal(self.get_XML_value(improvement_xml_tree, './Consumo/EnergiaPrimariaNoRenovable/Refrigeracion'))
        energia_acs = Decimal(self.get_XML_value(improvement_xml_tree, './Consumo/EnergiaPrimariaNoRenovable/ACS'))
        energia_iluminacion = Decimal(self.get_XML_value(improvement_xml_tree, './Consumo/EnergiaPrimariaNoRenovable/Iluminacion'))
        diff = energia_global - energia_global_base

        lxml.etree.SubElement(element, 'Global').text = '%s' % energia_global
        lxml.etree.SubElement(element, 'GlobalDiferenciaSituacionInicial').text = '%s' % diff
        lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % energia_calefaccion
        lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % energia_refrigeracion
        lxml.etree.SubElement(element, 'ACS').text = '%s' % energia_acs
        lxml.etree.SubElement(element, 'Iluminacion').text = '%s' % energia_iluminacion

    def improvement_fragment_add_calificacion_energia_primaria_no_renovable(self,
                                                                            improvement_xml_tree,
                                                                            improvement_xml_fragment):
        element = lxml.etree.SubElement(improvement_xml_fragment, 'CalificacionEnergiaPrimariaNoRenovable')

        energia_global = self.get_XML_value(improvement_xml_tree, './Calificacion/EnergiaPrimariaNoRenovable/Global', None)
        energia_calefaccion = self.get_XML_value(improvement_xml_tree, './Calificacion/EnergiaPrimariaNoRenovable/Calefaccion', None)
        energia_refrigeracion = self.get_XML_value(improvement_xml_tree, './Calificacion/EnergiaPrimariaNoRenovable/Refrigeracion', None)
        energia_acs = self.get_XML_value(improvement_xml_tree, './Calificacion/EnergiaPrimariaNoRenovable/ACS', None)
        energia_iluminacion = self.get_XML_value(improvement_xml_tree, './Calificacion/EnergiaPrimariaNoRenovable/Iluminacion', None)

        if energia_global:
            lxml.etree.SubElement(element, 'Global').text = '%s' % energia_global
        if energia_calefaccion:
            lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % energia_calefaccion
        if energia_refrigeracion:
            lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % energia_refrigeracion
        if energia_acs:
            lxml.etree.SubElement(element, 'ACS').text = '%s' % energia_acs
        if energia_iluminacion:
            lxml.etree.SubElement(element, 'Iluminacion').text = energia_iluminacion

    def improvement_fragment_add_emisiones_co2(self, improvement_xml_tree, improvement_xml_fragment):
        element = lxml.etree.SubElement(improvement_xml_fragment, 'EmisionesCO2')

        emisiones_global = Decimal(self.get_XML_value(improvement_xml_tree, './EmisionesCO2/Global'))
        emisiones_global_base = Decimal(self.get_XML_value(self.xmltree, './EmisionesCO2/Global'))
        emisiones_calefaccion = Decimal(self.get_XML_value(improvement_xml_tree, './EmisionesCO2/Calefaccion'))
        emisiones_refrigeracion = Decimal(self.get_XML_value(improvement_xml_tree, './EmisionesCO2/Refrigeracion'))
        emisiones_acs = Decimal(self.get_XML_value(improvement_xml_tree, './EmisionesCO2/ACS'))
        emisiones_iluminacion = Decimal(self.get_XML_value(improvement_xml_tree, './EmisionesCO2/Iluminacion'))
        diff = emisiones_global - emisiones_global_base

        lxml.etree.SubElement(element, 'Global').text = '%s' % emisiones_global
        lxml.etree.SubElement(element, 'GlobalDiferenciaSituacionInicial').text = '%s' % diff
        lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % emisiones_calefaccion
        lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % emisiones_refrigeracion
        lxml.etree.SubElement(element, 'ACS').text = '%s' % emisiones_acs
        lxml.etree.SubElement(element, 'Iluminacion').text = '%s' % emisiones_iluminacion

    def improvement_fragment_add_calificacion_emisiones_co2(self, improvement_xml_tree, improvement_xml_fragment):
        element = lxml.etree.SubElement(improvement_xml_fragment, 'CalificacionEmisionesCO2')

        emisiones_global = self.get_XML_value(improvement_xml_tree, './Calificacion/EmisionesCO2/Global', None)
        emisiones_calefaccion = self.get_XML_value(improvement_xml_tree, './Calificacion/EmisionesCO2/Calefaccion', None)
        emisiones_refrigeracion = self.get_XML_value(improvement_xml_tree, './Calificacion/EmisionesCO2/Refrigeracion', None)
        emisiones_acs = self.get_XML_value(improvement_xml_tree, './Calificacion/EmisionesCO2/ACS', None)
        emisiones_iluminacion = self.get_XML_value(improvement_xml_tree, './Calificacion/EmisionesCO2/Iluminacion', None)

        if emisiones_global:
            lxml.etree.SubElement(element, 'Global').text = '%s' % emisiones_global
        if emisiones_calefaccion:
            lxml.etree.SubElement(element, 'Calefaccion').text = '%s' % emisiones_calefaccion
        if emisiones_refrigeracion:
            lxml.etree.SubElement(element, 'Refrigeracion').text = '%s' % emisiones_refrigeracion
        if emisiones_acs:
            lxml.etree.SubElement(element, 'ACS').text = '%s' % emisiones_acs
        if emisiones_iluminacion:
            lxml.etree.SubElement(element, 'Iluminacion').text = '%s' % emisiones_iluminacion

    def append_improvement_fragment(self, improvement_xml_fragment):
        if improvement_xml_fragment is not None:
            improvement_measures = self.xmltree.find('./MedidasDeMejora')
            if improvement_measures is None:
                improvement_measures = lxml.etree.SubElement(self.xmltree, 'MedidasDeMejora')
            improvement_measures.append(improvement_xml_fragment)

    @property
    def version(self):
        """Version del esquema usado en el informe XML"""
        return self.xmltree.get('version')

    @property
    def data(self):
        """Objeto etree correspondiente al informe XML"""
        if self._data is None:
            self._data = self._parsetree()
        return self._data

    @property
    def astext(self):
        """Contenido del informe como texto"""
        SECTIONS = ('DatosDelCertificador',
                    'IdentificacionEdificio',
                    'DatosGeneralesyGeometria',
                    'DatosEnvolventeTermica',
                    'InstalacionesTermicas',
                    'InstalacionesIluminacion',  # Es lista
                    'Demanda',
                    'Consumo',
                    'CondicionesFuncionamientoyOcupacion',  # Es lista
                    'EmisionesCO2',
                    'Calificacion',
                    'MedidasDeMejora')
        data = [self.version]
        for section in SECTIONS:
            data.append('%s\n%s\n%s\n' % (section, '=' * len(section), getattr(self.data, section)))

        data.append('Potenciamediailum\n===========\n%s\n' % str(self.data.InstalacionesIluminacion.totalpotenciamedia))
        return '\n'.join(data)

    def _parsetree(self):
        data = Bunch()

        data.DatosDelCertificador = self.get_datos_certificador()
        data.IdentificacionEdificio = self.get_identificacion_edificio()
        data.DatosGeneralesyGeometria = self.get_datos_generales_y_geometria()
        data.DatosEnvolventeTermica = self.get_datos_envolvente_termica()
        data.InstalacionesTermicas = self.get_instalaciones_termicas()
        data.CondicionesFuncionamientoyOcupacion, data.superficies = self.get_condiciones_funcionamiento_y_ocupacion()
        data.InstalacionesIluminacion = self.get_instalaciones_iluminacion(data.superficies)
        data.EnergiasRenovables = self.get_energias_renovables()
        data.Demanda = self.get_demanda()
        data.Consumo = self.get_consumo()
        data.EmisionesCO2 = self.get_emisiones_co2()
        data.Calificacion = self.get_calificacion()
        data.MedidasDeMejora = self.get_medidas_de_mejora()
        data.PruebasComprobacionesInspecciones = self.get_pruebas_comprobaciones_inspecciones()
        data.DatosPersonalizados = self.get_datos_personalizados()

        return data

    def get_datos_certificador(self):
        datos_certificador = Bunch()

        for attr in ['NombreyApellidos', 'NIF', 'RazonSocial', 'NIFEntidad', 'Domicilio',
                     'Municipio', 'CodigoPostal', 'Provincia', 'ComunidadAutonoma',
                     'Email', 'Telefono', 'Titulacion', 'Fecha']:
            setattr(datos_certificador, attr, astext(self.xmltree, './DatosDelCertificador/%s' % attr))

        return datos_certificador

    def get_identificacion_edificio(self):
        identificacion_edificio = Bunch()

        for attr in ['NombreDelEdificio', 'Direccion',
                     'Municipio', 'CodigoPostal', 'Provincia', 'ComunidadAutonoma',
                     'ZonaClimatica', 'AnoConstruccion', 'ReferenciaCatastral',
                     'TipoDeEdificio', 'NormativaVigente', 'Procedimiento',
                     'AlcanceInformacionXML']:
            setattr(identificacion_edificio, attr, astext(self.xmltree, './IdentificacionEdificio/%s' % attr))
        if 'ninguno' in identificacion_edificio.ReferenciaCatastral:
            identificacion_edificio.ReferenciaCatastral = '-'
        if 'Seleccione de la lista' in identificacion_edificio.NormativaVigente:
            identificacion_edificio.NormativaVigente = '-'

        return identificacion_edificio

    def get_datos_generales_y_geometria(self):
        datos_generales_y_geometria = Bunch()

        datos_generales_y_geometria.NumeroDePlantasSobreRasante = astext(
            self.xmltree,
            './DatosGeneralesyGeometria/NumeroDePlantasSobreRasante')
        img = self.xmltree.find('./DatosGeneralesyGeometria/Imagen')
        datos_generales_y_geometria.Imagen = base64check(img.text) if (img is not None and img.text) else None
        img = self.xmltree.find('./DatosGeneralesyGeometria/Plano')
        datos_generales_y_geometria.Plano = base64check(img.text) if (img is not None and img.text) else None
        for attr in ['NumeroDePlantasBajoRasante',
                     'PorcentajeSuperficieHabitableCalefactada',
                     'PorcentajeSuperficieHabitableRefrigerada']:
            setattr(datos_generales_y_geometria, attr, asint(self.xmltree, './DatosGeneralesyGeometria/%s' % attr))
        for attr in ['SuperficieHabitable',
                     'VolumenEspacioHabitable',
                     'Compacidad',
                     'PorcentajeSuperficieAcristalada',
                     'DensidadFuentesInternas',
                     'VentilacionUsoResidencial',
                     'VentilacionTotal',
                     'DemandaDiariaACS']:
            setattr(datos_generales_y_geometria, attr, asfloat(self.xmltree, './DatosGeneralesyGeometria/%s' % attr))
        datos_generales_y_geometria.PorcentajeSuperficieAcristalada = {
            key: asint(self.xmltree, './DatosGeneralesyGeometria/PorcentajeSuperficieAcristalada/%s' % key)
            for key in 'N NE E SE S SO O NO'.split()
            }

        return datos_generales_y_geometria

    def get_datos_envolvente_termica(self):
        datos_envolvente_termica = Bunch()

        datos_envolvente_termica.CerramientosOpacos = self.get_cerramientos_opacos()
        datos_envolvente_termica.HuecosyLucernarios = self.get_huecos_y_lucernarios()
        datos_envolvente_termica.PuentesTermicos = self.get_puentes_termicos()

        return datos_envolvente_termica

    def get_cerramientos_opacos(self):
        cerramientos_opacos = []

        elementos_opacos = self.xmltree.find('./DatosEnvolventeTermica/CerramientosOpacos')
        elementos_opacos = [] if elementos_opacos is None else elementos_opacos
        for elemento in elementos_opacos:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'Orientacion', 'ModoDeObtencion']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['Superficie', 'Transmitancia']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            obj.Capas = []
            for ecapa in elemento.find('./Capas'):
                capa = Bunch()
                capa.Material = astext(ecapa, './Material')
                for attr in ['Espesor',
                             'ConductividadTermica', 'ResistenciaTermica',
                             'Densidad', 'FactorResistenciaVapor',
                             'CalorEspecifico']:
                    setattr(capa, attr, asfloat(ecapa, './%s' % attr))
                obj.Capas.append(capa)
            cerramientos_opacos.append(obj)

        return cerramientos_opacos

    def get_huecos_y_lucernarios(self):
        huecos_y_lucernarios = []

        elementos_huecos = self.xmltree.find('./DatosEnvolventeTermica/HuecosyLucernarios')
        elementos_huecos = [] if elementos_huecos is None else elementos_huecos
        for elemento in elementos_huecos:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'Orientacion',
                         'ModoDeObtencionTransmitancia',
                         'ModoDeObtencionFactorSolar']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['Superficie', 'Transmitancia', 'FactorSolar']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            huecos_y_lucernarios.append(obj)

        return huecos_y_lucernarios

    def get_puentes_termicos(self):
        puentes_termicos = []

        elementos_pts = self.xmltree.find('./DatosEnvolventeTermica/PuentesTermicos')
        elementos_pts = [] if elementos_pts is None else elementos_pts
        for elemento in elementos_pts:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ModoDeObtencion']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['Longitud', 'Transmitancia']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            puentes_termicos.append(obj)

        return puentes_termicos

    def get_instalaciones_termicas(self):
        bb = Bunch()

        bb.GeneradoresDeCalefaccion, bb.totalpotenciageneradoresdecalefaccion = self.get_generadores_de_calefaccion()
        bb.GeneradoresDeRefrigeracion, bb.totalpotenciageneradoresderefrigeracion = self.get_generadores_de_refrigeracion()
        bb.InstalacionesACS = self.get_instalaciones_acs()
        bb.SistemasSecundariosCalefaccionRefrigeracion = self.get_sistemas_secundarios_calefaccion_refrigeracion()
        bb.TorresyRefrigeracion, bb.totalconsumotorresyrefrigeracion = self.get_torres_y_refrigeracion()
        bb.VentilacionyBombeo, bb.totalconsumoventilacionybombeo = self.get_ventilacion_y_bombeo()

        return bb

    def get_generadores_de_calefaccion(self):
        generadores_de_calefaccion = []

        elementos_generadores = self.xmltree.find('./InstalacionesTermicas/GeneradoresDeCalefaccion')
        elementos_generadores = [] if elementos_generadores is None else elementos_generadores
        for elemento in elementos_generadores:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'VectorEnergetico',
                         'ModoDeObtencion']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['PotenciaNominal', 'RendimientoNominal', 'RendimientoEstacional']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            generadores_de_calefaccion.append(obj)

        total_potencia_generadores_de_calefaccion = sum(
            e.PotenciaNominal for e in generadores_de_calefaccion if e.PotenciaNominal <= ALERT)

        return generadores_de_calefaccion, total_potencia_generadores_de_calefaccion

    def get_generadores_de_refrigeracion(self):
        generadores_de_refrigeracion = []

        elementos_generadores = self.xmltree.find('./InstalacionesTermicas/GeneradoresDeRefrigeracion')
        elementos_generadores = [] if elementos_generadores is None else elementos_generadores
        for elemento in elementos_generadores:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'VectorEnergetico',
                         'ModoDeObtencion']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['PotenciaNominal', 'RendimientoNominal', 'RendimientoEstacional']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            generadores_de_refrigeracion.append(obj)

        total_potencia_generadores_de_refrigeracion = sum(
            e.PotenciaNominal for e in generadores_de_refrigeracion if e.PotenciaNominal <= ALERT)

        return generadores_de_refrigeracion, total_potencia_generadores_de_refrigeracion

    def get_instalaciones_acs(self):
        instalaciones_acs = []

        elementos_generadores = self.xmltree.find('./InstalacionesTermicas/InstalacionesACS')
        elementos_generadores = [] if elementos_generadores is None else elementos_generadores
        for elemento in elementos_generadores:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'VectorEnergetico',
                         'ModoDeObtencion']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['PotenciaNominal', 'RendimientoNominal', 'RendimientoEstacional']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            instalaciones_acs.append(obj)

        return instalaciones_acs

    def get_sistemas_secundarios_calefaccion_refrigeracion(self):
        sistemas_secundarios_calefaccion_refrigeracion = []

        elementos_secundarios = self.xmltree.find('./InstalacionesTermicas/SistemasSecundariosCalefaccionRefrigeracion')
        elementos_secundarios = [] if elementos_secundarios is None else elementos_secundarios
        for elemento in elementos_secundarios:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ZonaAsociada',
                         'EnfriamientoEvaporativo', 'RecuperacionEnergia',
                         'EnfriamentoGratuito', 'TipoControl']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['PotenciaCalor', 'PotenciaFrio', 'RendimentoCalor', 'RendimientoFrio',
                         'RendimientoEstacionalCalor', 'RendimientoEstacionalFrio']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            sistemas_secundarios_calefaccion_refrigeracion.append(obj)

        return sistemas_secundarios_calefaccion_refrigeracion

    def get_torres_y_refrigeracion(self):
        torres_y_refrigeracion = []

        elementos_torres = self.xmltree.find('./InstalacionesTermicas/TorresyRefrigeracion')
        elementos_torres = [] if elementos_torres is None else elementos_torres
        for elemento in elementos_torres:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ServicioAsociado']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['ConsumoDeEnergia']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            torres_y_refrigeracion.append(obj)

        total_consumo_torres_y_refrigeracion = sum(e.ConsumoDeEnergia for e in torres_y_refrigeracion)

        return torres_y_refrigeracion, total_consumo_torres_y_refrigeracion

    def get_ventilacion_y_bombeo(self):
        ventilacion_y_bombeo = []

        elementos_ventilacion = self.xmltree.find('./InstalacionesTermicas/VentilacionyBombeo')
        elementos_ventilacion = [] if elementos_ventilacion is None else elementos_ventilacion
        for elemento in elementos_ventilacion:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ServicioAsociado']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['ConsumoDeEnergia']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            ventilacion_y_bombeo.append(obj)

        total_consumo_ventilacion_y_bombeo = sum(e.ConsumoDeEnergia for e in ventilacion_y_bombeo)

        return ventilacion_y_bombeo, total_consumo_ventilacion_y_bombeo

    def get_condiciones_funcionamiento_y_ocupacion(self):
        condiciones_funcionamiento_y_ocupacion = []

        elementoscond = self.xmltree.find('./CondicionesFuncionamientoyOcupacion')
        elementoscond = [] if elementoscond is None else elementoscond
        for elemento in elementoscond:
            obj = Bunch()
            for attr in ['Nombre', 'NivelDeAcondicionamiento', 'PerfilDeUso']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['Superficie']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            condiciones_funcionamiento_y_ocupacion.append(obj)

        superficies = dict((e.Nombre, e.Superficie) for e in condiciones_funcionamiento_y_ocupacion)

        return condiciones_funcionamiento_y_ocupacion, superficies

    def get_instalaciones_iluminacion(self, superficies):
        instalaciones_iluminacion = Bunch()

        instalaciones_iluminacion.PotenciaTotalInstalada = asfloat(self.xmltree,
                                                                   './InstalacionesIluminacion/PotenciaTotalInstalada')
        instalaciones_iluminacion.Espacios = []
        elementosilumina = self.xmltree.find('./InstalacionesIluminacion')
        elementosilumina = [] if elementosilumina is None else elementosilumina
        for elemento in elementosilumina:
            if elemento.tag == 'PotenciaTotalInstalada':
                continue
            obj = Bunch()
            for attr in ['Nombre', 'ModoDeObtencion']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['PotenciaInstalada', 'VEEI', 'IluminanciaMedia']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            instalaciones_iluminacion.Espacios.append(obj)
        _eiluminados = dict((e.Nombre, e) for e in instalaciones_iluminacion.Espacios)
        _supiluminada = sum(superficies[e] for e in _eiluminados)

        instalaciones_iluminacion.totalpotenciamedia = sum(
            1.0 * superficies[e] * _eiluminados[e].PotenciaInstalada / _supiluminada for e in _eiluminados)

        return instalaciones_iluminacion

    def get_energias_renovables(self):
        energias_renovables = Bunch()

        energias_renovables.Termica, energias_renovables.totaltermica = self.get_energia_renovable_termica()
        energias_renovables.Electrica, energias_renovables.totalelectrica = self.get_energia_renovable_electrica()

        return energias_renovables

    def get_energia_renovable_termica(self):
        energia_renovable_termica = []

        elementosertermica = self.xmltree.find('./EnergiasRenovables/Termica')
        elementosertermica = [] if elementosertermica is None else elementosertermica
        for elemento in elementosertermica:
            obj = Bunch()
            for attr in ['Nombre']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['ConsumoFinalCalefaccion', 'ConsumoFinalRefrigeracion',
                         'ConsumoFinalACS', 'DemandaACS']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            energia_renovable_termica.append(obj)

        energia_renovable_total_termica = self.get_energia_renovable_total_termica(energia_renovable_termica)

        return energia_renovable_termica, energia_renovable_total_termica

    def get_energia_renovable_total_termica(self, termica):

        total_termica = Bunch()

        _noneaszero = lambda x: x if x is not None else 0

        total_termica.ConsumoFinalCalefaccion = sum(_noneaszero(getattr(e, 'ConsumoFinalCalefaccion', 0)) for e in termica)
        total_termica.ConsumoFinalRefrigeracion = sum(_noneaszero(getattr(e, 'ConsumoFinalRefrigeracion', 0)) for e in termica)
        total_termica.ConsumoFinalACS = sum(_noneaszero(getattr(e, 'ConsumoFinalACS', 0)) for e in termica)
        total_termica.DemandaACS = sum(_noneaszero(getattr(e, 'DemandaACS', 0)) for e in termica)

        return total_termica

    def get_energia_renovable_electrica(self):
        energia_renovable_electrica = []

        elementos_er_electrica = self.xmltree.find('./EnergiasRenovables/Electrica')
        elementos_er_electrica = [] if elementos_er_electrica is None else elementos_er_electrica
        for elemento in elementos_er_electrica:
            obj = Bunch()
            for attr in ['Nombre']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['EnergiaGeneradaAutoconsumida']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            energia_renovable_electrica.append(obj)

        energia_renovable_total_electrica = sum(e.EnergiaGeneradaAutoconsumida for e in energia_renovable_electrica)

        return energia_renovable_electrica, energia_renovable_total_electrica

    def get_demanda(self):
        demanda = Bunch()

        demanda.EdificioObjeto = Bunch()
        for attr in ['Global', 'Calefaccion', 'Refrigeracion', 'ACS',
                     'Conjunta', 'Calefaccion08', 'Refrigeracion08',
                     'Conjunta08', 'Ahorro08']:
            setattr(demanda.EdificioObjeto, attr,
                    asfloat(self.xmltree, './Demanda/EdificioObjeto/%s' % attr))

        demanda.EdificioDeReferencia = Bunch()
        for attr in ['Global', 'Calefaccion', 'Refrigeracion', 'ACS',
                     'Conjunta', 'Calefaccion08', 'Refrigeracion08',
                     'Conjunta08']:
            setattr(demanda.EdificioDeReferencia, attr,
                    asfloat(self.xmltree, './Demanda/EdificioDeReferencia/%s' % attr))

        demanda.Exigencias = Bunch()
        for attr in ['LimiteCalefaccionVivienda', 'LimiteRefrigeracionVivienda',
                     'LimiteAhorroOtrosUsos']:
            setattr(demanda.Exigencias, attr,
                    asfloat(self.xmltree, './Demanda/Exigencias/%s' % attr))

        return demanda

    def get_consumo(self):
        consumo = Bunch()
        consumo.FactoresdePaso = self.get_factores_de_paso()
        (consumo.EnergiaFinalVectores,
         consumo.EnergiaFinalPorVector,
         consumo.EnergiaFinalPorServicio) = self.get_energia_final_vectores()
        consumo.EnergiaFinal = self.get_energia_final_por_servicios(consumo.EnergiaFinalVectores)
        consumo.EnergiaPrimariaNoRenovable = self.get_energia_primaria_no_renovable()

        consumo.Exigencias = Bunch()
        consumo.Exigencias.LimiteViviendaGlobalEPNR = asfloat(self.xmltree,
                                                              './Consumo/Exigencias/LimiteViviendaGlobalEPNR')

        return consumo

    def get_factores_de_paso(self):
        factores_de_paso = Bunch()

        final_a_primaria_no_renovable = Bunch()
        for attr in VECTORES:
            value = './Consumo/FactoresdePaso/FinalAPrimariaNoRenovable/%s' % attr
            setattr(final_a_primaria_no_renovable, attr, asfloat(self.xmltree, value))
        factores_de_paso.FinalAPrimariaNoRenovable = final_a_primaria_no_renovable

        final_a_emisiones = Bunch()
        for attr in VECTORES:
            setattr(final_a_emisiones, attr, asfloat(self.xmltree,
                                                     './Consumo/FactoresdePaso/FinalAEmisiones/%s' % attr))
        factores_de_paso.FinalAEmisiones = final_a_emisiones

        return factores_de_paso

    def get_energia_final_vectores(self):
        energia_final_vectores = Bunch()
        energia_final_por_vector = {}
        energia_final_por_servicio = defaultdict(float)

        for vec in VECTORES:
            vector = Bunch()
            if self.xmltree.find('./Consumo/EnergiaFinalVectores/%s' % vec) is not None:
                total_por_vector = 0
                for servicio in SERVICIOS:
                    energia = asfloat(self.xmltree, './Consumo/EnergiaFinalVectores/%s/%s' % (vec, servicio))
                    setattr(vector, servicio, energia)

                    if servicio != 'Global' and energia is not None:
                        total_por_vector += energia
                        energia_final_por_servicio[servicio] += energia

                setattr(energia_final_vectores, vec, vector)

                # Si el vector tiene un campo Global, usamos ese campo. Si no, sumamos todos los demás
                if vector.get('Global', None) is not None:
                    energia_final_por_vector[vec] = vector['Global']
                else:
                    energia_final_por_vector[vec] = total_por_vector

        return energia_final_vectores, energia_final_por_vector, dict(energia_final_por_servicio)

    def get_energia_final_por_servicios(self, energia_final_vectores):
        energia_final_por_servicios = Bunch()

        for vector in VECTORES:
            vecdata = getattr(energia_final_vectores, vector, None)
            if vecdata is None:
                continue
            for servicio in SERVICIOS:
                veccval = getattr(vecdata, servicio, 0.0)
                if veccval is None:
                    continue
                cval = getattr(energia_final_por_servicios, servicio, 0.0)
                cval = 0.0 if cval is None else cval
                setattr(energia_final_por_servicios, servicio, cval + veccval)

        return energia_final_por_servicios

    def get_energia_primaria_no_renovable(self):
        energia_primaria_no_renovable = Bunch()

        for servicio in SERVICIOS:
            value = './Consumo/EnergiaPrimariaNoRenovable/%s' % servicio
            setattr(energia_primaria_no_renovable, servicio, asfloat(self.xmltree, value))

        return energia_primaria_no_renovable

    def get_emisiones_co2(self):
        emisiones_co2 = Bunch()

        for servicio in SERVICIOS + 'ConsumoElectrico ConsumoOtros TotalConsumoElectrico TotalConsumoOtros'.split():
            setattr(emisiones_co2, servicio, asfloat(self.xmltree, './EmisionesCO2/%s' % servicio))

        return emisiones_co2

    def get_calificacion(self):
        calificacion = Bunch()

        calificacion.Demanda = self.get_calificacion_demanda()
        calificacion.EnergiaPrimariaNoRenovable = self.get_calificacion_energia_primaria_no_renovable()
        calificacion.EmisionesCO2 = self.get_calificacion_emisiones_co2()

        return calificacion

    def get_calificacion_demanda(self):
        calificacion_demanda = Bunch()

        escala = self.xmltree.find('./Calificacion/Demanda/EscalaCalefaccion')
        if escala is not None:
            dd = Bunch()
            for nivel in NIVELESESCALA:
                setattr(dd, nivel, asfloat(escala, './%s' % nivel))
            calificacion_demanda.EscalaCalefaccion = dd

        escala = self.xmltree.find('./Calificacion/Demanda/EscalaRefrigeracion')
        if escala is not None:
            dd = Bunch()
            for nivel in NIVELESESCALA:
                setattr(dd, nivel, asfloat(escala, './%s' % nivel))
            calificacion_demanda.EscalaRefrigeracion = dd

        calificacion_demanda.Calefaccion = astext(self.xmltree, './Calificacion/Demanda/Calefaccion')
        calificacion_demanda.Refrigeracion = astext(self.xmltree, './Calificacion/Demanda/Calefaccion')

        return calificacion_demanda

    def get_calificacion_energia_primaria_no_renovable(self):
        calificacion_energia_primaria_no_renovable = Bunch()

        escala = self.xmltree.find('./Calificacion/EnergiaPrimariaNoRenovable/EscalaGlobal')
        if escala is not None:
            escala_global = Bunch()
            for nivel in NIVELESESCALA:
                setattr(escala_global, nivel, asfloat(escala, './%s' % nivel))
            calificacion_energia_primaria_no_renovable.EscalaGlobal = escala_global

        calificacion_energia_primaria_no_renovable.Global = astext(self.xmltree,
                                                                   './Calificacion/EnergiaPrimariaNoRenovable/Global')
        calificacion_energia_primaria_no_renovable.Calefaccion = astext(self.xmltree,
                                                                        './Calificacion/EnergiaPrimariaNoRenovable/Calefaccion')
        calificacion_energia_primaria_no_renovable.Refrigeracion = astext(self.xmltree,
                                                                          './Calificacion/EnergiaPrimariaNoRenovable/Refrigeracion')
        calificacion_energia_primaria_no_renovable.ACS = astext(self.xmltree,
                                                                './Calificacion/EnergiaPrimariaNoRenovable/ACS')
        calificacion_energia_primaria_no_renovable.Iluminacion = astext(self.xmltree,
                                                                        './Calificacion/EnergiaPrimariaNoRenovable/Iluminacion')

        return calificacion_energia_primaria_no_renovable

    def get_calificacion_emisiones_co2(self):
        calificacion_emisiones_co2 = Bunch()

        escala = self.xmltree.find('./Calificacion/EmisionesCO2/EscalaGlobal')
        if escala is not None:
            escala_global = Bunch()
            for nivel in NIVELESESCALA:
                setattr(escala_global, nivel, asfloat(escala, './%s' % nivel))
            calificacion_emisiones_co2.EscalaGlobal = escala_global

        calificacion_emisiones_co2.Global = astext(self.xmltree, './Calificacion/EmisionesCO2/Global')
        calificacion_emisiones_co2.Calefaccion = astext(self.xmltree, './Calificacion/EmisionesCO2/Calefaccion')
        calificacion_emisiones_co2.Refrigeracion = astext(self.xmltree, './Calificacion/EmisionesCO2/Refrigeracion')
        calificacion_emisiones_co2.ACS = astext(self.xmltree, './Calificacion/EmisionesCO2/ACS')
        calificacion_emisiones_co2.Iluminacion = astext(self.xmltree, './Calificacion/EmisionesCO2/Iluminacion')

        return calificacion_emisiones_co2

    def get_medidas_de_mejora(self):
        medidas_de_mejora = []

        medidas = self.xmltree.find('./MedidasDeMejora')
        medidas = [] if medidas is None else medidas
        for medida in medidas:
            medida_de_mejora = Bunch()

            for attr in 'Nombre Descripcion CosteEstimado OtrosDatos'.split():
                txt = astext(medida, './%s' % attr)
                if txt and txt.startswith('data:/text/html,'):
                    txt = txt.lstrip('data:/text/html,')
                    txt = clean_html(txt)
                setattr(medida_de_mejora, attr, txt)

            medida_de_mejora.Demanda = Bunch()
            for attr in 'Global GlobalDiferenciaSituacionInicial Calefaccion Refrigeracion'.split():
                setattr(medida_de_mejora.Demanda, attr, asfloat(medida, './Demanda/%s' % attr))

            medida_de_mejora.CalificacionDemanda = Bunch()
            for attr in 'Calefaccion Refrigeracion'.split():
                setattr(medida_de_mejora.CalificacionDemanda, attr, astext(medida, './CalificacionDemanda/%s' % attr))

            medida_de_mejora.EnergiaFinal = Bunch()
            for attr in SERVICIOS:
                setattr(medida_de_mejora.EnergiaFinal, attr, asfloat(medida, './EnergiaFinal/%s' % attr))

            medida_de_mejora.EnergiaPrimariaNoRenovable = Bunch()
            for attr in SERVICIOS:
                setattr(medida_de_mejora.EnergiaPrimariaNoRenovable, attr, asfloat(medida, './EnergiaPrimariaNoRenovable/%s' % attr))
            medida_de_mejora.EnergiaPrimariaNoRenovable.GlobalDiferenciaSituacionInicial = asfloat(medida,
                                                          './EnergiaPrimariaNoRenovable/GlobalDiferenciaSituacionInicial')

            medida_de_mejora.CalificacionEnergiaPrimariaNoRenovable = Bunch()
            for attr in SERVICIOS:
                setattr(medida_de_mejora.CalificacionEnergiaPrimariaNoRenovable, attr, astext(medida, './CalificacionEnergiaPrimariaNoRenovable/%s' % attr))

            medida_de_mejora.EmisionesCO2 = Bunch()
            for attr in SERVICIOS:
                setattr(medida_de_mejora.EmisionesCO2, attr, asfloat(medida, './EmisionesCO2/%s' % attr))
            medida_de_mejora.EmisionesCO2.GlobalDiferenciaSituacionInicial = asfloat(medida, './EmisionesCO2/GlobalDiferenciaSituacionInicial')

            medida_de_mejora.CalificacionEmisionesCO2 = Bunch()
            for attr in SERVICIOS:
                setattr(medida_de_mejora.CalificacionEmisionesCO2, attr, astext(medida, './CalificacionEmisionesCO2/%s' % attr))

            medidas_de_mejora.append(medida_de_mejora)

        return medidas_de_mejora

    def get_pruebas_comprobaciones_inspecciones(self):
        pruebas_comprobaciones_inspecciones = []

        pruebas = self.xmltree.find('./PruebasComprobacionesInspecciones')
        pruebas = [] if pruebas is None else pruebas
        for prueba in pruebas:
            bb = Bunch()
            bb.FechaVisita = astext(prueba, './FechaVisita')
            txt = astext(prueba, './Datos')
            if txt and txt.startswith('data:/text/html,'):
                txt = txt.lstrip('data:/text/html,')
                txt = clean_html(txt)
            bb.Datos = txt
            pruebas_comprobaciones_inspecciones.append(bb)

        return pruebas_comprobaciones_inspecciones

    def get_datos_personalizados(self):
        txt = astext(self.xmltree, './DatosPersonalizados')
        if txt and txt.startswith('data:/text/html,'):
            txt = txt.lstrip('data:/text/html,')
            txt = clean_html(txt)
        return txt

    def validate(self):
        """Valida el informe XML según el esquema XSD"""
        # http://lxml.de/validation.html
        if self.version == '1':
            self.xmlschema = lxml.etree.XMLSchema(lxml.etree.parse(open(XSDPATH1, encoding='UTF-8')))
        else:
            self.xmlschema = lxml.etree.XMLSchema(lxml.etree.parse(open(XSDPATH2, encoding='UTF-8')))
        self.xmlschema.validate(self.xmltree)

        errors = [(error.line, error.message) for error in self.xmlschema.error_log]
        self.errors['validation_errors'] += errors

    def analize(self):
        """Analiza contenidos de un Informe XML en busca de posibles errores"""
        zci = self.data.IdentificacionEdificio.ZonaClimatica[:-1]
        zcv = self.data.IdentificacionEdificio.ZonaClimatica[-1]
        esvivienda = 'Vivienda' in self.data.IdentificacionEdificio.TipoDeEdificio

        info = []
        if self.data.IdentificacionEdificio.AnoConstruccion == '-':
            info.append(('AVISO', 'No se ha definido el año de construcción'))
        if self.data.IdentificacionEdificio.ReferenciaCatastral == '-':
            info.append(('AVISO', 'No se ha definido la referencia catastral'))

        if sum(self.data.superficies.values()) > self.data.DatosGeneralesyGeometria.SuperficieHabitable:
            info.append(('ERROR', 'Superficies habitable menor que suma de la superficie de los espacios'))
        if zcv not in '1234':
            info.append(('ERROR', 'Zona climática de verano incorrecta'))
        if zci not in ['A', 'B', 'C', 'D', 'E', 'alfa', 'alpha']:
            info.append(('ERROR', 'Zona climática de invierno incorrecta'))

        plano_ = self.data.DatosGeneralesyGeometria.Plano
        if not plano_:
            info.append(('AVISO', 'Sin datos de plano'))
        elif not base64check(plano_):
            info.append(('AVISO', 'Datos de plano incorrectos'))

        imagen_ = self.data.DatosGeneralesyGeometria.Imagen
        if not imagen_:
            info.append(('AVISO', 'Sin datos de imagen'))
        elif not base64check(imagen_):
            info.append(('AVISO', 'Datos de imagen incorrectos'))

        if ((0 > self.data.DatosGeneralesyGeometria.PorcentajeSuperficieHabitableCalefactada > 100) or
                (0 > self.data.DatosGeneralesyGeometria.PorcentajeSuperficieHabitableRefrigerada > 100)):
            info.append(('ERROR', 'Porcentajes de superficies acondicionadas fuera de rango'))

        if esvivienda:
            # Sin chequear
            if (zcv == '1' and
                    (self.data.Demanda.EdificioDeReferencia.Refrigeracion or
                     self.data.Calificacion.EmisionesCO2.Refrigeracion or
                     self.data.Calificacion.Demanda.Refrigeracion or
                     self.data.Calificacion.EnergiaPrimariaNoRenovable.Refrigeracion)):
                info.append(('ERROR',
                             'Zona sin demanda de refrigeración de referencia y para el que se ha definido calificación para ese servicio'))
            # Sin chequear
            if (zci in ('alpha', 'alfa', 'a') and
                    (self.data.Demanda.EdificioDeReferencia.Calefaccion or
                     self.data.Calificacion.EmisionesCO2.Calefaccion or
                     self.data.Calificacion.Demanda.Calefaccion or
                     self.data.Calificacion.EnergiaPrimariaNoRenovable.Calefaccion)):
                info.append(('ERROR',
                             'Zona sin demanda de calefacción de referencia y para la que se ha definido calificación para ese servicio'))

        if not esvivienda:
            if not self.data.InstalacionesTermicas.SistemasSecundariosCalefaccionRefrigeracion:
                info.append(('AVISO', 'No se han definido sistemas secundarios de calefacción y/o refrigeración'))
            if not self.data.InstalacionesTermicas.VentilacionyBombeo:
                info.append(('AVISO', 'No se han definido sistemas de ventilación y bombeo'))

        def _visit(res, ckey, obj):
            """Incluye en res la lista de valores numéricos con sus etiquetas"""

            if isinstance(obj, numbers.Number):
                res.append((obj, ckey))
            elif isinstance(obj, (list, tuple)):
                for item in obj:
                    _visit(res, ckey, item)
            elif isinstance(obj, (Bunch,)):
                for key in obj.keys():
                    if key.startswith('_'):
                        continue
                    _visit(res, key, obj[key])

        values = []
        _visit(values, 'root', self.data)
        suspects = [key for (value, key) in values if value >= ALERT]
        if suspects:
            info.append(('AVISO', 'Valores numéricos erróneos en : %s' % ', '.join(set(suspects))))

        self.errors['info'] = info
