"""
Copyright (C) 2009, Tay Ray Chuan

Please see LICENCE for licensing details.
"""

import unittest

from django.contrib.sites.models import Site
from satchmo.shop.models import Cart
from satchmo.product.models import Product

from shipper import Shipper as singpost

try:
    from decimal import Decimal
except ImportError:
    from django.utils._decimal import Decimal

class SingPostTestCase(unittest.TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

        self.p1 = Product.objects.create(
            site=self.site,
            name='Shoulder Blouse',
            slug='shoulder-blouse',
            items_in_stock=10,
            weight=315, weight_units='gms')

    def test_shipping(self):
        cart1 = Cart.objects.create(site=self.site)
        cart2 = Cart.objects.create(site=self.site)

        cart1.add_item(self.p1, 1)
        cart2.add_item(self.p1, 3)

        self.assertTrue(self.p1.is_shippable)

        self.assertTrue(cart1.is_shippable)
        self.assertEqual(singpost(cart1, None).cost(), Decimal('1.50'))

        self.assertTrue(cart2.is_shippable)
        self.assertEqual(singpost(cart2, None).cost(), Decimal('2.55'))
