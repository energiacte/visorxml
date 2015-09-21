from django import forms
from django.utils.translation import ugettext as _


class XMLFileForm(forms.Form):
    base = forms.FileField(label=_('Archivo XML'),
                           help_text=_('Informe de evaluación de la eficiencia energética en formato XML. Archivo base'))
    mej1 = forms.FileField(label=_('Archivo XML con medidas de mejora nº1'),
                           help_text=_('Medidas de mejora desde archivo XML.'),
                           required=False)
    mej2 = forms.FileField(label=_('Archivo XML con medidas de mejora nº2'),
                           help_text=_('Medidas de mejora desde archivo XML.'),
                           required=False)
    mej3 = forms.FileField(label=_('Archivo XML con medidas de mejora nº3'),
                           help_text=_('Medidas de mejora desde archivo XML.'),
                           required=False)
