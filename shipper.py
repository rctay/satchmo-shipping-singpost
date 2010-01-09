"""
Copyright (C) 2009-2010, Tay Ray Chuan

Please see LICENCE for licensing details.
"""

"""
Each shipping option uses the data in an Order object to calculate the shipping cost and return the value
"""
try:
    from decimal import Decimal
except:
    from django.utils._decimal import Decimal

from django.utils.translation import ugettext as _
from livesettings import config_value
from shipping.modules.base import BaseShipper

class WeightCostMap:
    def __init__(self, map):
        self.map = map

    def get_lowest_cost(self):
        return reduce(lambda x, y: x if x < y else y, self.map)[1]

    def get_heaviest_weight(self):
        return reduce(lambda x, y: x if x > y else y, self.map)[0]

    def cost_for_weight(self, total_weight):
        prev = None
        result_cost = None

        for weight, cost in self.map:
            if total_weight <= Decimal(weight):
                if prev:
                    if total_weight > Decimal(prev):
                        result_cost = cost
                        break
            else:
                prev = weight

        return result_cost

WEIGHT_COST_MAPS = {
    'LOCAL': WeightCostMap((
        (40,	Decimal('0.50')),
        (100,	Decimal('0.80')),
        (250,	Decimal('1.00')),
        (500,	Decimal('1.50')),
        (1000,	Decimal('2.55')),
        (2000,	Decimal('3.35'))
    )),
}

class Shipper(BaseShipper):
    id = "SingPost"

    def __init__(self, cart=None, contact=None, service_type='LOCAL'):
        super(Shipper, self).__init__(cart, contact)

        self.service_type = service_type

    def __str__(self):
        """
        This is mainly helpful for debugging purposes
        """
        return "SingPost"

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
    def _partitioned_shipments(self, wcm):
        max_weight = wcm.get_heaviest_weight()

        if not self._weight() > max_weight:
            return [self._cart_as_shipment()]
        else:
            shipments = []
            a_shipment = []
            the_weight = Decimal('0')
            b = None
            for cartitem in self.cart.cartitem_set.all():
                for i in xrange(cartitem.quantity):
                    b = the_weight + Decimal(cartitem.product.weight)

                    if b <= max_weight:
                        the_weight = b
                        a_shipment.append(cartitem)

                        if b == max_weight:
                            shipments.append(a_shipment)
                            a_shipment = []
                    else:
                        shipments.append(a_shipment)
                        a_shipment = [cartitem]
                        the_weight = cartitem.product.weight

            if len(a_shipment):
                shipments.append(a_shipment)

            return shipments

    def _cost_for_shipment(self, shipment, wcm):
        total_weight = self._weight_for_shipment(shipment)

        result_cost = wcm.cost_for_weight(total_weight)

        # use the lightest class
        if result_cost is None:
            result_cost = wcm.get_lowest_cost()

        return result_cost

    def cost(self):
        """
        Complex calculations can be done here as long as the return value is a dollar figure
        """
        assert(self._calculated)

        wcm = WEIGHT_COST_MAPS[self.service_type]

        shipments = self._partitioned_shipments(wcm)

        total_cost = Decimal('0.00')

        for shipment in shipments:
            total_cost += self._cost_for_shipment(shipment, wcm)

        return total_cost

    def method(self):
        """
        Describes the actual delivery service (Mail, FedEx, DHL, UPS, etc)
        """
        return _('SingPost')

    def expectedDelivery(self):
        """
        Can be a plain string or complex calcuation returning an actual date
        """
        return _('3-4 business days')

    def valid(self, order=None):
        """
        Can do complex validation about whether or not this option is valid.
        For example, may check to see if the recipient is in an allowed country
        or location.
        """
        return True
