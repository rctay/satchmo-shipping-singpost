"""
Copyright (C) 2009-2010, Tay Ray Chuan

Please see LICENCE for licensing details.
"""

from django.utils.translation import ugettext_lazy as _
from livesettings import *

SHIP_MODULES = config_get('SHIPPING', 'MODULES')
SHIP_MODULES.add_choice(('singpost', 'SingPost'))

SHIPPING_GROUP = ConfigurationGroup('singpost',
  _('SingPost Shipping Settings'),
  requires = SHIP_MODULES,
  requiresvalue='singpost',
  ordering = 101
)

config_register_list(
    MultipleStringValue(SHIPPING_GROUP,
        'SINGPOST_SHIPPING_CHOICES',
        description=_("SingPost shipping choices available to customers."),
        choices = (
            (('LOCAL', 'Local mail (inclusive of 7%% GST')),
            (('SURFACE', 'Surface mail (0%% GST')),
            (('AIR', 'Airmail (0%% GST')),
        ),
        default = ('LOCAL', 'SURFACE', 'AIR')),
)
