#!/usr/bin/env python
# encoding: utf8

"""Definición de entidades para el análisis de informes de resultados en XML"""

import os
from collections import OrderedDict
import base64

import numbers
import lxml.etree
from lxml.html.clean import clean_html
from pygments import highlight
from pygments.lexers.html import XmlLexer
from pygments.formatters import HtmlFormatter
from .imgb64 import base64check

XSDPATH2 = os.path.join(
    os.path.dirname(__file__),
    'static/validador/DatosEnergeticosDelEdificioSchema20.xsd')
XSDPATH1 = os.path.join(
    os.path.dirname(__file__),
    'static/validador/DatosEnergeticosDelEdificioSchema10.xsd')

VECTORES = ('GasNatural GasoleoC GLP Carbon BiomasaPellet BiomasaOtros '
            'ElectricidadPeninsular ElectricidadBaleares '
            'ElectricidadCanarias ElectricidadCeutayMelilla Biocarburante').split()
SERVICIOS = ('Global Calefaccion Refrigeracion ACS Iluminacion').split()
NIVELESESCALA = 'A B C D E F'.split()
ALERTINT = 9999999999
ALERTFLOAT = ALERTINT + 0.99
ALERT = ALERTINT / 100

class Bunch(OrderedDict):
    "Contenedor genérico"
    def __init__(self, *args, **kwds):
        OrderedDict.__init__(self, *args, **kwds)
    def __str__(self):
        state = [u"%s=%s" % (attribute, value)
                 for (attribute, value) in self.__dict__.items()
                 if not attribute.startswith('_OrderedDict')]
        return u'\n'.join(state)
    __unicode__ = __str__

XMLPARSER = lxml.etree.XMLParser(resolve_entities=False, # no sustituye unicode a entidades
                                 remove_blank_text=True,
                                 ns_clean=True, # limpia namespaces
                                 remove_comments=True)
def astext(tree, path):
    element = tree.find(path)
    if element is None or not element.text:
        return None
    txt = element.text
    if txt and txt.startswith('data:/text/html,'):
        txt = txt.lstrip('data:/text/html,')
        txt = clean_html(txt)
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


class InformeXML(object):
    def __init__(self, xmldata):
        self.xml = xmldata
        self._xmltree = None
        self._data = None
        self.xmlschema = None
        self._parsetree()

    @property
    def xmltree(self):
        """Árbol lxml de entidades XML"""
        if self._xmltree is None:
            self._xmltree = lxml.etree.XML(self.xml,
                                           parser=XMLPARSER)
        return self._xmltree

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
        SECTIONS = ('DatosDelCertificador', 'IdentificacionEdificio',
                    'DatosGeneralesyGeometria', 'DatosEnvolventeTermica',
                    'InstalacionesTermicas', 'InstalacionesIluminacion', #Es lista
                    'Demanda', 'Consumo', 'CondicionesFuncionamientoyOcupacion', # Es lista
                    'EmisionesCO2', 'Calificacion', 'MedidasDeMejora')
        data = [self.version,]
        for section in SECTIONS:
            data.append(u'%s\n' % section +
                        u'=' * len(section) +
                        u'\n' + unicode(getattr(self.data, section)) +
                        u"\n")
        data.append(u'Potenciamediailum\n===========\n' +
                    str(self.data.InstalacionesIluminacion.totalpotenciamedia) +
                    u"\n")
        return '\n'.join(data)

    @property
    def ashtml(self):
        """Contenido del informe como HTML resaltado"""
        return highlight(self.xml,
                         XmlLexer(),
                         HtmlFormatter(noclasses=True))

    def _parsetree(self):
        et = self.xmltree
        data = Bunch()

        ## Datos del certificador
        bb = Bunch()
        data.DatosDelCertificador = bb
        for attr in ['NombreyApellidos', 'NIF', 'RazonSocial', 'NIFEntidad', 'Domicilio',
                     'Municipio', 'CodigoPostal', 'Provincia', 'ComunidadAutonoma',
                     'Email', 'Telefono', 'Titulacion', 'Fecha']:
            setattr(bb, attr, astext(et, './DatosDelCertificador/%s' % attr))
        #print bb

        ## Identificación del edificio
        bb = Bunch()
        data.IdentificacionEdificio = bb
        for attr in ['NombreDelEdificio', 'Direccion',
                     'Municipio', 'CodigoPostal', 'Provincia', 'ComunidadAutonoma',
                     'ZonaClimatica', 'AnoConstruccion', 'ReferenciaCatastral',
                     'TipoDeEdificio', 'NormativaVigente', 'Procedimiento',
                     'AlcanceInformacionXML']:
            setattr(bb, attr, astext(et, './IdentificacionEdificio/%s' % attr))
        #print bb

        ## Datos generales y geometría
        bb = Bunch()
        data.DatosGeneralesyGeometria = bb
        bb.NumeroDePlantasSobreRasante = astext(et, './DatosGeneralesyGeometria/NumeroDePlantasSobreRasante')
        img = self.xmltree.find('./DatosGeneralesyGeometria/Imagen')
        bb.Imagen = base64check(img.text) if (img is not None and img.text) else None
        img = self.xmltree.find('./DatosGeneralesyGeometria/Plano')
        bb.Plano = base64check(img.text) if (img is not None and img.text) else None
        for attr in ['NumeroDePlantasBajoRasante',
                     'PorcentajeSuperficieHabitableCalefactada',
                     'PorcentajeSuperficieHabitableRefrigerada']:
            setattr(bb, attr, asint(et, './DatosGeneralesyGeometria/%s' % attr))
        for attr in ['SuperficieHabitable',
                     'VolumenEspacioHabitable',
                     'Compacidad',
                     'PorcentajeSuperficieAcristalada',
                     'DensidadFuentesInternas',
                     'VentilacionUsoResidencial',
                     'VentilacionTotal',
                     'DemandaDiariaACS']:
            setattr(bb, attr, asfloat(et, './DatosGeneralesyGeometria/%s' % attr))
        bb.PorcentajeSuperficieAcristalada = Bunch(
            **{key:asint(et, './DatosGeneralesyGeometria/PorcentajeSuperficieAcristalada/%s' % key)
               for key in 'N NE E SE S SO O NO'.split()})
        #print bb

        ## Datos Envolvente Térmica
        bb = Bunch()
        data.DatosEnvolventeTermica = bb
        bb.CerramientosOpacos = []
        elementosopacos = self.xmltree.find('./DatosEnvolventeTermica/CerramientosOpacos')
        elementosopacos = [] if elementosopacos is None else elementosopacos
        for elemento in elementosopacos:
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
            bb.CerramientosOpacos.append(obj)

        bb.HuecosyLucernarios = []
        elementoshuecos = self.xmltree.find('./DatosEnvolventeTermica/HuecosyLucernarios')
        elementoshuecos = [] if elementoshuecos is None else elementoshuecos
        for elemento in elementoshuecos:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'Orientacion',
                         'ModoDeObtencionTransmitancia',
                         'ModoDeObtencionFactorSolar']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['Superficie', 'Transmitancia', 'FactorSolar']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.HuecosyLucernarios.append(obj)

        bb.PuentesTermicos = []
        elementospts = self.xmltree.find('./DatosEnvolventeTermica/PuentesTermicos')
        elementospts = [] if elementospts is None else elementospts
        for elemento in elementospts:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ModoDeObtencion']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['Longitud', 'Transmitancia']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.PuentesTermicos.append(obj)
        #print bb

        ## Instalaciones Térmicas
        bb = Bunch()
        data.InstalacionesTermicas = bb
        bb.GeneradoresDeCalefaccion = []
        elementosgeneradores = self.xmltree.find('./InstalacionesTermicas/GeneradoresDeCalefaccion')
        elementosgeneradores = [] if elementosgeneradores is None else elementosgeneradores
        for elemento in elementosgeneradores:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'VectorEnergetico',
                         'ModoDeObtencion']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['PotenciaNominal', 'RendimientoNominal', 'RendimientoEstacional']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.GeneradoresDeCalefaccion.append(obj)
        bb.totalpotenciageneradoresdecalefaccion = sum(e.PotenciaNominal for e in bb.GeneradoresDeCalefaccion if e.PotenciaNominal <= ALERT)
            
        bb.GeneradoresDeRefrigeracion = []
        elementosgeneradores = self.xmltree.find('./InstalacionesTermicas/GeneradoresDeRefrigeracion')
        elementosgeneradores = [] if elementosgeneradores is None else elementosgeneradores
        for elemento in elementosgeneradores:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'VectorEnergetico',
                         'ModoDeObtencion']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['PotenciaNominal', 'RendimientoNominal', 'RendimientoEstacional']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.GeneradoresDeRefrigeracion.append(obj)
        bb.totalpotenciageneradoresderefrigeracion = sum(e.PotenciaNominal for e in bb.GeneradoresDeRefrigeracion if e.PotenciaNominal <= ALERT)
            
        bb.InstalacionesACS = []
        elementosgeneradores = self.xmltree.find('./InstalacionesTermicas/InstalacionesACS')
        elementosgeneradores = [] if elementosgeneradores is None else elementosgeneradores
        for elemento in elementosgeneradores:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'VectorEnergetico',
                         'ModoDeObtencion']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['PotenciaNominal', 'RendimientoNominal', 'RendimientoEstacional']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.InstalacionesACS.append(obj)

        bb.SistemasSecundariosCalefaccionRefrigeracion = []
        elementossecundarios = self.xmltree.find('./InstalacionesTermicas/SistemasSecundariosCalefaccionRefrigeracion')
        elementossecundarios = [] if elementossecundarios is None else elementossecundarios
        for elemento in elementossecundarios:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ZonaAsociada',
                         'EnfriamientoEvaporativo', 'RecuperacionEnergia',
                         'EnfriamentoGratuito', 'TipoControl']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['PotenciaCalor', 'PotenciaFrio', 'RendimentoCalor', 'RendimientoFrio',
                         'RendimientoEstacionalCalor', 'RendimientoEstacionalFrio']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.SistemasSecundariosCalefaccionRefrigeracion.append(obj)

        bb.TorresyRefrigeracion = []
        elementostorres = self.xmltree.find('./InstalacionesTermicas/TorresyRefrigeracion')
        elementostorres = [] if elementostorres is None else elementostorres
        for elemento in elementostorres:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ServicioAsociado']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['ConsumoDeEnergia']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.TorresyRefrigeracion.append(obj)
        bb.totalconsumotorresyrefrigeracion = sum(e.ConsumoDeEnergia for e in bb.TorresyRefrigeracion)
            
        bb.VentilacionyBombeo = []
        elementosventila = self.xmltree.find('./InstalacionesTermicas/VentilacionyBombeo')
        elementosventila = [] if elementosventila is None else elementosventila
        for elemento in elementosventila:
            obj = Bunch()
            for attr in ['Nombre', 'Tipo', 'ServicioAsociado']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['ConsumoDeEnergia']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.VentilacionyBombeo.append(obj)
        bb.totalconsumoventilacionybombeo = sum(e.ConsumoDeEnergia for e in bb.VentilacionyBombeo)
        #print bb

        ## Condiciones de funcionamiento y ocupación
        bb = []
        data.CondicionesFuncionamientoyOcupacion = bb
        elementoscond = self.xmltree.find('./CondicionesFuncionamientoyOcupacion')
        elementoscond = [] if elementoscond is None else elementoscond
        for elemento in elementoscond:
            obj = Bunch()
            for attr in ['Nombre', 'NivelDeAcondicionamiento', 'PerfilDeUso']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['Superficie']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.append(obj)
        #print self.CondicionesFuncionamientoyOcupacion

        # Superficies de los espacios
        data.superficies = dict((e.Nombre, e.Superficie) for e in data.CondicionesFuncionamientoyOcupacion)

        ## Instalaciones de iluminación
        bb = Bunch()
        data.InstalacionesIluminacion = bb
        bb.PotenciaTotalInstalada = asfloat(self.xmltree, './InstalacionesIluminacion/PotenciaTotalInstalada')
        bb.Espacios = []
        elementosilumina = self.xmltree.find('./InstalacionesIluminacion')
        elementosilumina = [] if elementosilumina is None else elementosilumina
        for elemento in elementosilumina:
            if elemento.tag == 'PotenciaTotalInstalada': continue
            obj = Bunch()
            for attr in ['Nombre', 'ModoDeObtencion']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['PotenciaInstalada', 'VEEI', 'IluminanciaMedia']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.Espacios.append(obj)
        _eiluminados = dict((e.Nombre, e) for e in bb.Espacios)
        _supiluminada = sum(data.superficies[e] for e in _eiluminados)
        bb.totalpotenciamedia = sum(1.0*data.superficies[e]*_eiluminados[e].PotenciaInstalada / _supiluminada for e in _eiluminados)
        #print bb

        ## Energías renovables
        bb = Bunch()
        data.EnergiasRenovables = bb
        bb.Termica = []
        elementosertermica = self.xmltree.find('./EnergiasRenovables/Termica')
        elementosertermica = [] if elementosertermica is None else elementosertermica
        for elemento in elementosertermica:
            obj = Bunch()
            for attr in ['Nombre']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['ConsumoFinalCalefaccion', 'ConsumoFinalRefrigeracion',
                         'ConsumoFinalACS', 'DemandaACS']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.Termica.append(obj)

        bb.totaltermica = Bunch()
        _noneaszero = lambda x: x if x is not None else 0
        bb.totaltermica.ConsumoFinalCalefaccion = sum(_noneaszero(getattr(e, 'ConsumoFinalCalefaccion', 0)) for e in bb.Termica)
        bb.totaltermica.ConsumoFinalRefrigeracion = sum(_noneaszero(getattr(e, 'ConsumoFinalRefrigeracion', 0)) for e in bb.Termica)
        bb.totaltermica.ConsumoFinalACS = sum(_noneaszero(getattr(e, 'ConsumoFinalACS', 0)) for e in bb.Termica)
        bb.totaltermica.DemandaACS = sum(_noneaszero(getattr(e, 'DemandaACS', 0)) for e in bb.Termica)

        bb.Electrica = []
        elementoserelectrica = self.xmltree.find('./EnergiasRenovables/Electrica')
        elementoserelectrica = [] if elementoserelectrica is None else elementoserelectrica
        for elemento in elementoserelectrica:
            obj = Bunch()
            for attr in ['Nombre']:
                setattr(obj, attr, astext(elemento, './%s' % attr))
            for attr in ['EnergiaGeneradaAutoconsumida']:
                setattr(obj, attr, asfloat(elemento, './%s' % attr))
            bb.Electrica.append(obj)
        bb.totalelectrica = sum(e.EnergiaGeneradaAutoconsumida for e in bb.Electrica)
        #print bb

        ## Demanda
        bb = Bunch()
        data.Demanda = bb
        bb.EdificioObjeto = Bunch()
        for attr in ['Global', 'Calefaccion', 'Refrigeracion', 'ACS',
                     'Conjunta', 'Calefaccion08', 'Refrigeracion08',
                     'Conjunta08', 'Ahorro08']:
            setattr(bb.EdificioObjeto, attr,
                    asfloat(self.xmltree, './Demanda/EdificioObjeto/%s' % attr))

        bb.EdificioDeReferencia = Bunch()
        for attr in ['Global', 'Calefaccion', 'Refrigeracion', 'ACS',
                     'Conjunta', 'Calefaccion08', 'Refrigeracion08',
                     'Conjunta08']:
            setattr(bb.EdificioDeReferencia, attr,
                    asfloat(self.xmltree, './Demanda/EdificioDeReferencia/%s' % attr))

        bb.Exigencias = Bunch()
        for attr in ['LimiteCalefaccionVivienda', 'LimiteRefrigeracionVivienda',
                     'LimiteAhorroOtrosUsos']:
            setattr(bb.Exigencias, attr,
                    asfloat(self.xmltree, './Demanda/Exigencias/%s' % attr))
        #print bb

        ## Consumo
        bb = Bunch()
        data.Consumo = bb
        bb.FactoresdePaso = Bunch()

        cc = Bunch()
        for attr in VECTORES:
            setattr(cc, attr, asfloat(self.xmltree, './Consumo/FactoresdePaso/FinalAPrimariaNoRenovable/%s' % attr))
        bb.FactoresdePaso.FinalAPrimariaNoRenovable = cc

        cc = Bunch()
        for attr in VECTORES:
            setattr(cc, attr, asfloat(self.xmltree, './Consumo/FactoresdePaso/FinalAEmisiones/%s' % attr))
        bb.FactoresdePaso.FinalAEmisiones = cc

        cc = Bunch()
        for vec in VECTORES:
            vv = Bunch()
            if self.xmltree.find('./Consumo/EnergiaFinalVectores/%s' % vec) is not None:
                for servicio in SERVICIOS:
                    setattr(vv, servicio, asfloat(self.xmltree, './Consumo/EnergiaFinalVectores/%s/%s' % (vec, servicio)))
                setattr(cc, vec, vv)
        bb.EnergiaFinalVectores = cc

        # Datos de energía final por servicios
        cc = Bunch()
        bb.EnergiaFinal = cc
        for vector in VECTORES:
            vecdata = getattr(bb.EnergiaFinalVectores, vector, None)
            if vecdata is None: continue
            for servicio in SERVICIOS:
                veccval = getattr(vecdata, servicio, 0.0)
                if veccval is None: continue
                cval = getattr(cc, servicio, 0.0)
                cval = 0.0 if cval is None else cval
                setattr(cc, servicio, cval + veccval)

        cc = Bunch()
        for servicio in SERVICIOS:
            setattr(cc, servicio, asfloat(self.xmltree, './Consumo/EnergiaPrimariaNoRenovable/%s' % servicio))
        bb.EnergiaPrimariaNoRenovable = cc

        bb.Exigencias = Bunch()
        bb.Exigencias.LimiteViviendaGlobalEPNR = asfloat(self.xmltree, './Consumo/Exigencias/LimiteViviendaGlobalEPNR')
        #print bb

        ## Emisiones de CO2
        bb = Bunch()
        data.EmisionesCO2 = bb
        for servicio in SERVICIOS + 'ConsumoElectrico ConsumoOtros TotalConsumoElectrico TotalConsumoOtros'.split():
            setattr(bb, servicio, asfloat(self.xmltree, './EmisionesCO2/%s' % servicio))
        #print bb

        ## Calificacion
        bb = Bunch()
        data.Calificacion = bb

        cc = Bunch()
        bb.Demanda = cc
        escala = self.xmltree.find('./Calificacion/Demanda/EscalaCalefaccion')
        if escala is not None:
            dd = Bunch()
            for nivel in NIVELESESCALA:
                setattr(dd, nivel, asfloat(escala, './%s' % nivel))
            cc.EscalaCalefaccion = dd
        escala = self.xmltree.find('./Calificacion/Demanda/EscalaRefrigeracion')
        if escala is not None:
            dd = Bunch()
            for nivel in NIVELESESCALA:
                setattr(dd, nivel, asfloat(escala, './%s' % nivel))
            cc.EscalaRefrigeracion = dd
        cc.Calefaccion = astext(self.xmltree, './Calificacion/Demanda/Calefaccion')
        cc.Refrigeracion = astext(self.xmltree, './Calificacion/Demanda/Calefaccion')

        cc = Bunch()
        bb.EnergiaPrimariaNoRenovable = cc
        escala = self.xmltree.find('./Calificacion/EnergiaPrimariaNoRenovable/EscalaGlobal')
        if escala is not None:
            dd = Bunch()
            for nivel in NIVELESESCALA:
                setattr(dd, nivel, asfloat(escala, './%s' % nivel))
            cc.EscalaGlobal = dd
        cc.Global = astext(self.xmltree, './Calificacion/EnergiaPrimariaNoRenovable/Global')
        cc.Calefaccion = astext(self.xmltree, './Calificacion/EnergiaPrimariaNoRenovable/Calefaccion')
        cc.Refrigeracion = astext(self.xmltree, './Calificacion/EnergiaPrimariaNoRenovable/Refrigeracion')
        cc.ACS = astext(self.xmltree, './Calificacion/EnergiaPrimariaNoRenovable/ACS')
        cc.Iluminacion = astext(self.xmltree, './Calificacion/EnergiaPrimariaNoRenovable/Iluminacion')

        cc = Bunch()
        bb.EmisionesCO2 = cc
        escala = self.xmltree.find('./Calificacion/EmisionesCO2/EscalaGlobal')
        if escala is not None:
            dd = Bunch()
            for nivel in NIVELESESCALA:
                setattr(dd, nivel, asfloat(escala, './%s' % nivel))
            cc.EscalaGlobal = dd
        cc.Global = astext(self.xmltree, './Calificacion/EmisionesCO2/Global')
        cc.Calefaccion = astext(self.xmltree, './Calificacion/EmisionesCO2/Calefaccion')
        cc.Refrigeracion = astext(self.xmltree, './Calificacion/EmisionesCO2/Refrigeracion')
        cc.ACS = astext(self.xmltree, './Calificacion/EmisionesCO2/ACS')
        cc.Iluminacion = astext(self.xmltree, './Calificacion/EmisionesCO2/Iluminacion')
        #print bb

        ## Medidas de mejora
        data.MedidasDeMejora = []
        medidas = self.xmltree.find('./MedidasDeMejora')
        medidas = [] if medidas is None else medidas
        for medida in medidas:
            bb = Bunch()
            for attr in 'Nombre Descripcion CosteEstimado OtrosDatos'.split():
                txt = astext(medida, './%s' % attr)
                if txt and txt.startswith('data:/text/html,'):
                    txt = txt.lstrip('data:/text/html,')
                    txt = clean_html(txt)
                setattr(bb, attr, txt)
            cc = Bunch()
            bb.Demanda = cc
            for attr in 'Global GlobalDiferenciaSituacionInicial Calefaccion Refrigeracion'.split():
                setattr(cc, attr, asfloat(medida, './Demanda/%s' % attr))
            cc = Bunch()
            bb.CalificacionDemanda = cc
            for attr in 'Calefaccion Refrigeracion'.split():
                setattr(cc, attr, astext(medida, './CalificacionDemanda/%s' % attr))
            cc = Bunch()
            bb.EnergiaFinal = cc
            for attr in SERVICIOS:
                setattr(cc, attr, asfloat(medida, './EnergiaFinal/%s' % attr))
            cc = Bunch()
            bb.CalificacionEnergiaFinal = None #TODO: Obtener calificación a partir de escalas
            bb.EnergiaPrimariaNoRenovable = cc
            for attr in SERVICIOS:
                setattr(cc, attr, asfloat(medida, './EnergiaPrimariaNoRenovable/%s' % attr))
            cc.GlobalDiferenciaSituacionInicial = asfloat(medida, './EnergiaPrimariaNoRenovable/GlobalDiferenciaSituacionInicial')
            cc = Bunch()
            bb.CalificacionEnergiaPrimariaNoRenovable = cc
            for attr in SERVICIOS:
                setattr(cc, attr, astext(medida, './CalificacionEnergiaPrimariaNoRenovable/%s' % attr))
            cc = Bunch()
            bb.EmisionesCO2 = cc
            for attr in SERVICIOS:
                setattr(cc, attr, asfloat(medida, './EmisionesCO2/%s' % attr))
            cc.GlobalDiferenciaSituacionInicial = asfloat(medida, './EmisionesCO2/GlobalDiferenciaSituacionInicial')
            cc = Bunch()
            bb.CalificacionEmisionesCO2 = cc
            for attr in SERVICIOS:
                setattr(cc, attr, astext(medida, './CalificacionEmisionesCO2/%s' % attr))
            data.MedidasDeMejora.append(bb)
        #print bb

        ## Pruebas, comprobaciones e inspecciones
        data.PruebasComprobacionesInspecciones = []
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
            data.PruebasComprobacionesInspecciones.append(bb)
        #print bb

        ## Datos personalizados
        #TODO: parece no funcionar
        txt = astext(self.xmltree, './DatosPersonalizados')
        if txt and txt.startswith('data:/text/html,'):
            txt = txt.lstrip('data:/text/html,')
            txt = clean_html(txt)
        data.DatosPersonalizados = txt
        #print data.DatosPersonalizados

        return data

    def validate(self):
        """Valida el informe XML según el esquema XSD"""
        # http://lxml.de/validation.html
        if self.version == '1':
            self.xmlschema = lxml.etree.XMLSchema(lxml.etree.parse(open(XSDPATH1)))
        else:
            self.xmlschema = lxml.etree.XMLSchema(lxml.etree.parse(open(XSDPATH2)))
        self.xmlschema.validate(self.xmltree)
        errors = [(error.line, error.message.encode("utf-8"))
                  for error in self.xmlschema.error_log]
        return errors

def analize(informe):
    """Analiza contenidos de un Informe XML en busca de posibles errores"""
    dd = informe.data
    zci = dd.IdentificacionEdificio.ZonaClimatica[:-1]
    zcv = dd.IdentificacionEdificio.ZonaClimatica[-1]
    esvivienda = 'Vivienda' in dd.IdentificacionEdificio.TipoDeEdificio

    info = []
    if sum(informe.data.superficies.values()) > dd.DatosGeneralesyGeometria.SuperficieHabitable:
        info.append(('ERROR', u'Superficies habitable menor que suma de la superficie de los espacios'))
    if zcv not in '1234':
        info.append(('ERROR', u'Zona climática de verano incorrecta'))
    if zci not in ['A', 'B', 'C', 'D', 'E', 'alfa', 'alpha']:
        info.append(('ERROR', u'Zona climática de invierno incorrecta'))

    plano_ = dd.DatosGeneralesyGeometria.Plano
    if not plano_:
        info.append(('AVISO', u'Sin datos de plano'))
    elif not base64check(plano_):
        info.append(('AVISO', u'Datos de plano incorrectos'))

    imagen_ = dd.DatosGeneralesyGeometria.Imagen
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
                 or dd.Calificacion.EmisionesCO2.Refrigeracion
                 or dd.Calificacion.Demanda.Refrigeracion
                 or dd.Calificacion.EnergiaPrimariaNoRenovable.Refrigeracion)):
            info.append(('ERROR', u'Zona sin demanda de refrigeración de referencia y para el que se ha definido calificación para ese servicio'))
        # Sin chequear
        if (zci in ('alpha', 'alfa', 'a')
            and (dd.Demanda.EdificioDeReferencia.Calefaccion
                 or dd.Calificacion.EmisionesCO2.Calefaccion
                 or dd.Calificacion.Demanda.Calefaccion
                 or dd.Calificacion.EnergiaPrimariaNoRenovable.Calefaccion)):
            info.append(('ERROR', u'Zona sin demanda de calefacción de referencia y para la que se ha definido calificación para ese servicio'))

    if not esvivienda:
        if not informe.data.InstalacionesTermicas.SistemasSecundariosCalefaccionRefrigeracion:
            info.append(('AVISO', u'No se han definido sistemas secundarios de calefacción y/o refrigeración'))
        if not informe.data.InstalacionesTermicas.VentilacionyBombeo:
            info.append(('AVISO', u'No se han definido sistemas de ventilación y bombeo'))

    def _visit(res, ckey, obj):
        "Incluye en res la lista de valores numéricos con sus etiquetas"
        if isinstance(obj, numbers.Number):
            res.append((obj, ckey))
        elif isinstance(obj, (list, tuple)):
            for item in obj:
                _visit(res, ckey, item)
        elif isinstance(obj, (Bunch,)):
            for key in obj.keys():
                if key.startswith('_'): continue
                _visit(res, key, obj[key])

    values = []
    _visit(values, 'root', informe.data)
    suspects = [key for (value, key) in values if value >= ALERT]
    if suspects:
        info.append(('AVISO', u'Valores numéricos erróneos en : %s' % ', '.join(set(suspects))))

    return info

