from django.shortcuts import render

# --- MAIN SITE VIEWS ---
def home(request): return render(request, 'index.html')
def shop(request): return render(request, 'shop.html')
def offers(request): return render(request, 'offers.html')
def gallery(request): return render(request, 'gallery.html')
def about(request): return render(request, 'about.html')
def contact(request): return render(request, 'contact.html')
def login_page(request): return render(request, 'login.html')

# --- ADMIN VIEWS ---
def admin_dashboard(request): return render(request, 'admin/dashboard.html')
def admin_analytics(request): return render(request, 'admin/analytics.html')
def admin_products(request): return render(request, 'admin/products.html')
def admin_add_product(request): return render(request, 'admin/add_product.html')

# New Views (Create these files in the next step)
def admin_categories(request): return render(request, 'admin/categories.html')
def admin_inventory(request): return render(request, 'admin/inventory.html')
def admin_reviews(request): return render(request, 'admin/reviews.html')
def admin_orders(request): return render(request, 'admin/orders.html')
def admin_invoices(request): return render(request, 'admin/invoices.html')
def admin_shipments(request): return render(request, 'admin/shipments.html')
def admin_returns(request): return render(request, 'admin/returns.html')
def admin_customers(request): return render(request, 'admin/customers.html')
def admin_segments(request): return render(request, 'admin/segments.html')
def admin_staff(request): return render(request, 'admin/staff.html')
def admin_discounts(request): return render(request, 'admin/discounts.html')
def admin_campaigns(request): return render(request, 'admin/campaigns.html')
def admin_blog(request): return render(request, 'admin/blog.html')
def admin_media(request): return render(request, 'admin/media.html')
def admin_settings(request): return render(request, 'admin/settings.html')

import json
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

# --- AUTHENTICATION APIS ---

def signup_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        full_name = data.get('full_name')
        email = data.get('email')
        password = data.get('password')

        # Check if email already exists
        if User.objects.filter(email=email).exists():
            return JsonResponse({'success': False, 'error': 'Email already exists!'})
        
        # Create User
        # We use email as username for simplicity, or generate one
        user = User.objects.create_user(username=email, email=email, password=password)
        user.first_name = full_name
        user.save()
        
        # Create Customer Profile (linked to your models.py)
        from .models import Customer
        Customer.objects.create(user=user, full_name=full_name, email=email)

        login(request, user) # Auto login after signup
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

def login_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')

        # Django auth expects username, so we look up the user by email first
        try:
            user_obj = User.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except User.DoesNotExist:
            user = None

        if user is not None:
            login(request, user)
            return JsonResponse({'success': True, 'is_staff': user.is_staff})
        else:
            return JsonResponse({'success': False, 'error': 'Invalid email or password'})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

def logout_api(request):
    logout(request)
    return JsonResponse({'success': True})