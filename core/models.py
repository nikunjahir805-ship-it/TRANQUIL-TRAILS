from django.db import models
from django.contrib.auth.models import User

# --- 1. CATEGORY MODEL ---
class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Categories"

# --- 2. PRODUCT MODEL ---
class Product(models.Model):
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    image = models.ImageField(upload_to='products/')
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

# --- 3. CUSTOMER MODEL (Extends User) ---
class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=200)
    email = models.EmailField(max_length=200)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', default='profiles/default.png', blank=True)

    def __str__(self):
        return self.full_name

# --- 4. ORDER MODEL ---
class Order(models.Model):
    STATUS_CHOICES = (
        ('Pending', 'Pending'),
        ('Processing', 'Processing'),
        ('Shipped', 'Shipped'),
        ('Delivered', 'Delivered'),
        ('Cancelled', 'Cancelled'),
    )

    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True, blank=True)
    date_ordered = models.DateTimeField(auto_now_add=True)
    complete = models.BooleanField(default=False)
    transaction_id = models.CharField(max_length=100, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')

    def __str__(self):
        return str(self.id)

    @property
    def get_cart_total(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.get_total for item in orderitems])
        return total

    @property
    def get_cart_items(self):
        orderitems = self.orderitem_set.all()
        total = sum([item.quantity for item in orderitems])
        return total

# --- 5. ORDER ITEM MODEL ---
class OrderItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField(default=0, null=True, blank=True)
    date_added = models.DateTimeField(auto_now_add=True)

    @property
    def get_total(self):
        total = self.product.price * self.quantity
        return total

# --- 6. SHIPPING ADDRESS MODEL ---
class ShippingAddress(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.SET_NULL, null=True)
    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True)
    address = models.CharField(max_length=200, null=True)
    city = models.CharField(max_length=200, null=True)
    state = models.CharField(max_length=200, null=True)
    zipcode = models.CharField(max_length=200, null=True)
    date_added = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.address

# --- 7. GALLERY MODEL ---
class GalleryItem(models.Model):
    CATEGORY_CHOICES = [
        ('Ceramics', 'Ceramics'),
        ('Wood', 'Woodwork'),
        ('Textiles', 'Textiles'),
        ('Other', 'Other')
    ]
    
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='Other')
    image = models.ImageField(upload_to='gallery/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# --- 8. OFFER MODEL ---
class Offer(models.Model):
    CATEGORY_CHOICES = (
        ('Membership', 'Membership'),
        ('Training', 'Workshops'),
        ('Merchandise', 'Merchandise'),
    )
    
    title = models.CharField(max_length=100)
    description = models.TextField()
    discount_text = models.CharField(max_length=50, help_text="E.g. '25% OFF' or '₹500 OFF'")
    code = models.CharField(max_length=20)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    
    # Visuals for the card
    color = models.CharField(max_length=20, default="#8B5E3C", help_text="Hex Code (e.g. #8B5E3C)")
    icon_class = models.CharField(max_length=50, default="fa-gift", help_text="FontAwesome class (e.g. fa-gift)")
    
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

# --- 9. REVIEW MODEL ---
class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE)
    rating = models.IntegerField(default=5)
    comment = models.TextField()
    is_liked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.customer.full_name} - {self.product.name}"

# --- 10. CAMPAIGN MODEL ---
class Campaign(models.Model):
    STATUS_CHOICES = [
        ('Draft', 'Draft'),
        ('Sent', 'Sent'),
        ('Scheduled', 'Scheduled'),
    ]

    subject = models.CharField(max_length=200)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Draft')
    sent_date = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.subject

# --- 11. SITE SETTING MODEL ---
class SiteSetting(models.Model):
    store_name = models.CharField(max_length=100, default="Tranquil Trails")
    admin_email = models.EmailField(default="admin@tranquiltrails.com")
    contact_phone = models.CharField(max_length=20, default="+1 234 567 890")
    
    currency = models.CharField(max_length=10, default="USD")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=5.00)
    shipping_flat_rate = models.DecimalField(max_digits=6, decimal_places=2, default=15.00)
    
    maintenance_mode = models.BooleanField(default=False)

    def __str__(self):
        return "Site Configuration"