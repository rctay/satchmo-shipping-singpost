# coding: utf-8
"""
Copyright (C) 2009-2010, Tay Ray Chuan

Please see LICENCE for licensing details.
"""

import unittest

from django.core.exceptions import ObjectDoesNotExist
from django.contrib.sites.models import Site
from l10n.models import Country
from satchmo_store.contact.models import Contact
from satchmo_store.shop.models import Cart
from product.models import Product

from shipper import Shipper as singpost

try:
    from decimal import Decimal
except ImportError:
    from django.utils._decimal import Decimal

class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.site = Site.objects.get_current()

        self.product_blouse = self._get_product_blouse()
        self.product_dress = self._get_product_dress()
        self.product_skirt = self._get_product_skirt()

        self.contact_sg = self._get_contact_sg()
        self.contact_my = self._get_contact_my()
        self.contact_bn = self._get_contact_bn()
        self.contact_th = self._get_contact_th()
        self.contact_au = self._get_contact_au()
        self.contact_as = self._get_contact_as()
        self.contact_jo = self._get_contact_jo()

    def _get_product_blouse(self):
        p, created = Product.objects.get_or_create(
            slug='shoulder-blouse',
            defaults={
                'site': Site.objects.get_current(),
                'name': 'Shoulder Blouse',
                'items_in_stock': 10,
                'weight': '315', 'weight_units': 'gms'
            })

        return p

    def _get_product_dress(self):
        p, created = Product.objects.get_or_create(
            slug='lovely-dress',
            defaults={
                'site': Site.objects.get_current(),
                'name': 'Lovely Dress',
                'items_in_stock': 10,
                'weight': '42', 'weight_units': 'gms'
            })

        return p

    def _get_product_skirt(self):
        p, created = Product.objects.get_or_create(
            slug='denim-skirt',
            defaults={
                'site': Site.objects.get_current(),
                'name': 'Denim Skirt',
                'items_in_stock': 30,
                'weight': '115', 'weight_units': 'gms'
            })

        return p

    def _get_contact_sg(self):
        try:
            contact = Contact.objects.get(first_name='Ahsia', last_name='Kia')
        except ObjectDoesNotExist:
            contact = Contact.objects.create(first_name='Ahsia', last_name='Kia')
            contact.addressbook_set.create(street1='1 Orchard Rd',
                city='Singapore', postal_code='123456',
                country=Country.objects.create(
                    iso2_code='SG', iso3_code='SGP',
                    name='SINGAPORE', printable_name='Singapore',
                    continent='AS'
                )
            )

        return contact

    def _get_contact_my(self):
        try:
            contact = Contact.objects.get(first_name='Iam', last_name='Malaysian')
        except ObjectDoesNotExist:
            contact = Contact.objects.create(first_name='Iam', last_name='Malaysian')
            contact.addressbook_set.create(street1='Jalan P Ramlee',
                city='Kuala Lumpur', postal_code='50250',
                country=Country.objects.create(
                    iso2_code='MY', iso3_code='MYS',
                    name='MALAYSIA', printable_name='Malaysia',
                    continent='AS'
                )
            )

        return contact

    def _get_contact_bn(self):
        try:
            contact = Contact.objects.get(first_name='Iam', last_name='Bruneian')
        except ObjectDoesNotExist:
            contact = Contact.objects.create(first_name='Iam', last_name='Bruneian')
            contact.addressbook_set.create(street1=u'15½ Jalan Kota Batu',
                city='Brunei Darussalam', postal_code='BU2529',
                country=Country.objects.create(
                    iso2_code='BN', iso3_code='BRN',
                    name='BRUNEI DARUSSALAM', printable_name='Brunei Darussalam',
                    continent='AS'
                )
            )

        return contact

    def _get_contact_th(self):
        try:
            contact = Contact.objects.get(first_name='Iam', last_name='Thai')
        except ObjectDoesNotExist:
            contact = Contact.objects.create(first_name='Iam', last_name='Thai')
            contact.addressbook_set.create(street1='24 Sukhumvit',
                city='Bangkok', postal_code='10110',
                country=Country.objects.create(
                    iso2_code='TH', iso3_code='THA',
                    name='THAILAND', printable_name='Thailand',
                    continent='AS'
                )
            )

        return contact

    def _get_contact_au(self):
        try:
            contact = Contact.objects.get(first_name='Iam', last_name='Australian')
        except ObjectDoesNotExist:
            contact = Contact.objects.create(first_name='Iam', last_name='Australian')
            contact.addressbook_set.create(street1='100 St Kilda Rd',
                city='Melbourne', state='Victoria', postal_code='3004',
                country=Country.objects.create(
                    iso2_code='AU', iso3_code='AUS',
                    name='AUSTRALIA', printable_name='Australia',
                    continent='OC'
                )
            )

        return contact

    def _get_contact_as(self):
        try:
            contact = Contact.objects.get(first_name='Iam', last_name='Samoan')
        except ObjectDoesNotExist:
            contact = Contact.objects.create(first_name='Iam', last_name='Samoan')
            contact.addressbook_set.create(street1='Pago Pago',
                city='Pago Pago', postal_code='96799',
                country=Country.objects.create(
                    iso2_code='AS', iso3_code='ASM',
                    name='AMERICAN SAMOA', printable_name='American Samoa',
                    continent='OC'
                )
            )

        return contact

    def _get_contact_jo(self):
        try:
            contact = Contact.objects.get(first_name='Iam', last_name='Jordanian')
        except ObjectDoesNotExist:
            contact = Contact.objects.create(first_name='Iam', last_name='Jordanian')
            contact.addressbook_set.create(street1='Islamic College Street',
                city='Amman', postal_code='11180',
                country=Country.objects.create(
                    iso2_code='JO', iso3_code='JOR',
                    name='JORDAN', printable_name='Jordan',
                    continent='AS'
                )
            )

        return contact

class LocalShippingTestCase(BaseTestCase):
    def test_simple_shipping(self):
        p1 = self.product_blouse
        self.assertTrue(p1.is_shippable)

        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(p1, 1)
        ship1 = singpost(cart=cart1, service_type=('LOCAL',''), contact=self.contact_sg)
        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('315'))
        self.assertEqual(ship1.cost(), Decimal('1.50'))

        ship1_r = singpost(cart=cart1, service_type=('LOCAL_REGISTERED',''), contact=self.contact_sg)
        self.assertEqual(ship1_r._weight(), Decimal('315'))
        self.assertEqual(ship1_r.cost(), Decimal('3.74'))

        cart2 = Cart.objects.create(site=self.site)
        cart2.add_item(p1, 3)
        ship2 = singpost(cart=cart2, service_type=('LOCAL',''), contact=self.contact_sg)
        self.assertTrue(cart2.is_shippable)
        self.assertEqual(ship2._weight(), Decimal('945'))
        self.assertEqual(ship2.cost(), Decimal('2.55'))

    def test_simple_shipping2(self):
        p1 = Product.objects.create(
            site=self.site,
            name='Stipple Sponge',
            slug='stipple-sponge',
            items_in_stock=10,
            weight='1.6', weight_units='gms')

        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(p1, 1)
        ship1 = singpost(cart=cart1, service_type=('LOCAL',''), contact=self.contact_sg)
        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('1.6'))
        self.assertEqual(ship1.cost(), Decimal('0.50'))

    def test_partitioned_shipping(self):
        p1 = self.product_blouse
        p2 = self.product_skirt

        # should split into 2 shipments: [6, 3]
        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(p1, 9)
        ship1 = singpost(cart=cart1, service_type=('LOCAL',''), contact=self.contact_sg)
        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('2835'))
        self.assertEqual(ship1.cost(), Decimal('5.90'))

        # should split into 2 shipments: [6, 3p1+9p2, 1p2]
        cart2 = Cart.objects.create(site=self.site)
        cart2.add_item(p1, 9)
        cart2.add_item(p2, 10)
        ship2 = singpost(cart=cart2, service_type=('LOCAL',''), contact=self.contact_sg)
        self.assertTrue(cart2.is_shippable)
        self.assertEqual(ship2._weight(), Decimal('3985'))
        self.assertEqual(ship2.cost(), Decimal('7.70'))

    def test_heavy_item(self):
        # exceeds max weight and can't be split
        p3 = Product.objects.create(
            site=self.site,
            name='Shoulder Blouse4',
            slug='shoulder-blouse4',
            items_in_stock=10,
            weight='2001', weight_units='gms')
        cart3 = Cart.objects.create(site=self.site)
        cart3.add_item(p3, 1)
        ship3 = singpost(cart=cart3, service_type=('LOCAL',''), contact=self.contact_sg)
        self.assertTrue(cart3.is_shippable)
        self.assertEqual(ship3._weight(), Decimal('2001'))
        self.assertEqual(ship3.cost(), None)

    def test_country_filter(self):
        p1 = self.product_blouse
        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(p1, 1)

        ship1 = singpost(cart=cart1, service_type=('LOCAL',''), contact=self.contact_sg)
        self.assertEqual(ship1.cost(), Decimal('1.50'))
        self.assertEqual(ship1.valid(), True)

        ship2 = singpost(cart=cart1, service_type=('LOCAL',''), contact=self.contact_my)
        self.assertEqual(ship2.cost(), None)
        self.assertEqual(ship2.valid(), False)

class SurfaceTestCase(BaseTestCase):
    def test_shipping1(self):
        p1 = self.product_dress
        p2 = self.product_blouse
        p3 = self.product_skirt

        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(p1, 1)
        ship1 = singpost(cart=cart1, service_type=('SURFACE',''), contact=self.contact_sg)
        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('42'))
        self.assertEqual(ship1.cost(), Decimal('0.70'))

        cart2 = Cart.objects.create(site=self.site)
        cart2.add_item(p2, 1)
        ship2 = singpost(cart=cart2, service_type=('SURFACE',''), contact=self.contact_sg)
        self.assertTrue(cart2.is_shippable)
        self.assertEqual(ship2._weight(), Decimal('315'))
        self.assertEqual(ship2.cost(), Decimal('4.00'))

        cart3 = Cart.objects.create(site=self.site)
        cart3.add_item(p3, 1)
        ship3 = singpost(cart=cart3, service_type=('SURFACE',''), contact=self.contact_sg)
        self.assertTrue(cart3.is_shippable)
        self.assertEqual(ship3._weight(), Decimal('115'))
        self.assertEqual(ship3.cost(), Decimal('2.00'))

        ship3_r = singpost(cart=cart3, service_type=('SURFACE_REGISTERED',''), contact=self.contact_sg)
        self.assertEqual(ship3_r._weight(), Decimal('115'))
        self.assertEqual(ship3_r.cost(), Decimal('4.24'))

        cart4 = Cart.objects.create(site=self.site)
        cart4.add_item(p1, 2)
        ship4 = singpost(cart=cart4, service_type=('SURFACE',''), contact=self.contact_th)
        self.assertTrue(cart4.is_shippable)
        self.assertEqual(ship4._weight(), Decimal('84'))
        self.assertEqual(ship4.cost(), Decimal('1.00'))

        ship4_r = singpost(cart=cart4, service_type=('SURFACE_REGISTERED',''), contact=self.contact_th)
        self.assertEqual(ship4_r._weight(), Decimal('84'))
        self.assertEqual(ship4_r.cost(), Decimal('3.20'))

    def test_country_filter(self):
        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(self.product_dress, 1)

        ship1 = singpost(cart=cart1, service_type=('SURFACE',''), contact=self.contact_my)
        self.assertEqual(ship1.cost(), None)
        self.assertEqual(ship1.valid(), False)

        ship2 = singpost(cart=cart1, service_type=('SURFACE',''), contact=self.contact_bn)
        self.assertEqual(ship2.cost(), None)
        self.assertEqual(ship2.valid(), False)

        ship3 = singpost(cart=cart1, service_type=('SURFACE',''), contact=self.contact_th)
        self.assertEqual(ship3.cost(), Decimal('0.70'))
        self.assertEqual(ship3.valid(), True)

class AirTestCase(BaseTestCase):
    def test_zoning(self):
        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(self.product_dress, 1)

        ship1 = singpost(cart=cart1, service_type=('AIR',''), contact=self.contact_sg)
        self.assertEqual(ship1.cost(), None)
        self.assertEqual(ship1.valid(), False)

    def test_zone1(self):
        p1 = self.product_dress

        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(p1, 1)
        ship1 = singpost(cart=cart1, service_type=('AIR',''), contact=self.contact_my)
        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('42'))
        self.assertEqual(ship1.cost(), Decimal('0.55'))

        cart2 = Cart.objects.create(site=self.site)
        cart2.add_item(self.product_blouse, 1)
        ship2 = singpost(cart=cart2, service_type=('AIR',''), contact=self.contact_bn)
        self.assertTrue(cart2.is_shippable)
        self.assertEqual(ship2._weight(), Decimal('315'))
        self.assertEqual(ship2.cost(), Decimal('3.85'))

    def test_zone2(self):
        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(self.product_dress, 1)
        ship1 = singpost(cart=cart1, service_type=('AIR',''), contact=self.contact_as)
        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('42'))
        self.assertEqual(ship1.cost(), Decimal('1.40'))

    def test_zone3(self):
        cart1 = Cart.objects.create(site=self.site)
        cart1.add_item(self.product_dress, 1)
        ship1 = singpost(cart=cart1, service_type=('AIR',''), contact=self.contact_au)
        self.assertTrue(cart1.is_shippable)
        self.assertEqual(ship1._weight(), Decimal('42'))
        self.assertEqual(ship1.cost(), Decimal('2.15'))

        cart2 = Cart.objects.create(site=self.site)
        cart2.add_item(self.product_dress, 1)
        ship2 = singpost(cart=cart2, service_type=('AIR',''), contact=self.contact_jo)
        self.assertTrue(cart2.is_shippable)
        self.assertEqual(ship2._weight(), Decimal('42'))
        self.assertEqual(ship2.cost(), Decimal('2.15'))
