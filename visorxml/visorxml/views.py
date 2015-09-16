from django.views.generic import TemplateView


class HomeView(TemplateView):
    template_name = "home.html"


class ValidatorView(TemplateView):
    template_name = "validator.html"
