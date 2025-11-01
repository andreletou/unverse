from django.test import TestCase
from .models import User, Payment,Cart, Product, CartItem, PaymentAttempt
class PaygateTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('testuser', 'test@example.com', 'password')
        self.product = Product.objects.create(name="Test Product", price=100)
        self.cart = Cart.objects.create(user=self.user)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1, price=100)
        
    @patch('requests.post')
    def test_initiate_payment(self, mock_post):
        mock_post.return_value.json.return_value = {
            'status': 0,
            'tx_reference': 'TEST123'
        }
        
        success, result = PaymentAttempt.initiate_payment(...)
        self.assertTrue(success)
        self.assertIsInstance(result, Payment)