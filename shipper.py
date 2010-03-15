"""
Copyright (C) 2009-2010, Tay Ray Chuan

Please see LICENCE for licensing details.
"""

"""
Each shipping option uses the data in an Order object to calculate the shipping cost and return the value
"""
try:
    from decimal import getcontext, Decimal, InvalidOperation
except:
    from django.utils._decimal import getcontext, Decimal, InvalidOperation

from django.utils.translation import ugettext as _
from livesettings import config_value
from shipping.modules.base import BaseShipper
import re

import logging
log = logging.getLogger('singpost.shipper')

def safe_get_decimal(val):
    try:
        d = Decimal(val)
    except (ValueError, TypeError, InvalidOperation):
        d = Decimal(0)

    return d

class CountryFilter(object):
    """
    If a country is found in the exclude tuple, return False immediately.

    A positive match for countries and continents (referred to as x) occurs
    when:
    1. The relevant tuple is None, OR

    2i). The relevant tuple is not empty, AND
    2ii). x is found found in the relevant tuple

    If there is a positive match for both the country and continent, return
    True.
    """
    def __init__(self, include=None, exclude=None,
        include_continent=None):
        self.include = include
        self.exclude = exclude

        self.include_continent = include_continent

    def country_is_included(self, country):
        if not self.exclude == None and len(self.exclude) \
            and country.iso2_code in self.exclude:
            return False

        match_continent = False
        match_country = False

        if self.include_continent == None or \
            (len(self.include_continent) and country.continent in self.include_continent):
            match_continent = True

        if self.include == None or \
            (len(self.include) and country.iso2_code in self.include):
            match_country = True

        return match_continent and match_country

class BaseCostTiers(object):
    def __init__(self, tiers, filter=CountryFilter()):
        self.tiers = tiers

        self.maximum_item_weight = None
        self.filter = filter

    def get_lowest_cost(self):
        return reduce(lambda x, y: x if x < y else y, self.tiers)[1]

    def get_heaviest_weight_tier(self):
        return reduce(lambda x, y: x if x > y else y, self.tiers)

    def get_heaviest_weight(self):
        return self.get_heaviest_weight_tier()[0]

    def cost_for_shipment_with_weight(self, shipment_weight):
        raise NotImplementedError

    """
    Returns a list of shipments.
    """
    def partitioned_shipments(self, total_weight, cart):
        raise NotImplementedError

class ExplicitCostTiers(BaseCostTiers):
    def __init__(self, *args, **kwargs):
        super(ExplicitCostTiers, self).__init__(*args, **kwargs)

        self.maximum_item_weight = self.get_heaviest_weight()

    """
    The weight of a single must fall within specified "tiers", therefore the
    maximum allowed weight of a single item is the heaviest weight
    specified in tiers.
    """
    def cost_for_shipment_with_weight(self, shipment_weight):
        if (shipment_weight > self.maximum_item_weight):
            log.error("shipment weight exceeds maximum allowed weight: " \
                "weight=%d, max=%d" \
                % (shipment_weight, self.maximum_item_weight))
            return None

        prev = None
        result_cost = None

        for weight, cost in self.tiers:
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
            the_weight = Decimal(0)
            new_weight = None
            for cartitem in cart.cartitem_set.all():
                for i in xrange(cartitem.quantity):
                    product_weight = safe_get_decimal(cartitem.product.weight)
                    new_weight = the_weight + product_weight

                    if new_weight <= self.maximum_item_weight:
                        the_weight = new_weight
                        a_shipment.append(cartitem)

                        if new_weight == self.maximum_item_weight:
                            shipments.append(a_shipment)
                            a_shipment = []
                    elif len(a_shipment) > 0 and the_weight > Decimal(0):
                        shipments.append(a_shipment)
                        a_shipment = [cartitem]
                        the_weight = product_weight
                    else:
                        log.error("item exceeds max weight: " \
                            "name=%s, weight=%d" \
                            % (cartitem.product.name, cartitem.product.weight))
                        return None

        if len(a_shipment):
            shipments.append(a_shipment)

        return shipments

class ImplicitCostTiers(ExplicitCostTiers):
    """
    implied_tier --- A tuple of (weight_step, Decimal(n)) form. When weight
    exceeds the last specified weight in tiers, cost is added for every
    additional weight_step.
    """
    def __init__(self, implied_tier, maximum_item_weight,
        *args, **kwargs):
        super(ImplicitCostTiers, self).__init__(*args, **kwargs)

        self.maximum_item_weight = maximum_item_weight
        self.implied_tier = implied_tier

    def cost_for_shipment_with_weight(self, shipment_weight):
        max_tier = self.get_heaviest_weight_tier()

        if (shipment_weight <= max_tier[0]):
            prev = None
            result_cost = None

            for weight, cost in self.tiers:
                if shipment_weight <= Decimal(weight):
                    if prev:
                        if shipment_weight > Decimal(prev):
                            result_cost = cost
                            break
                else:
                    prev = weight
        else:
            result = getcontext().divmod(
                Decimal(shipment_weight - max_tier[0]),
                Decimal(self.implied_tier[0]))
            steps = result[0] + (1 if result[1] > Decimal(0) else 0)
            result_cost = max_tier[1] + steps * self.implied_tier[1]

        return result_cost

class ZonedCostTiers(ImplicitCostTiers):
    def __init__(self, maximum_item_weight=None,
        *args, **kwargs):
        super(ZonedCostTiers, self).__init__(
            maximum_item_weight=maximum_item_weight,
            *args, **kwargs)

class ZonedCostTiersSet(BaseCostTiers):
    def __init__(self, zones, maximum_item_weight, tiers=None,
        *args, **kwargs):
        super(ZonedCostTiersSet, self).__init__(tiers=tiers,
            *args, **kwargs)

        self.maximum_item_weight = maximum_item_weight

        for zone in zones:
            zone.maximum_item_weight = self.maximum_item_weight

        self.zones = zones

    def tier_for_country(self, country):
        for zone in self.zones:
            if zone.filter.country_is_included(country):
                return zone

        log.error('Could not determine zone for country:' \
        'country=%s' % country)
        return None

SERVICE_TIERS = {
    'LOCAL': ExplicitCostTiers(
        tiers=(
            (40,	Decimal('0.50')),
            (100,	Decimal('0.80')),
            (250,	Decimal('1.00')),
            (500,	Decimal('1.50')),
            (1000,	Decimal('2.55')),
            (2000,	Decimal('3.35'))
        ),
        filter = CountryFilter(include=('SG',))
    ),
    'SURFACE': ImplicitCostTiers(
        tiers=(
            (20,	Decimal('0.50')),
            (50,	Decimal('0.70')),
            (100,	Decimal('1.00'))
        ),
        implied_tier=(100, Decimal('1.00')),
        maximum_item_weight=2000,
        filter = CountryFilter(exclude=('MY', 'BN'))
    ),
    'AIR': ZonedCostTiersSet(
        zones=(
            ZonedCostTiers(
                tiers=(
                    (20,	Decimal('0.45')),
                    (50,	Decimal('0.55')),
                    (100,	Decimal('0.85'))
                ),
                implied_tier=(100, Decimal('1.00')),
                filter = CountryFilter(include=('MY', 'BN'))
            ),
            ZonedCostTiers(
                tiers=(
                    (20,	Decimal('0.65')),
                ),
                implied_tier=(10, Decimal('0.25')),
                filter = CountryFilter(
                    include=(
                        'AS', # American Samoa
                        'KI', # Kiribati
                        'NR', # Nauru
                        'SB', # Solomon Islands
                        'BD', # Bangladesh
                        'KP', # Korea, Dem. People's Rep. of
                        'NP', # Nepal
                        'LK', # Sri Lanka
                        'BT', # Bhutan
                        'KR', # Korea, Rep. of (South)
                        'NC', # New Caledonia
                        'TW', # Taiwan
                        'KH', # Cambodia
                        'LA', # Lao
                        'MP', # Northern Mariana Islands
                        'TH', # Thailand
                        'CN', # China
                        'MO', # Macao
                        'PK', # Pakistan
                        'TL', # Timor-Leste
                        'FJ', # Fiji
                        'MV', # Maldives
                        'PW', # Palau
                        'TO', # Tonga
                        'PF', # French Polynesia
                        'MH', # Marshall Islands
                        'PG', # Papua New Guinea
                        'TV', # Tuvalu
                        'GU', # Guam
                        'FM', # Micronesia, Fed. States of
                        'PH', # Philippines
                        'VU', # Vanuatu
                        'HK', # Hong Kong
                        'MN', # Mongolia
                        'PN', # Pitcairn Islands
                        'VN', # Viet Nam
                        'IN', # India
                        'MM', # Myanmar
                        'WS', # Samoa
                        'WF', # Wallis and Futuna
                        'ID', # Indonesia
                    )
                )
            ),
            ZonedCostTiers(
                tiers=(
                    (20,	Decimal('1.10')),
                ),
                implied_tier=(10, Decimal('0.35'))
            ),
        ),
        maximum_item_weight=2000,
        filter = CountryFilter(exclude=('SG'))
    ),

    'LOCAL_REGISTERED': None,
    'SURFACE_REGISTERED': None,
    'AIRMAIL_REGISTERED': None,
}

HAS_SURCHARGE_PATTERN = '^(.+)_REGISTERED$'

class Surcharge(object):
    """
    An additional charge to be applied on top of the cost calculated by a
    :ref:`singpost.shipper.BaseCostTier <tier>`.

    Satchmo doesn't allow one to this very easily on a per-service basis, so we
    just present a totally separate service to the user.

    :param: charge: The additional fee to be applied.
    """
    def __init__(self, charge, filter):
       self.charge = safe_get_decimal(charge or 0)
       self.filter = filter

REGISTERED_SURCHARGE = (
    Surcharge(Decimal('2.24'), CountryFilter(include=('SG'))),
    Surcharge(Decimal('2.20'), CountryFilter(exclude=('SG'))),
)

class Shipper(BaseShipper):
    def __init__(self, cart=None, contact=None, service_type=None):
        super(Shipper, self).__init__(cart, contact)

        self.service_type_code = service_type[0]
        self.service_type_description = service_type[1]

        self.id = self.service_type_code

    def __str__(self):
        """
        This is mainly helpful for debugging purposes
        """
        return self.description()

    def description(self):
        """
        A basic description that will be displayed to the user when selecting their shipping options
        """
        return _("SingPost - %s" % self.service_type_description)

    def _get_surcharge(self):
        m = re.match(HAS_SURCHARGE_PATTERN, self.service_type_code)
        if not m:
            return Decimal(0)

        s = None
        for surcharge in REGISTERED_SURCHARGE:
            if surcharge.filter.country_is_included(
                self.contact.shipping_address.country):
                s = surcharge

        if not s:
            return Decimal(0)

        return s.charge
    surcharge = property(_get_surcharge)

    def _get_tier(self):
        tier_code = self.service_type_code

        m = re.match(HAS_SURCHARGE_PATTERN, self.service_type_code)
        if m:
            tier_code = m.group(1)

        tier = SERVICE_TIERS[tier_code]

        if not tier.filter.country_is_included(
            self.contact.shipping_address.country):
            return None

        if tier.tiers == None and hasattr(tier, 'zones'):
            tier = tier.tier_for_country(self.contact.shipping_address.country)

        return tier
    tier = property(_get_tier)

    def _weight_for_shipment(self, shipment):
        total_weight = Decimal(0)

        for cartitem in shipment:
            if cartitem.product.is_shippable:
                total_weight += safe_get_decimal(cartitem.product.weight)

        return total_weight

    def _weight(self):
        total_weight = Decimal(0)

        for cartitem in self.cart.cartitem_set.all():
            if cartitem.product.is_shippable:
                total_weight += safe_get_decimal(cartitem.product.weight) * \
                                safe_get_decimal(cartitem.quantity)

        return total_weight

    def _cost_for_shipment(self, shipment, tier):
        shipment_weight = self._weight_for_shipment(shipment)

        result_cost = tier.cost_for_shipment_with_weight(shipment_weight)

        # use the lightest class
        if result_cost is None:
            result_cost = tier.get_lowest_cost()

        return result_cost

    def cost(self):
        """
        Complex calculations can be done here as long as the return value is a dollar figure
        """
        assert(self._calculated)

        if self.tier == None:
            return None

        shipments = self.tier.partitioned_shipments(self._weight(), self.cart)
        if shipments == None or not len(shipments):
            return None

        total_cost = Decimal(0)

        for shipment in shipments:
            total_cost += self._cost_for_shipment(shipment, self.tier) + self.surcharge

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
        ret = True if not self.tier == None else False
        return ret
