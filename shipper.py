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

    def __init__(self, service_type='NONSTANDARD_MAIL'):
        self.service_type = service_type

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

    def _weight_for_shipment(self, shipment):
        total_weight = Decimal('0')

        for cartitem in shipment:
            if cartitem.product.is_shippable:
                total_weight += Decimal(cartitem.product.weight)

        return total_weight

    def _weight(self):
        total_weight = Decimal('0')

        for cartitem in self.cart.cartitem_set.all():
            if cartitem.product.is_shippable:
                total_weight += Decimal(cartitem.product.weight) * Decimal(cartitem.quantity)

        return total_weight

    def _cart_as_shipment(self):
        shipment = []
        for cartitem in self.cart.cartitem_set.all():
            for i in xrange(cartitem.quantity):
                shipment.append(cartitem)

        return shipment

    """
    Returns a list of shipments.
    """
    def _partitioned_shipments(self):
        pair = reduce(lambda x, y: x if x > y else y, \
            WEIGHT_COST_MAP[self.service_type])
        max_weight_class = pair[0]

        if not self._weight() > max_weight_class:
            return [self._cart_as_shipment()]
        else:
            shipments = []
            a_shipment = []
            the_weight = Decimal('0')
            b = None
            for cartitem in self.cart.cartitem_set.all():
                for i in xrange(cartitem.quantity):
                    b = the_weight + Decimal(cartitem.product.weight)

                    if b <= max_weight_class:
                        the_weight = b
                        a_shipment.append(cartitem)

                        if b == max_weight_class:
                            shipments.append(a_shipment)
                            a_shipment = []
                    else:
                        shipments.append(a_shipment)
                        a_shipment = [cartitem]
                        the_weight = cartitem.product.weight

            if len(a_shipment):
                shipments.append(a_shipment)

            return shipments

    def _cost_for_shipment(self, shipment):
        total_weight = self._weight_for_shipment(shipment)

        prev = None
        result_cost = None

        for weight_class, weight_class_cost in \
            WEIGHT_COST_MAP[self.service_type]:
            if total_weight <= Decimal(weight_class):
                if prev:
                    if total_weight > Decimal(prev):
                        result_cost = weight_class_cost
                        break
            else:
                prev = weight_class

        return result_cost

    def cost(self):
        """
        Complex calculations can be done here as long as the return value is a dollar figure
        """
        assert(self._calculated)

        shipments = self._partitioned_shipments()

        total_cost = Decimal('0.00')

        for shipment in shipments:
            total_cost += self._cost_for_shipment(shipment)

        return total_cost

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
