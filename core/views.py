import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncMonth
from django.conf import settings
import razorpay

from .models import (
    Product, Customer, Category, GalleryItem, Order, OrderItem,
    Offer, Review, Campaign, SiteSetting
)

# ------------------ HELPERS ------------------

def admin_only(user):
    return user.is_authenticated and user.is_staff

# ------------------ PUBLIC PAGES ------------------

def home(request):
    gallery_slider = GalleryItem.objects.all().order_by('-created_at')[:7]
    wood_products = Product.objects.filter(category__name='Wood')[:5]
    categories = Category.objects.all()[:4]

    return render(request, 'index.html', {
        'gallery_slider': gallery_slider,
        'wood_products': wood_products,
        'categories': categories
    })

def shop(request):
    return render(request, 'shop.html', {'products': Product.objects.all()})

def product_detail(request, pk):
    return render(request, 'product_detail.html', {
        'product': get_object_or_404(Product, pk=pk)
    })

def gallery(request):
    return render(request, 'gallery.html', {
        'items': GalleryItem.objects.all().order_by('-created_at')
    })

def gallery_detail(request, pk):
    return render(request, 'gallery_detail.html', {
        'item': get_object_or_404(GalleryItem, pk=pk)
    })

def offers(request):
    offers_queryset = Offer.objects.filter(active=True)
    
    offers_data = []
    for o in offers_queryset:
        offers_data.append({
            'id': o.id,
            'title': o.title,
            'description': o.description,
            'discount_text': o.discount_text,
            'code': o.code,
            'category': o.category,
            'color': o.color,
            'icon_class': o.icon_class
        })
    
    return render(request, 'offers.html', {'offers_data': offers_data})

def about(request): 
    return render(request, 'about.html')

def contact(request): 
    return render(request, 'contact.html')

# ------------------ AUTH ------------------

def login_page(request): 
    return render(request, 'login.html')

def signup_page(request): 
    return render(request, 'signup.html')

@csrf_exempt
def signup_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({'success': False})
        user = User.objects.create_user(
            username=data['email'],
            email=data['email'],
            password=data['password']
        )
        Customer.objects.create(user=user, full_name=data['full_name'], email=data['email'])
        login(request, user)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False})

@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        try:
            user_obj = User.objects.get(email=data['email'])
            user = authenticate(request, username=user_obj.username, password=data['password'])
            if user:
                login(request, user)
                return JsonResponse({'success': True, 'is_staff': user.is_staff})
        except User.DoesNotExist:
            pass
    return JsonResponse({'success': False})

def logout_api(request):
    logout(request)
    return JsonResponse({'success': True})

# ------------------ ADMIN DASHBOARD ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_dashboard(request):
    total_orders = Order.objects.filter(complete=True).count()
    pending_count = Order.objects.filter(status='Pending').count()
    total_revenue = OrderItem.objects.filter(
        order__complete=True
    ).aggregate(total=Sum(F('quantity') * F('product__price')))['total'] or 0

    recent_orders = Order.objects.filter(complete=True).order_by('-date_ordered')[:5]

    return render(request, 'admin/dashboard.html', {
        'total_orders': total_orders,
        'pending_count': pending_count,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_analytics(request):
    return render(request, 'admin/analytics.html')

# ------------------ ADMIN PAGES ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_products(request):
    return render(request, 'admin/products.html', {
        'products': Product.objects.all()
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_add_product(request):
    return render(request, 'admin/add_product.html')

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_categories(request):
    return render(request, 'admin/categories.html', {
        'categories': Category.objects.all()
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_inventory(request):
    return render(request, 'admin/inventory.html', {
        'products': Product.objects.all()
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_media(request):
    return render(request, 'admin/media.html', {
        'gallery_items': GalleryItem.objects.all()
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_settings(request):
    settings_obj, _ = SiteSetting.objects.get_or_create(id=1)
    return render(request, 'admin/settings.html', {'settings': settings_obj})

# ------------------ ADMIN DELETE ACTIONS ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_delete_product(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        messages.success(request, "Product deleted successfully.")
    return redirect('admin_products')

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_delete_category(request, pk):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=pk)
        category.delete()
        messages.success(request, "Category deleted successfully.")
    return redirect('admin_categories')

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_delete_gallery_item(request, pk):
    if request.method == 'POST':
        item = get_object_or_404(GalleryItem, pk=pk)
        item.delete()
        messages.success(request, "Gallery item deleted successfully.")
    return redirect('admin_media')

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_delete_review(request, pk):
    if request.method == 'POST':
        review = get_object_or_404(Review, pk=pk)
        review.delete()
        messages.success(request, "Review deleted successfully.")
    return redirect('admin_reviews')

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_delete_discount(request, pk):
    if request.method == 'POST':
        offer = get_object_or_404(Offer, pk=pk)
        offer.delete()
        messages.success(request, "Discount deleted successfully.")
    return redirect('admin_discounts')

# ------------------ STUB ADMIN VIEWS ------------------

def admin_orders(request): 
    return render(request, 'admin/orders.html')

def admin_invoices(request): 
    return render(request, 'admin/invoices.html')

def admin_shipments(request): 
    return render(request, 'admin/shipments.html')

def admin_returns(request): 
    return render(request, 'admin/returns.html')

def admin_customers(request): 
    return render(request, 'admin/customers.html')

def admin_segments(request): 
    return render(request, 'admin/segments.html')

def admin_staff(request): 
    return render(request, 'admin/staff.html')

def admin_blog(request): 
    return render(request, 'admin/blog.html')

def admin_campaigns(request): 
    return render(request, 'admin/campaigns.html')

def admin_discounts(request): 
    return render(request, 'admin/discounts.html')

def admin_reviews(request): 
    return render(request, 'admin/reviews.html')

def admin_museum_manager(request):
    return render(request, 'admin/museum_manager.html')

def admin_toggle_heart(request, pk):
    return redirect('admin_reviews')

def admin_update_stock(request, pk):
    return redirect('admin_inventory')

# ------------------ CART & PAYMENT ------------------

def cart_page(request):
    return render(request, 'cart.html')

client = razorpay.Client(
    auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET)
)

@login_required
def checkout(request):
    return render(request, 'checkout.html')

def payment_success(request):
    return render(request, 'success.html')

def verify_payment(request):
    return JsonResponse({'status': 'success'})