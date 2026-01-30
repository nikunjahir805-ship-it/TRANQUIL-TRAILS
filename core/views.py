from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from django.contrib import messages
import json

# IMPORT YOUR MODELS
from .models import Product, Customer, Category

# --- MAIN SITE VIEWS ---

def home(request): 
    return render(request, 'index.html')

def shop(request): 
    products = Product.objects.all()
    return render(request, 'shop.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})

def offers(request): return render(request, 'offers.html')
def gallery(request): return render(request, 'gallery.html')
def about(request): return render(request, 'about.html')
def contact(request): return render(request, 'contact.html')
def login_page(request): return render(request, 'login.html')

# --- ADMIN VIEWS ---
def admin_dashboard(request): return render(request, 'admin/dashboard.html')
def admin_analytics(request): return render(request, 'admin/analytics.html')

def admin_products(request): 
    products = Product.objects.all().order_by('-id')
    return render(request, 'admin/products.html', {'products': products})

# UPDATED: Add Product Logic
def admin_add_product(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        image = request.FILES.get('image') # Get the uploaded image

        if not name or not price:
            messages.error(request, "Name and Price are required!")
            return redirect('admin_add_product')

        try:
            category_obj = Category.objects.get(id=category_id) if category_id else None
            
            Product.objects.create(
                name=name,
                slug=slugify(name),
                price=price,
                description=description,
                category=category_obj,
                image=image
            )
            messages.success(request, "Product added successfully!")
            return redirect('admin_products')
            
        except Exception as e:
            messages.error(request, f"Error saving product: {e}")

    return render(request, 'admin/add_product.html', {'categories': categories})

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

# --- AUTHENTICATION APIS ---

@csrf_exempt 
def signup_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            full_name = data.get('full_name')
            email = data.get('email')
            password = data.get('password')

            if User.objects.filter(email=email).exists():
                return JsonResponse({'success': False, 'error': 'Email already exists!'})
            
            user = User.objects.create_user(username=email, email=email, password=password)
            user.first_name = full_name
            user.save()
            
            Customer.objects.create(user=user, full_name=full_name, email=email)

            login(request, user)
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
            
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@csrf_exempt
def login_api(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            email = data.get('email')
            password = data.get('password')

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
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    return JsonResponse({'success': False, 'error': 'Invalid method'})

def logout_api(request):
    logout(request)
    return JsonResponse({'success': True})