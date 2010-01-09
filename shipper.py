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

import logging
log = logging.getLogger('singpost.shipper')

class BaseWeightCostMap(object):
    def __init__(self, map):
        self.map = map

        self.maximum_item_weight = None

    def get_lowest_cost(self):
        return reduce(lambda x, y: x if x < y else y, self.map)[1]

    def get_heaviest_weight(self):
        return reduce(lambda x, y: x if x > y else y, self.map)[0]

    def cost_for_shipment_with_weight(self, shipment_weight):
        raise NotImplementedError

    """
    Returns a list of shipments.
    """
    def partitioned_shipments(self, total_weight, cart):
        raise NotImplementedError

class TieredWeightCostMap(BaseWeightCostMap):
    def __init__(self, *args, **kwargs):
        super(TieredWeightCostMap, self).__init__(*args, **kwargs)

        self.maximum_item_weight = self.get_heaviest_weight()

    """
    The weight of a single must fall within specified "tiers", therefore the
    maximum allowed weight of a single item is the heaviest weight
    specified in map.
    """
    def cost_for_shipment_with_weight(self, shipment_weight):
        if (shipment_weight > self.maximum_item_weight):
            log.error("shipment weight exceeds maximum allowed weight: weight=%d, max=%d" \
                % (shipment_weight, self.maximum_item_weight))
            return None

        prev = None
        result_cost = None

        for weight, cost in self.map:
            if shipment_weight <= Decimal(weight):
                if prev:
                    if shipment_weight > Decimal(prev):
                        result_cost = cost
                        break
            else:
                prev = weight

        return result_cost

    def partitioned_shipments(self, total_weight, cart):
        shipments = []
        a_shipment = []

        if total_weight < self.maximum_item_weight:
            # optimized version - no need to check weight for every item
            for cartitem in cart.cartitem_set.all():
                for i in xrange(cartitem.quantity):
                    a_shipment.append(cartitem)
        else:
            the_weight = Decimal('0')
            new_weight = None
            for cartitem in cart.cartitem_set.all():
                for i in xrange(cartitem.quantity):
                    new_weight = the_weight + Decimal(cartitem.product.weight)

                    if new_weight <= self.maximum_item_weight:
                        the_weight = new_weight
                        a_shipment.append(cartitem)

                        if new_weight == self.maximum_item_weight:
                            shipments.append(a_shipment)
                            a_shipment = []
                    elif len(a_shipment) > 0 and the_weight > Decimal('0'):
                        shipments.append(a_shipment)
                        a_shipment = [cartitem]
                        the_weight = Decimal(cartitem.product.weight)
                    else:
                        log.error("item exceeds max weight: name=%s, weight=%d" \
                            % (cartitem.product.name, cartitem.product.weight))
                        return None

        if len(a_shipment):
            shipments.append(a_shipment)

        return shipments

WEIGHT_COST_MAPS = {
    'LOCAL': TieredWeightCostMap(map=(
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

    def _cost_for_shipment(self, shipment, wcm):
        shipment_weight = self._weight_for_shipment(shipment)

        result_cost = wcm.cost_for_shipment_with_weight(shipment_weight)

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

        shipments = wcm.partitioned_shipments(self._weight(), self.cart)

        if shipments == None:
            return None

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
