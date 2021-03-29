"""Procesadores de plantillas"""

from django.urls import translate_url
from django.conf import settings

def redirect_path_context_processor(request):
    """Procesador para generar el redirect_to para la localización en el selector de idiomas"""
    return {'language_select_redirect_to': translate_url(request.path, settings.LANGUAGE_CODE)}
