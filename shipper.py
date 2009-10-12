"""
Copyright (C) 2009, Tay Ray Chuan

Please see LICENCE for licensing details.
"""

"""
Each shipping option uses the data in an Order object to calculate the shipping cost and return the value
"""
try:
    from decimal import Decimal
except:
    from django.utils._decimal import Decimal

from django.utils.translation import ugettext, ugettext_lazy
from satchmo.configuration import config_value
_ = ugettext_lazy
from satchmo.shipping.modules.base import BaseShipper

WEIGHT_COST_MAP = {
    'NONSTANDARD_MAIL': (
        (40,	Decimal('0.50')),
        (100,	Decimal('0.80')),
        (250,	Decimal('1.00')),
        (500,	Decimal('1.50')),
        (1000,	Decimal('2.55')),
        (2000,	Decimal('3.35'))
    )
}

class Shipper(BaseShipper):
    id = "SingPost"

    def __str__(self):
        """
        This is mainly helpful for debugging purposes
        """
        return "Flat Rate: %s" % config_value('SHIPPING', 'FLAT_RATE')

    def description(self):
        """
        A basic description that will be displayed to the user when selecting their shipping options
        """
        return _("SingPost Shipping")

    def _weight(self):
        total_weight = 0

        for cartitem in self.cart.cartitem_set.all():
            if cartitem.product.is_shippable:
                total_weight += cartitem.product.weight * cartitem.quantity

        return total_weight

    def cost(self):
        """
        Complex calculations can be done here as long as the return value is a dollar figure
        """
        assert(self._calculated)

        total_weight = self._weight()

        prev = None
        result_cost = None

        for pair in WEIGHT_COST_MAP[config_value('SHIPPING', 'SHIPPING_CHOICE')[0]]:
            weight_class = pair[0]
            weight_class_cost = pair[1]
            if total_weight <= Decimal(weight_class):
                if prev:
                    if total_weight > Decimal(prev):
                        result_cost = weight_class_cost
                        break
            else:
                prev = weight_class

        return result_cost

    def method(self):
        """
        Describes the actual delivery service (Mail, FedEx, DHL, UPS, etc)
        """
        return ugettext(config_value('SHIPPING', 'FLAT_SERVICE'))

    def expectedDelivery(self):
        """
        Can be a plain string or complex calcuation returning an actual date
        """
        return ugettext(config_value('SHIPPING', 'FLAT_DAYS'))

    def valid(self, order=None):
        """
        Can do complex validation about whether or not this option is valid.
        For example, may check to see if the recipient is in an allowed country
        or location.
        """
        return True

