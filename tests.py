"""
Copyright (C) 2009-2010, Tay Ray Chuan

Please see LICENCE for licensing details.
"""

import unittest

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.sites.models import Site
from satchmo_store.shop.models import Cart
from product.models import Product

from shipper import Shipper as singpost

try:
    from decimal import Decimal
except ImportError:
    from django.utils._decimal import Decimal

def get_product_blouse():
    try:
        p = Product.objects.get(slug='shoulder-blouse')
    except ObjectDoesNotExist:
        p = Product.objects.create(
            site=Site.objects.get_current(),
            name='Shoulder Blouse',
            slug='shoulder-blouse',
            items_in_stock=10,
            weight='315', weight_units='gms')

    return p

def get_product_dress():
    try:
        p = Product.objects.get(slug='lovely-dress')
    except ObjectDoesNotExist:
        p = Product.objects.create(
            site=Site.objects.get_current(),
            name='Lovely Dress',
            slug='lovely-dress',
            items_in_stock=10,
            weight='42', weight_units='gms')

    return p

def get_product_skirt():
    try:
        p = Product.objects.get(slug='denim-skirt')
    except ObjectDoesNotExist:
        p = Product.objects.create(
            site=Site.objects.get_current(),
            name='Denim Skirt',
            slug='denim-skirt',
            items_in_stock=10,
            weight='115', weight_units='gms')

    return p

class LocalTestCaseNormal(unittest.TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_shipping(self):
        cart1 = Cart.objects.create(site=self.site)
        cart2 = Cart.objects.create(site=self.site)

        p1 = get_product_blouse()

        cart1.add_item(p1, 1)
        cart2.add_item(p1, 3)

        ship1 = singpost(cart=cart1, service_type='LOCAL')
        ship2 = singpost(cart=cart2, service_type='LOCAL')

        self.assertTrue(p1.is_shippable)

        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('315'))
        self.assertEqual(ship1.cost(), Decimal('1.50'))

        self.assertTrue(cart2.is_shippable)
        self.assertEqual(ship2._weight(), Decimal('945'))
        self.assertEqual(ship2.cost(), Decimal('2.55'))

class LocalTestCaseHeavy(unittest.TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_shipping1(self):
        p1 = get_product_blouse()

        p2 = Product.objects.create(
            site=self.site,
            name='Shoulder Blouse3',
            slug='shoulder-blouse3',
            items_in_stock=10,
            weight='200', weight_units='gms')

        # should split into 2 shipments: [6, 3]
        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(p1, 9)
        ship1 = singpost(cart=cart1, service_type='LOCAL')
        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('2835'))
        self.assertEqual(ship1.cost(), Decimal('5.90'))

        # should split into 2 shipments: [6, 3p1+5p2, 1p2]
        cart2 = Cart.objects.create(site=self.site)
        cart2.add_item(p1, 9)
        cart2.add_item(p2, 6)
        ship2 = singpost(cart=cart2, service_type='LOCAL')
        self.assertTrue(cart2.is_shippable)
        self.assertEqual(ship2._weight(), Decimal('4035'))
        self.assertEqual(ship2.cost(), Decimal('7.70'))

        # exceeds max weight and can't be split
        p3 = Product.objects.create(
            site=self.site,
            name='Shoulder Blouse4',
            slug='shoulder-blouse4',
            items_in_stock=10,
            weight='2001', weight_units='gms')
        cart3 = Cart.objects.create(site=self.site)
        cart3.add_item(p3, 1)
        ship3 = singpost(cart=cart3, service_type='LOCAL')
        self.assertTrue(cart3.is_shippable)
        self.assertEqual(ship3._weight(), Decimal('2001'))
        self.assertEqual(ship3.cost(), None)

class LocalTestCaseLight(unittest.TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_shipping1(self):
        p1 = Product.objects.create(
            site=self.site,
            name='Stipple Sponge',
            slug='stipple-sponge',
            items_in_stock=10,
            weight='1.6', weight_units='gms')

        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(p1, 1)
        ship1 = singpost(cart=cart1, service_type='LOCAL')
        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('1.6'))
        self.assertEqual(ship1.cost(), Decimal('0.50'))

class SurfaceTestCaseNormal(unittest.TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

    def test_shipping1(self):
        p1 = get_product_dress()
        p2 = get_product_blouse()
        p3 = get_product_skirt()

        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(p1, 1)
        ship1 = singpost(cart=cart1, service_type='SURFACE')
        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('42'))
        self.assertEqual(ship1.cost(), Decimal('0.70'))

        cart2 = Cart.objects.create(site=self.site)
        cart2.add_item(p2, 1)
        ship2 = singpost(cart=cart2, service_type='SURFACE')
        self.assertTrue(cart2.is_shippable)
        self.assertEqual(ship2._weight(), Decimal('315'))
        self.assertEqual(ship2.cost(), Decimal('4.00'))

        cart3 = Cart.objects.create(site=self.site)
        cart3.add_item(p3, 1)
        ship3 = singpost(cart=cart3, service_type='SURFACE')
        self.assertTrue(cart3.is_shippable)
        self.assertEqual(ship3._weight(), Decimal('115'))
        self.assertEqual(ship3.cost(), Decimal('2.00'))

        cart4 = Cart.objects.create(site=self.site)
        cart4.add_item(p1, 2)
        ship4 = singpost(cart=cart4, service_type='SURFACE')
        self.assertTrue(cart4.is_shippable)
        self.assertEqual(ship4._weight(), Decimal('84'))
        self.assertEqual(ship4.cost(), Decimal('1.00'))
