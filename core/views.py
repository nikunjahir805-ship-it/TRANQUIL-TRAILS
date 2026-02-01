from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from django.contrib import messages
from django.db.models import Count
import json

# IMPORT YOUR MODELS
from .models import Product, Customer, Category, GalleryItem

# --- MAIN SITE VIEWS ---

def home(request): 
    return render(request, 'index.html')

def shop(request): 
    products = Product.objects.all()
    return render(request, 'shop.html', {'products': products})

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_detail.html', {'product': product})

def gallery(request): 
    items = GalleryItem.objects.all().order_by('-created_at')
    return render(request, 'gallery.html', {'items': items})

def gallery_detail(request, pk):
    item = get_object_or_404(GalleryItem, pk=pk)
    return render(request, 'gallery_detail.html', {'item': item})

def offers(request): return render(request, 'offers.html')
def about(request): return render(request, 'about.html')
def contact(request): return render(request, 'contact.html')

# --- AUTHENTICATION PAGES ---
def login_page(request): return render(request, 'login.html')
def signup_page(request): return render(request, 'signup.html')

# --- ADMIN DASHBOARD ---
def admin_dashboard(request): return render(request, 'admin/dashboard.html')
def admin_analytics(request): return render(request, 'admin/analytics.html')

# --- PRODUCT MANAGEMENT ---

def admin_products(request): 
    products = Product.objects.all().order_by('-id')
    return render(request, 'admin/products.html', {'products': products})

def admin_add_product(request):
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name')
        price = request.POST.get('price')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        image = request.FILES.get('image')

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
                image=image,
                stock=0 # Default stock
            )
            messages.success(request, "Product added successfully!")
            return redirect('admin_products')
            
        except Exception as e:
            messages.error(request, f"Error saving product: {e}")

    return render(request, 'admin/add_product.html', {'categories': categories})

def admin_delete_product(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        product.delete()
        messages.success(request, "Product deleted successfully.")
    return redirect('admin_products')

# --- CATEGORY MANAGEMENT ---

def admin_categories(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')

        if name:
            if not Category.objects.filter(name=name).exists():
                Category.objects.create(
                    name=name,
                    slug=slugify(name),
                    image=image
                )
                messages.success(request, f"Collection '{name}' created!")
            else:
                messages.error(request, "This category already exists.")
        return redirect('admin_categories')

    categories = Category.objects.annotate(product_count=Count('products')).order_by('-id')
    return render(request, 'admin/categories.html', {'categories': categories})

def admin_delete_category(request, pk):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=pk)
        category.delete()
        messages.success(request, "Category deleted successfully.")
    return redirect('admin_categories')

# --- INVENTORY MANAGEMENT ---

def admin_inventory(request):
    products = Product.objects.all().order_by('name')
    return render(request, 'admin/inventory.html', {'products': products})

def admin_update_stock(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        new_stock = request.POST.get('stock')
        if new_stock:
            product.stock = int(new_stock)
            product.save()
            messages.success(request, f"Stock updated for {product.name}")
    return redirect('admin_inventory')

# --- MEDIA GALLERY MANAGEMENT ---

def admin_media(request): 
    # 1. Fetch Categories for the Dropdown
    categories = Category.objects.all()

    # 2. Handle Upload
    if request.method == "POST":
        image = request.FILES.get('image')
        category_name = request.POST.get('category') # Getting the name directly
        title = request.POST.get('title', '')

        if image:
            GalleryItem.objects.create(image=image, category=category_name, title=title)
            messages.success(request, "Image uploaded to gallery!")
            return redirect('admin_media')
        else:
            messages.error(request, "Please select an image.")

    # 3. Fetch Items
    gallery_items = GalleryItem.objects.all().order_by('-created_at')
    
    return render(request, 'admin/media.html', {
        'gallery_items': gallery_items,
        'categories': categories # <-- Sending categories to HTML
    })

def admin_delete_gallery_item(request, pk):
    if request.method == 'POST':
        item = get_object_or_404(GalleryItem, pk=pk)
        item.delete()
        messages.success(request, "Image deleted successfully.")
    return redirect('admin_media')


# --- PLACEHOLDER VIEWS ---
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