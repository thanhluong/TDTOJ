from django.apps import AppConfig

import os

from dmoj.settings import BASE_DIR


class AuthTdtUAppConfig(AppConfig):
    name = 'auth_tdtu'
    verbose_name = gettext_lazy('TDTU Authentication')
    path = BASE_DIR