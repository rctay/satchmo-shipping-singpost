"""
Copyright (C) 2009, Tay Ray Chuan

Please see LICENCE for licensing details.
"""

from django.utils.translation import ugettext_lazy as _
from satchmo.configuration import *

SHIP_MODULES = config_get('SHIPPING', 'MODULES')
SHIP_MODULES.add_choice(('singpost', 'SingPost'))
