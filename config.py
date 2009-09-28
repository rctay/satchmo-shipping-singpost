"""
Copyright (C) 2009, Tay Ray Chuan

Please see LICENCE for licensing details.
"""

from django.utils.translation import ugettext_lazy as _
from satchmo.configuration import *

SHIP_MODULES = config_get('SHIPPING', 'MODULES')
SHIP_MODULES.add_choice(('singpost', 'SingPost'))
SHIPPING_GROUP = config_get_group('SHIPPING')

config_register_list(
    MultipleStringValue(SHIPPING_GROUP,
        'SHIPPING_CHOICE',
        description=_('SingPost local postal rates.'),
        choices = (
                    (('STANDARD_MAIL','Local, Standard Mail')),
                    (('NONSTANDARD_MAIL','Local, Non-Standard Mail'))
        ),
        default = ('NONSTANDARD_MAIL',))
)
