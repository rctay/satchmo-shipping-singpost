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

class SingPostTestCaseNormal(unittest.TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

        self.p1 = Product.objects.create(
            site=self.site,
            name='Shoulder Blouse',
            slug='shoulder-blouse',
            items_in_stock=10,
            weight='315', weight_units='gms')

    def test_shipping(self):
        cart1 = Cart.objects.create(site=self.site)
        cart2 = Cart.objects.create(site=self.site)

        cart1.add_item(self.p1, 1)
        cart2.add_item(self.p1, 3)

        self.ship1 = singpost(cart1, None)
        ship2 = singpost(cart2, None)

        self.assertTrue(self.p1.is_shippable)

        self.assertTrue(cart1.is_shippable)
        self.assertEqual(self.ship1._weight(), Decimal('315'))
        self.assertEqual(self.ship1.cost(), Decimal('1.50'))

        self.assertTrue(cart2.is_shippable)
        self.assertEqual(ship2._weight(), Decimal('945'))
        self.assertEqual(ship2.cost(), Decimal('2.55'))

class SingPostTestCaseHeavy(unittest.TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

        self.p1 = Product.objects.create(
            site=self.site,
            name='Shoulder Blouse2',
            slug='shoulder-blouse2',
            items_in_stock=10,
            weight='315', weight_units='gms')

        self.p2 = Product.objects.create(
            site=self.site,
            name='Shoulder Blouse3',
            slug='shoulder-blouse3',
            items_in_stock=10,
            weight='200', weight_units='gms')

    def test_shipping1(self):
        # should split into 2 shipments: [6, 3]
        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(self.p1, 9)
        ship1 = singpost(cart1, None)
        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('2835'))
        self.assertEqual(ship1.cost(), Decimal('5.90'))

        # should split into 2 shipments: [6, 3p1+5p2, 1p2]
        cart2 = Cart.objects.create(site=self.site)
        cart2.add_item(self.p1, 9)
        cart2.add_item(self.p2, 6)
        ship2 = singpost(cart2, None)
        self.assertTrue(cart2.is_shippable)
        self.assertEqual(ship2._weight(), Decimal('4035'))
        self.assertEqual(ship2.cost(), Decimal('7.70'))
