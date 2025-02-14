from django.apps import AppConfig
from django.utils.translation import gettext_lazy

import os

from dmoj.settings import BASE_DIR


class AuthTdtUAppConfig(AppConfig):
    name = 'auth_tdtu'
    verbose_name = gettext_lazy('TDTU Authentication')
    path = BASE_DIR