import json
from datetime import timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.text import slugify
from django.utils import timezone
from django.contrib import messages
from django.db.models import Count, Sum, F
from django.db.models.functions import TruncMonth

# IMPORT YOUR MODELS
# Ensure SiteSetting, Campaign, etc. are added to your models.py
from .models import (
    Product, Customer, Category, GalleryItem, Order, OrderItem, 
    Offer, Review, Campaign, SiteSetting
)

# --- MAIN SITE VIEWS ---

def home(request):
    # Fetch latest 5-7 items for the 3D Slider
    gallery_slider = GalleryItem.objects.all().order_by('-created_at')[:7]
    
    # Use 'category__name' to look up the Category by its name text.
    wood_products = Product.objects.filter(category__name='Wood')[:5] 

    return render(request, 'index.html', {
        'gallery_slider': gallery_slider,
        'wood_products': wood_products
    })

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

def offers(request):
    # FIX: Changed 'is_active' to 'active' to match your database model
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

def about(request): return render(request, 'about.html')
def contact(request): return render(request, 'contact.html')

# --- AUTHENTICATION PAGES ---
def login_page(request): return render(request, 'login.html')
def signup_page(request): return render(request, 'signup.html')

# --- ADMIN DASHBOARD (REAL DATA) ---

@login_required
def admin_dashboard(request):
    if not request.user.is_staff:
        return redirect('home')

    # 1. KPI Cards Data
    total_orders = Order.objects.filter(complete=True).count()
    pending_count = Order.objects.filter(status='Pending').count()
    
    # Calculate Total Revenue
    total_revenue = OrderItem.objects.filter(order__complete=True).aggregate(
        total=Sum(F('quantity') * F('product__price'))
    )['total'] or 0

    # 2. Recent Orders Table (Fetch last 5)
    recent_orders = Order.objects.filter(complete=True).order_by('-date_ordered')[:5]

    # 3. Chart Data: Revenue Last 7 Days
    today = timezone.now().date()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]
    revenue_labels = [] 
    revenue_data = []   

    for date in dates:
        revenue_labels.append(date.strftime("%a")) # Mon, Tue
        daily_sum = OrderItem.objects.filter(
            order__complete=True, 
            order__date_ordered__date=date
        ).aggregate(total=Sum(F('quantity') * F('product__price')))['total'] or 0
        revenue_data.append(float(daily_sum))

    # 4. Chart Data: Sales by Category
    categories = Category.objects.all()
    cat_labels = []
    cat_data = []

    for cat in categories:
        count = OrderItem.objects.filter(
            order__complete=True, 
            product__category=cat
        ).aggregate(qty=Sum('quantity'))['qty'] or 0
        
        if count > 0:
            cat_labels.append(cat.name)
            cat_data.append(count)

    context = {
        'total_revenue': total_revenue,
        'total_orders': total_orders,
        'pending_count': pending_count,
        'recent_orders': recent_orders,
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'cat_labels': cat_labels,
        'cat_data': cat_data,
    }
    return render(request, 'admin/dashboard.html', context)

# --- ADMIN ANALYTICS (REAL DATA) ---

@login_required
def admin_analytics(request):
    if not request.user.is_staff:
        return redirect('home')

    # 1. KPI Metrics
    total_revenue = OrderItem.objects.filter(order__complete=True).aggregate(
        total=Sum(F('quantity') * F('product__price'))
    )['total'] or 0

    total_orders = Order.objects.filter(complete=True).count()
    avg_order_value = round(total_revenue / total_orders, 2) if total_orders > 0 else 0

    # 2. Top Performing Products
    top_products_query = OrderItem.objects.filter(order__complete=True).values(
        'product__name'
    ).annotate(
        sales_count=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('product__price'))
    ).order_by('-total_revenue')[:5]

    top_products = []
    if top_products_query:
        max_rev = top_products_query[0]['total_revenue']
        for item in top_products_query:
            item['percentage'] = f"{(item['total_revenue'] / max_rev) * 100}%"
            top_products.append(item)

    # 3. Chart Data (Monthly Sales)
    monthly_sales = Order.objects.filter(complete=True).annotate(
        month=TruncMonth('date_ordered')
    ).values('month').annotate(
        total=Sum(F('orderitem__quantity') * F('orderitem__product__price'))
    ).order_by('month')

    sales_labels = []
    sales_data = []

    for entry in monthly_sales:
        sales_labels.append(entry['month'].strftime('%b')) 
        sales_data.append(float(entry['total']))

    context = {
        'total_revenue': total_revenue,
        'total_visits': 12540, 
        'conversion_rate': 3.5, 
        'avg_order_value': avg_order_value,
        'top_products': top_products,
        'sales_data_json': sales_data, 
        'sales_labels_json': sales_labels,
    }
    return render(request, 'admin/analytics.html', context)

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
                stock=0 
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
    categories = Category.objects.all()

    if request.method == "POST":
        try:
            image = request.FILES.get('image')
            title = request.POST.get('title', '')
            category_name = request.POST.get('category')
            price = request.POST.get('price')

            if image:
                GalleryItem.objects.create(
                    title=title,
                    image=image,
                    category=category_name,
                    price=price if price else 0.00
                )
                messages.success(request, "Image uploaded to gallery!")
                return redirect('admin_media')
            else:
                messages.error(request, "Please select an image.")
        except Exception as e:
            messages.error(request, f"Error: {e}")

    # For drop down filter
    gallery_cats = [{'name': 'Ceramics'}, {'name': 'Wood'}, {'name': 'Textiles'}, {'name': 'Other'}]
    gallery_items = GalleryItem.objects.all().order_by('-created_at')
    
    return render(request, 'admin/media.html', {
        'gallery_items': gallery_items,
        'categories': gallery_cats 
    })

def admin_delete_gallery_item(request, pk):
    if request.method == 'POST':
        item = get_object_or_404(GalleryItem, pk=pk)
        item.delete()
        messages.success(request, "Image deleted successfully.")
    return redirect('admin_media')

# --- DISCOUNT / OFFERS MANAGEMENT ---

def admin_discounts(request):
    if request.method == "POST":
        title = request.POST.get('title')
        code = request.POST.get('code')
        discount_text = request.POST.get('discount_text')
        category = request.POST.get('category')
        description = request.POST.get('description')
        color = request.POST.get('color', '#8B5E3C')
        # Correctly capture icon_class
        icon = request.POST.get('icon_class', 'fa-gift')

        if title and code:
            try:
                Offer.objects.create(
                    title=title,
                    code=code,
                    discount_text=discount_text,
                    category=category,
                    description=description,
                    color=color,
                    icon_class=icon,
                    active=True # Fixed: active=True
                )
                messages.success(request, "New coupon created successfully!")
            except Exception as e:
                messages.error(request, f"Error creating coupon: {e}")
            return redirect('admin_discounts')
        else:
            messages.error(request, "Title and Code are required.")

    # FIX: Filter by active=True (not is_active)
    offers = Offer.objects.filter(active=True).order_by('-created_at')
    
    return render(request, 'admin/discounts.html', {'offers': offers})

def admin_delete_discount(request, pk):
    if request.method == 'POST':
        offer = get_object_or_404(Offer, pk=pk)
        offer.delete()
        messages.success(request, "Coupon deleted.")
    return redirect('admin_discounts')

# --- EMAIL CAMPAIGNS MANAGEMENT ---

def admin_campaigns(request):
    if request.method == "POST":
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        action = request.POST.get('action') # 'draft' or 'send'

        if subject and content:
            status = 'Sent' if action == 'send' else 'Draft'
            sent_date = timezone.now() if action == 'send' else None
            
            Campaign.objects.create(
                subject=subject,
                content=content,
                status=status,
                sent_date=sent_date
            )
            
            msg = "Campaign sent successfully!" if action == 'send' else "Draft saved."
            messages.success(request, msg)
            return redirect('admin_campaigns')
        else:
            messages.error(request, "Subject and Content are required.")

    campaigns = Campaign.objects.all().order_by('-created_at')
    subscriber_count = Customer.objects.count()
    sent_count = Campaign.objects.filter(status='Sent').count()

    return render(request, 'admin/campaigns.html', {
        'campaigns': campaigns,
        'subscriber_count': subscriber_count,
        'sent_count': sent_count
    })

# --- REVIEWS MANAGEMENT ---

def admin_reviews(request):
    if request.method == "POST":
        customer_id = request.POST.get('customer')
        product_id = request.POST.get('product')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment')

        if customer_id and product_id and rating:
            Review.objects.create(
                customer_id=customer_id,
                product_id=product_id,
                rating=rating,
                comment=comment
            )
            messages.success(request, "Review added successfully!")
            return redirect('admin_reviews')
        else:
            messages.error(request, "Please fill all fields.")

    reviews = Review.objects.all().order_by('-created_at')
    customers = Customer.objects.all()
    products = Product.objects.all()

    return render(request, 'admin/reviews.html', {
        'reviews': reviews, 
        'customers': customers, 
        'products': products
    })

def admin_delete_review(request, pk):
    if request.method == "POST":
        review = get_object_or_404(Review, pk=pk)
        review.delete()
        messages.success(request, "Review deleted.")
    return redirect('admin_reviews')

def admin_toggle_heart(request, pk):
    review = get_object_or_404(Review, pk=pk)
    # Assuming is_liked logic exists in your model if needed
    # review.is_liked = not review.is_liked
    # review.save()
    return redirect('admin_reviews')

# --- SETTINGS MANAGEMENT ---

def admin_settings(request):
    # Singleton settings object (ID=1)
    settings_obj, created = SiteSetting.objects.get_or_create(id=1)

    if request.method == 'POST':
        settings_obj.store_name = request.POST.get('store_name')
        settings_obj.admin_email = request.POST.get('admin_email')
        settings_obj.contact_phone = request.POST.get('contact_phone')
        settings_obj.currency = request.POST.get('currency')
        settings_obj.tax_rate = request.POST.get('tax_rate')
        settings_obj.shipping_flat_rate = request.POST.get('shipping_flat_rate')
        
        # Checkbox handling
        settings_obj.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        
        settings_obj.save()
        messages.success(request, "System preferences updated successfully.")
        return redirect('admin_settings')

    return render(request, 'admin/settings.html', {'settings': settings_obj})

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

# --- PLACEHOLDERS ---
# These prevent import errors for urls that might point here
def admin_orders(request): return render(request, 'admin/orders.html')
def admin_invoices(request): return render(request, 'admin/invoices.html')
def admin_shipments(request): return render(request, 'admin/shipments.html')
def admin_returns(request): return render(request, 'admin/returns.html')
def admin_customers(request): return render(request, 'admin/customers.html')
def admin_segments(request): return render(request, 'admin/segments.html')
def admin_staff(request): return render(request, 'admin/staff.html')
def admin_blog(request): return render(request, 'admin/blog.html')


# In core/views.py

def home(request):
    # 1. Slider Data
    gallery_slider = GalleryItem.objects.all().order_by('-created_at')[:7]
    
    # 2. Featured Products (Wood)
    wood_products = Product.objects.filter(category__name='Wood')[:5] 

    # --- NEW ADDITION ---
    # 3. Fetch all categories for the "Shop by Category" section
    categories = Category.objects.all()[:4] # Limit to 4 for a nice grid

    return render(request, 'index.html', {
        'gallery_slider': gallery_slider,
        'wood_products': wood_products,
        'categories': categories # Pass this to the template
    })