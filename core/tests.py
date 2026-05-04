import json
from django.contrib.auth.models import User
from django.test import TestCase, Client
from django.urls import reverse
from .models import Product, Category, Customer, Review, Order


class ContactReviewTests(TestCase):
    def setUp(self):
        # create dummy category & product for review tests
        self.category = Category.objects.create(name='TestCat', slug='testcat')
        self.product = Product.objects.create(
            category=self.category,
            name='Test Product',
            slug='test-product',
            price=9.99,
            image='products/test.jpg',
            stock=10,
            available=True,
        )
        self.client = Client()
        self.client.defaults['wsgi.url_scheme'] = 'https'

    def test_submit_message_only(self):
        response = self.client.post('/contact/submit/', {
            'name': 'Bob',
            'email': 'bob@example.com',
            'message': 'Hello there',
        }, secure=True)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertFalse(Review.objects.exists())

    def test_invalid_email(self):
        response = self.client.post('/contact/submit/', {
            'name': 'Foo',
            'email': 'invalid',
            'message': 'Test',
        }, secure=True)
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json().get('success'))

    def test_review_submit_endpoint(self):
        response = self.client.post('/contact/review/submit/', {
            'name': 'Alice',
            'email': 'alice@example.com',
            'product': str(self.product.id),
            'rating': '4',
            'comment': 'Great product!',
        }, secure=True)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertTrue(Review.objects.filter(comment='Great product!').exists())

    def test_testimonials_page_loads(self):
        customer = Customer.objects.create(full_name='Test Customer', email='customer@example.com')
        Review.objects.create(
            customer=customer,
            product=self.product,
            rating=5,
            comment='Beautiful craftsmanship and a calm buying experience.',
        )

        response = self.client.get(reverse('testimonials'), secure=True)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Beautiful craftsmanship and a calm buying experience.')


class OrderWorkflowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.client.defaults['wsgi.url_scheme'] = 'https'
        self.category = Category.objects.create(name='Craft', slug='craft')
        self.product = Product.objects.create(
            category=self.category,
            name='Handmade Vase',
            slug='handmade-vase',
            price=1200,
            image='products/vase.jpg',
            stock=5,
            available=True,
        )
        self.user = User.objects.create_user(
            username='buyer@example.com',
            email='buyer@example.com',
            password='testpass123',
        )
        self.customer = Customer.objects.create(
            user=self.user,
            full_name='Buyer One',
            email='buyer@example.com',
            phone='9999999999',
            address='Old Address',
        )
        self.admin_user = User.objects.create_user(
            username='admin@example.com',
            email='admin@example.com',
            password='adminpass123',
            is_staff=True,
        )

    def test_cod_checkout_creates_pending_order(self):
        self.client.force_login(self.user)
        payload = {
            'items': [{'id': self.product.id, 'quantity': 2}],
            'payment_method': 'COD',
            'full_name': 'Buyer One',
            'email': 'buyer@example.com',
            'phone': '9999999999',
            'address': 'Craft Street',
            'city': 'Jaipur',
            'state': 'Rajasthan',
            'zipcode': '302001',
        }

        response = self.client.post(
            reverse('create_checkout_order'),
            data=json.dumps(payload),
            content_type='application/json',
            secure=True,
        )

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(customer=self.customer)
        self.assertEqual(order.status, 'Processing')
        self.assertTrue(order.complete)
        self.product.refresh_from_db()
        self.assertEqual(self.product.stock, 3)

    def test_admin_can_confirm_order_and_user_can_view_it(self):
        order = Order.objects.create(
            customer=self.customer,
            payment_method='COD',
            status='Pending',
            complete=False,
        )
        order.orderitem_set.create(product=self.product, quantity=2)

        self.client.force_login(self.admin_user)
        response = self.client.post(
            reverse('admin_update_order_status', args=[order.id]),
            {'status': 'Processing'},
            secure=True,
        )

        self.assertEqual(response.status_code, 302)
        order.refresh_from_db()
        self.product.refresh_from_db()
        self.assertTrue(order.complete)
        self.assertEqual(order.status, 'Processing')
        self.assertEqual(self.product.stock, 3)

        self.client.force_login(self.user)
        response = self.client.get(reverse('my_orders'), secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, f'Order #{order.id}')
        self.assertContains(response, 'Processing')


class AdminExportTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.client.defaults['wsgi.url_scheme'] = 'https'
        self.category = Category.objects.create(name='Decor', slug='decor')
        self.product = Product.objects.create(
            category=self.category,
            name='Lantern',
            slug='lantern',
            price=499.50,
            image='products/lantern.jpg',
            stock=4,
            available=True,
            description='Handcrafted brass lantern',
        )
        self.admin_user = User.objects.create_user(
            username='exports@example.com',
            email='exports@example.com',
            password='adminpass123',
            is_staff=True,
        )
        self.client.force_login(self.admin_user)

    def test_products_csv_export(self):
        response = self.client.get(reverse('admin_export_products_section'), {'format': 'csv'}, follow=True, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertIn('products_export.csv', response['Content-Disposition'])
        self.assertIn('Lantern', response.content.decode('utf-8'))

    def test_categories_word_export(self):
        response = self.client.get(reverse('admin_export_categories'), {'format': 'word'}, follow=True, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/msword')
        self.assertIn('categories_export.doc', response['Content-Disposition'])
        self.assertIn('Decor', response.content.decode('utf-8'))

    def test_inventory_pdf_export(self):
        response = self.client.get(reverse('admin_export_inventory'), {'format': 'pdf'}, follow=True, secure=True)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('inventory_export.pdf', response['Content-Disposition'])
        self.assertTrue(response.content.startswith(b'%PDF-1.4'))
