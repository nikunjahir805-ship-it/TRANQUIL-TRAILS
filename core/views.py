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

# ------------------ HELPER FUNCTIONS ------------------

def admin_only(user):
    return user.is_authenticated and user.is_staff

def generate_unique_slug(model, name, slug_field='slug', instance_id=None):
    """
    Generate a unique slug by appending numbers if slug already exists.
    
    Args:
        model: Django model class
        name: String to generate slug from
        slug_field: Name of the slug field (default: 'slug')
        instance_id: ID of current instance (for updates, to exclude self)
    
    Returns:
        Unique slug string
    """
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    
    while True:
        # Build query to check if slug exists
        query = {slug_field: slug}
        queryset = model.objects.filter(**query)
        
        # Exclude current instance if updating
        if instance_id:
            queryset = queryset.exclude(id=instance_id)
        
        # If slug doesn't exist, we can use it
        if not queryset.exists():
            return slug
        
        # Otherwise, try next number
        slug = f"{base_slug}-{counter}"
        counter += 1

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
    products = Product.objects.filter(available=True)
    categories = Category.objects.all()
    
    return render(request, 'shop.html', {
        'products': products,
        'categories': categories
    })

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
    # Calculate analytics data
    total_revenue = OrderItem.objects.filter(
        order__complete=True
    ).aggregate(total=Sum(F('quantity') * F('product__price')))['total'] or 0
    
    total_visits = 15420  # Mock data - integrate with analytics service
    conversion_rate = 3.2  # Mock data
    avg_order_value = 2450  # Mock data
    
    # Top products by revenue
    top_products = OrderItem.objects.filter(
        order__complete=True
    ).values(
        'product__name', 'product__image'
    ).annotate(
        sales_count=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('product__price'))
    ).order_by('-total_revenue')[:10]
    
    # Calculate percentage for progress bars
    if top_products:
        max_revenue = top_products[0]['total_revenue']
        for product in top_products:
            product['percentage'] = f"{(product['total_revenue'] / max_revenue * 100):.0f}%"
    
    # Sales data by month (last 12 months)
    sales_by_month = OrderItem.objects.filter(
        order__complete=True,
        order__date_ordered__gte=timezone.now() - timedelta(days=365)
    ).annotate(
        month=TruncMonth('order__date_ordered')
    ).values('month').annotate(
        revenue=Sum(F('quantity') * F('product__price'))
    ).order_by('month')
    
    sales_labels = [item['month'].strftime('%b') for item in sales_by_month]
    sales_data = [float(item['revenue']) for item in sales_by_month]
    
    return render(request, 'admin/analytics.html', {
        'total_revenue': total_revenue,
        'total_visits': total_visits,
        'conversion_rate': conversion_rate,
        'avg_order_value': avg_order_value,
        'top_products': top_products,
        'sales_data_json': json.dumps(sales_data),
        'sales_labels_json': json.dumps(sales_labels),
    })

# ------------------ ADMIN PRODUCTS ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_products(request):
    products = Product.objects.all().select_related('category')
    
    return render(request, 'admin/products.html', {
        'products': products
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        description = request.POST.get('description')
        image = request.FILES.get('image')
        
        category = get_object_or_404(Category, id=category_id)
        
        Product.objects.create(
            name=name,
            slug=generate_unique_slug(Product, name),
            category=category,
            price=price,
            description=description,
            image=image,
            stock=0,
            available=True
        )
        
        messages.success(request, f"Product '{name}' added successfully!")
        return redirect('admin_products')
    
    categories = Category.objects.all()
    return render(request, 'admin/add_product.html', {
        'categories': categories
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_delete_product(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        product_name = product.name
        product.delete()
        messages.success(request, f"Product '{product_name}' deleted successfully.")
    return redirect('admin_products')

# ------------------ ADMIN CATEGORIES ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_categories(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        image = request.FILES.get('image')
        
        Category.objects.create(
            name=name,
            slug=generate_unique_slug(Category, name),
            image=image
        )
        
        messages.success(request, f"Category '{name}' created successfully!")
        return redirect('admin_categories')
    
    categories = Category.objects.annotate(
        product_count=Count('products')
    )
    
    return render(request, 'admin/categories.html', {
        'categories': categories
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_delete_category(request, pk):
    if request.method == 'POST':
        category = get_object_or_404(Category, pk=pk)
        category_name = category.name
        category.delete()
        messages.success(request, f"Category '{category_name}' deleted successfully.")
    return redirect('admin_categories')

# ------------------ ADMIN INVENTORY ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_inventory(request):
    products = Product.objects.all().select_related('category')
    
    return render(request, 'admin/inventory.html', {
        'products': products
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_update_stock(request, pk):
    if request.method == 'POST':
        product = get_object_or_404(Product, pk=pk)
        new_stock = request.POST.get('stock', 0)
        
        product.stock = int(new_stock)
        product.save()
        
        messages.success(request, f"Stock updated for '{product.name}'")
    
    return redirect('admin_inventory')

# ------------------ ADMIN MEDIA / GALLERY ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_media(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        category = request.POST.get('category', 'Other')
        price = request.POST.get('price', 0)
        image = request.FILES.get('image')
        
        GalleryItem.objects.create(
            title=title,
            category=category,
            price=price,
            image=image
        )
        
        messages.success(request, f"Gallery item '{title}' added successfully!")
        return redirect('admin_media')
    
    gallery_items = GalleryItem.objects.all().order_by('-created_at')
    categories = Category.objects.all()
    
    return render(request, 'admin/media.html', {
        'gallery_items': gallery_items,
        'categories': categories
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_delete_gallery_item(request, pk):
    if request.method == 'POST':
        item = get_object_or_404(GalleryItem, pk=pk)
        item.delete()
        messages.success(request, "Gallery item deleted successfully.")
    return redirect('admin_media')

# ------------------ ADMIN MUSEUM MANAGER ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_museum_manager(request):
    if request.method == "POST":
        action = request.POST.get('action')
        item_id = request.POST.get('item_id')
        item_type = request.POST.get('item_type')
        
        # DELETE ACTION
        if action == "delete":
            if item_type == "collections":
                get_object_or_404(Category, id=item_id).delete()
            elif item_type == "gallery":
                get_object_or_404(GalleryItem, id=item_id).delete()
            elif item_type == "woodwork":
                get_object_or_404(Product, id=item_id).delete()
            messages.success(request, "Item removed from Museum.")
            return redirect('museum_manager')
        
        # SAVE ACTION (Add/Edit)
        elif action == "save":
            name = request.POST.get('name')
            price = request.POST.get('price', 0)
            image = request.FILES.get('image')
            
            if item_type == "collections":
                if item_id:  # Edit
                    obj = get_object_or_404(Category, id=item_id)
                    obj.name = name
                    obj.slug = generate_unique_slug(Category, name, instance_id=item_id)
                    if image:
                        obj.image = image
                    obj.save()
                else:  # Add New
                    Category.objects.create(
                        name=name,
                        slug=generate_unique_slug(Category, name),
                        image=image
                    )
            
            elif item_type == "gallery":
                if item_id:  # Edit
                    obj = get_object_or_404(GalleryItem, id=item_id)
                    obj.title = name
                    obj.price = price
                    if image:
                        obj.image = image
                    obj.save()
                else:  # Add New
                    GalleryItem.objects.create(
                        title=name,
                        price=price,
                        image=image
                    )
            
            elif item_type == "woodwork":
                # Get or create Wood category
                wood_category, _ = Category.objects.get_or_create(
                    name='Wood',
                    defaults={'slug': 'wood'}
                )
                
                if item_id:  # Edit
                    obj = get_object_or_404(Product, id=item_id)
                    obj.name = name
                    obj.slug = generate_unique_slug(Product, name, instance_id=item_id)
                    obj.price = price
                    if image:
                        obj.image = image
                    obj.save()
                else:  # Add New
                    Product.objects.create(
                        name=name,
                        slug=generate_unique_slug(Product, name),
                        price=price,
                        image=image,
                        category=wood_category,
                        stock=0,
                        available=True
                    )
            
            messages.success(request, "Museum updated successfully!")
            return redirect('museum_manager')
    
    # GET REQUEST - Display Museum Manager
    context = {
        'gallery_items': GalleryItem.objects.all().order_by('-created_at'),
        'categories': Category.objects.all(),
        'wood_products': Product.objects.filter(category__name='Wood')
    }
    return render(request, 'admin/museum_manager.html', context)

# ------------------ ADMIN REVIEWS ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_reviews(request):
    if request.method == 'POST':
        customer_id = request.POST.get('customer')
        product_id = request.POST.get('product')
        rating = request.POST.get('rating', 5)
        comment = request.POST.get('comment')
        
        customer = get_object_or_404(Customer, id=customer_id)
        product = get_object_or_404(Product, id=product_id)
        
        Review.objects.create(
            customer=customer,
            product=product,
            rating=rating,
            comment=comment
        )
        
        messages.success(request, "Review posted successfully!")
        return redirect('admin_reviews')
    
    reviews = Review.objects.all().select_related('customer', 'product').order_by('-created_at')
    customers = Customer.objects.all()
    products = Product.objects.all()
    
    return render(request, 'admin/reviews.html', {
        'reviews': reviews,
        'customers': customers,
        'products': products
    })

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
def admin_toggle_heart(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.is_liked = not review.is_liked
    review.save()
    return redirect('admin_reviews')

# ------------------ ADMIN DISCOUNTS ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_discounts(request):
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        discount_text = request.POST.get('discount_text')
        code = request.POST.get('code')
        category = request.POST.get('category', 'Merchandise')
        
        Offer.objects.create(
            title=title,
            description=description,
            discount_text=discount_text,
            code=code,
            category=category,
            active=True
        )
        
        messages.success(request, f"Discount '{title}' created successfully!")
        return redirect('admin_discounts')
    
    discounts = Offer.objects.all().order_by('-created_at')
    
    return render(request, 'admin/discounts.html', {
        'discounts': discounts
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_delete_discount(request, pk):
    if request.method == 'POST':
        offer = get_object_or_404(Offer, pk=pk)
        offer.delete()
        messages.success(request, "Discount deleted successfully.")
    return redirect('admin_discounts')

# ------------------ ADMIN CAMPAIGNS ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_campaigns(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        content = request.POST.get('content')
        action = request.POST.get('action', 'draft')
        
        if action == 'send':
            Campaign.objects.create(
                subject=subject,
                content=content,
                status='Sent',
                sent_date=timezone.now()
            )
            messages.success(request, f"Campaign '{subject}' sent successfully!")
        else:
            Campaign.objects.create(
                subject=subject,
                content=content,
                status='Draft'
            )
            messages.success(request, f"Campaign '{subject}' saved as draft.")
        
        return redirect('admin_campaigns')
    
    campaigns = Campaign.objects.all().order_by('-created_at')
    subscriber_count = Customer.objects.count()
    sent_count = Campaign.objects.filter(status='Sent').count()
    
    return render(request, 'admin/campaigns.html', {
        'campaigns': campaigns,
        'subscriber_count': subscriber_count,
        'sent_count': sent_count
    })

# ------------------ STUB ADMIN VIEWS ------------------

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_orders(request):
    orders = Order.objects.filter(complete=True).order_by('-date_ordered')
    return render(request, 'admin/orders.html', {'orders': orders})

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_customers(request):
    customers = Customer.objects.all()
    return render(request, 'admin/customers.html', {'customers': customers})

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_settings(request):
    settings_obj, _ = SiteSetting.objects.get_or_create(id=1)
    
    if request.method == 'POST':
        settings_obj.store_name = request.POST.get('store_name', settings_obj.store_name)
        settings_obj.admin_email = request.POST.get('admin_email', settings_obj.admin_email)
        settings_obj.contact_phone = request.POST.get('contact_phone', settings_obj.contact_phone)
        settings_obj.save()
        
        messages.success(request, "Settings updated successfully!")
        return redirect('admin_settings')
    
    return render(request, 'admin/settings.html', {'settings': settings_obj})

def admin_invoices(request): 
    return render(request, 'admin/invoices.html')

def admin_shipments(request): 
    return render(request, 'admin/shipments.html')

def admin_returns(request): 
    return render(request, 'admin/returns.html')

def admin_segments(request): 
    return render(request, 'admin/segments.html')

def admin_staff(request): 
    return render(request, 'admin/staff.html')

def admin_blog(request): 
    return render(request, 'admin/blog.html')

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