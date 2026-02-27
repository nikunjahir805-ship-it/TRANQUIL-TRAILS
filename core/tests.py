from django.test import TestCase, Client
from .models import Product, Category, Customer, Review


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

    def test_submit_message_only(self):
        response = self.client.post('/contact/submit/', {
            'name': 'Bob',
            'email': 'bob@example.com',
            'message': 'Hello there',
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertFalse(Review.objects.exists())

    def test_invalid_email(self):
        response = self.client.post('/contact/submit/', {
            'name': 'Foo',
            'email': 'invalid',
            'message': 'Test',
        })
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json().get('success'))

    def test_review_submit_endpoint(self):
        response = self.client.post('/contact/review/submit/', {
            'name': 'Alice',
            'email': 'alice@example.com',
            'product': str(self.product.id),
            'rating': '4',
            'comment': 'Great product!',
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get('success'))
        self.assertTrue(Review.objects.filter(comment='Great product!').exists())
