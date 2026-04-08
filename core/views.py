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
import csv

from .models import (
    Product, Customer, Category, GalleryItem, Order, OrderItem, ShippingAddress,
    Offer, Review, Campaign, SiteSetting
)

# ------------------ HELPER FUNCTIONS ------------------

def admin_only(user):
    return user.is_authenticated and user.is_staff

def generate_unique_slug(model, name, slug_field='slug', instance_id=None):
    base_slug = slugify(name)
    slug = base_slug
    counter = 1
    
    while True:
        query = {slug_field: slug}
        queryset = model.objects.filter(**query)
        
        if instance_id:
            queryset = queryset.exclude(id=instance_id)
        
        if not queryset.exists():
            return slug
        
        slug = f"{base_slug}-{counter}"
        counter += 1

# ------------------ PUBLIC PAGES ------------------

def home(request):
    gallery_slider = GalleryItem.objects.all().order_by('-created_at')[:7]
    wood_products = Product.objects.filter(category__name='Wood')[:5]
    categories = Category.objects.all()[:4]

    # load latest three reviews (could filter by is_liked or rating)
    reviews = Review.objects.all().select_related('customer').order_by('-created_at')[:3]

    return render(request, 'index.html', {
        'gallery_slider': gallery_slider,
        'wood_products': wood_products,
        'categories': categories,
        'reviews': reviews,
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
    # pass available products for review form
    products = Product.objects.filter(available=True)
    return render(request, 'contact.html', {'products': products})

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
    
    # Stock Statistics
    total_products = Product.objects.count()
    low_stock_count = Product.objects.filter(stock__gt=0, stock__lte=10).count()
    out_of_stock_count = Product.objects.filter(stock=0).count()
    total_stock = Product.objects.aggregate(total=Sum('stock'))['total'] or 0

    return render(request, 'admin/dashboard.html', {
        'total_orders': total_orders,
        'pending_count': pending_count,
        'total_revenue': total_revenue,
        'recent_orders': recent_orders,
        'total_products': total_products,
        'low_stock_count': low_stock_count,
        'out_of_stock_count': out_of_stock_count,
        'total_stock': total_stock,
    })

@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_analytics(request):
    total_revenue = OrderItem.objects.filter(
        order__complete=True
    ).aggregate(total=Sum(F('quantity') * F('product__price')))['total'] or 0
    
    total_visits = 15420
    conversion_rate = 3.2
    avg_order_value = 2450
    
    top_products = OrderItem.objects.filter(
        order__complete=True
    ).values(
        'product__name', 'product__image'
    ).annotate(
        sales_count=Sum('quantity'),
        total_revenue=Sum(F('quantity') * F('product__price'))
    ).order_by('-total_revenue')[:10]
    
    if top_products:
        max_revenue = top_products[0]['total_revenue']
        for product in top_products:
            product['percentage'] = f"{(product['total_revenue'] / max_revenue * 100):.0f}%"
    
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
@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_add_product(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        category_id = request.POST.get('category')
        price = request.POST.get('price')
        stock = request.POST.get('stock', 0)
        description = request.POST.get('description')
        image = request.FILES.get('image')
        
        category = get_object_or_404(Category, id=category_id)
        
        Product.objects.create(
            name=name,
            slug=generate_unique_slug(Product, name),
            category=category,
            price=price,
            stock=int(stock),
            description=description,
            image=image,
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
def admin_edit_product(request, pk):
    product = get_object_or_404(Product, pk=pk)
    
    if request.method == 'POST':
        product.name = request.POST.get('name')
        category_id = request.POST.get('category')
        product.category = get_object_or_404(Category, id=category_id)
        product.price = request.POST.get('price')
        product.description = request.POST.get('description')
        product.slug = generate_unique_slug(Product, product.name, instance_id=pk)
        
        new_image = request.FILES.get('image')
        if new_image:
            product.image = new_image
        
        product.save()
        messages.success(request, f"Product '{product.name}' updated successfully!")
        return redirect('admin_products')
    
    categories = Category.objects.all()
    return render(request, 'admin/edit_product.html', {
        'product': product,
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
def admin_edit_category(request, pk):
    category = get_object_or_404(Category, pk=pk)
    
    if request.method == 'POST':
        category.name = request.POST.get('name')
        category.slug = generate_unique_slug(Category, category.name, instance_id=pk)
        
        new_image = request.FILES.get('image')
        if new_image:
            category.image = new_image
        
        category.save()
        messages.success(request, f"Category '{category.name}' updated successfully!")
        return redirect('admin_categories')
    
    return render(request, 'admin/edit_category.html', {
        'category': category
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

# CSV Export / Import for Products
@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_export_products(request):
    """Export products as CSV (admin only)."""
    products = Product.objects.select_related('category').all()

    from django.http import HttpResponse

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="products_export.csv"'

    writer = csv.writer(response)
    writer.writerow(['id', 'name', 'slug', 'category', 'price', 'stock', 'available', 'description', 'image'])

    for p in products:
        writer.writerow([
            p.id,
            p.name,
            p.slug,
            p.category.name if p.category else '',
            float(p.price),
            p.stock,
            '1' if p.available else '0',
            p.description or '',
            p.image.url if p.image else ''
        ])

    return response


@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_import_products(request):
    """Import products from uploaded CSV. CSV headers: id,name,slug,category,price,stock,available,description"""
    if request.method == 'POST' and request.FILES.get('csv_file'):
        csvfile = request.FILES['csv_file']
        decoded = csvfile.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded)
        created = 0
        updated = 0

        for row in reader:
            # Basic field extraction
            pid = row.get('id') or row.get('ID')
            name = row.get('name') or row.get('Name')
            slug = row.get('slug') or row.get('Slug')
            category_name = row.get('category') or row.get('Category')
            price = row.get('price') or 0
            try:
                stock = int(row.get('stock') or 0)
            except ValueError:
                stock = 0
            available = row.get('available') in ('1', 'True', 'true', 'yes', 'Yes')
            description = row.get('description') or ''

            # Resolve or create category
            cat = None
            if category_name:
                cat, _ = Category.objects.get_or_create(name=category_name, defaults={'slug': slugify(category_name)})

            if pid:
                try:
                    prod = Product.objects.get(pk=int(pid))
                    prod.name = name or prod.name
                    prod.slug = slug or prod.slug
                    if cat:
                        prod.category = cat
                    prod.price = price or prod.price
                    prod.stock = stock
                    prod.available = available
                    prod.description = description
                    prod.save()
                    updated += 1
                    continue
                except Product.DoesNotExist:
                    pid = None

            # Create new product
            if name:
                p = Product.objects.create(
                    name=name,
                    slug=slug or generate_unique_slug(Product, name),
                    category=cat,
                    price=price or 0,
                    stock=stock,
                    description=description,
                    available=available
                )
                created += 1

        messages.success(request, f"Import complete: {created} created, {updated} updated.")
    else:
        messages.error(request, "No CSV file uploaded.")

    return redirect('admin_products')

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
def admin_edit_gallery_item(request, pk):
    item = get_object_or_404(GalleryItem, pk=pk)
    
    if request.method == 'POST':
        item.title = request.POST.get('title')
        item.category = request.POST.get('category', 'Other')
        item.price = request.POST.get('price', 0)
        
        new_image = request.FILES.get('image')
        if new_image:
            item.image = new_image
        
        item.save()
        messages.success(request, f"Gallery item '{item.title}' updated successfully!")
        return redirect('admin_media')
    
    categories = Category.objects.all()
    return render(request, 'admin/edit_gallery_item.html', {
        'item': item,
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
        
        if action == "delete":
            if item_type == "collections":
                obj = get_object_or_404(Category, id=item_id)
                obj.delete()
            elif item_type == "gallery":
                obj = get_object_or_404(GalleryItem, id=item_id)
                obj.delete()
            elif item_type == "woodwork":
                obj = get_object_or_404(Product, id=item_id)
                obj.delete()
            messages.success(request, "Item removed from Museum.")
            return redirect('museum_manager')
        
        elif action == "save":
            name = request.POST.get('name')
            price = request.POST.get('price', 0)
            new_image = request.FILES.get('image')
            
            if item_type == "collections":
                if item_id:
                    obj = get_object_or_404(Category, id=item_id)
                    obj.name = name
                    obj.slug = generate_unique_slug(Category, name, instance_id=item_id)
                    if new_image:
                        obj.image = new_image
                    obj.save()
                else:
                    Category.objects.create(
                        name=name,
                        slug=generate_unique_slug(Category, name),
                        image=new_image
                    )
            
            elif item_type == "gallery":
                if item_id:
                    obj = get_object_or_404(GalleryItem, id=item_id)
                    obj.title = name
                    obj.price = price
                    if new_image:
                        obj.image = new_image
                    obj.save()
                else:
                    GalleryItem.objects.create(
                        title=name,
                        price=price,
                        image=new_image
                    )
            
            elif item_type == "woodwork":
                wood_category, _ = Category.objects.get_or_create(
                    name='Wood',
                    defaults={'slug': 'wood'}
                )
                
                if item_id:
                    obj = get_object_or_404(Product, id=item_id)
                    obj.name = name
                    obj.slug = generate_unique_slug(Product, name, instance_id=item_id)
                    obj.price = price
                    if new_image:
                        obj.image = new_image
                    obj.save()
                else:
                    Product.objects.create(
                        name=name,
                        slug=generate_unique_slug(Product, name),
                        price=price,
                        image=new_image,
                        category=wood_category,
                        stock=0,
                        available=True
                    )
            
            messages.success(request, "Museum updated successfully!")
            return redirect('museum_manager')
    
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
    site_info, _ = SiteSetting.objects.get_or_create(id=1)
    featured_products = Product.objects.filter(available=True).select_related('category')[:4]
    return render(request, 'cart.html', {
        'site_info': site_info,
        'featured_products': featured_products,
    })


def wishlist_page(request):
    site_info, _ = SiteSetting.objects.get_or_create(id=1)
    featured_products = Product.objects.filter(available=True).select_related('category')[:6]
    return render(request, 'wishlist.html', {
        'site_info': site_info,
        'featured_products': featured_products,
    })

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


    from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404
from .models import ContactMessage

@require_POST
def review_submit(request):
    try:
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        product_id = request.POST.get('product')
        rating = request.POST.get('rating', '5')
        comment = request.POST.get('comment', '').strip()

        if not name or not email or not product_id or not comment:
            return JsonResponse({'success': False, 'error': 'All review fields are required'}, status=400)
        if '@' not in email or '.' not in email:
            return JsonResponse({'success': False, 'error': 'Invalid email format'}, status=400)

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Product not found'}, status=400)

        customer, created = Customer.objects.get_or_create(
            email=email,
            defaults={'full_name': name}
        )
        try:
            rating_val = int(rating)
        except (TypeError, ValueError):
            rating_val = 5

        Review.objects.create(
            customer=customer,
            product=product,
            rating=rating_val,
            comment=comment
        )
        return JsonResponse({'success': True, 'message': 'Review submitted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@require_POST
def contact_submit(request):
    try:
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        message = request.POST.get('message', '').strip()
        
        if not name or not email or not message:
            return JsonResponse({'success': False, 'error': 'All fields are required'}, status=400)
        
        if '@' not in email or '.' not in email:
            return JsonResponse({'success': False, 'error': 'Invalid email format'}, status=400)
        
        ContactMessage.objects.create(name=name, email=email, message=message)
        return JsonResponse({'success': True, 'message': 'Your message has been sent successfully!'})
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_contact_messages(request):
    filter_status = request.GET.get('status', None)
    
    if filter_status == 'unread':
        messages_list = ContactMessage.objects.filter(is_read=False)
    elif filter_status == 'read':
        messages_list = ContactMessage.objects.filter(is_read=True)
    else:
        messages_list = ContactMessage.objects.all()
    
    paginator = Paginator(messages_list, 15)
    page_obj = paginator.get_page(request.GET.get('page'))
    
    context = {
        'messages': page_obj,
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'total_messages': ContactMessage.objects.count(),
        'unread_count': ContactMessage.objects.filter(is_read=False).count(),
        'read_count': ContactMessage.objects.filter(is_read=True).count(),
        'filter_status': filter_status,
    }
    return render(request, 'admin/admin_contact_messages.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def mark_message_read(request, message_id):
    try:
        message = get_object_or_404(ContactMessage, id=message_id)
        message.is_read = True
        message.save()
        return JsonResponse({'success': True, 'message': 'Message marked as read'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@login_required
@user_passes_test(lambda u: u.is_superuser)
@require_POST
def delete_contact_message(request, message_id):
    try:
        message = get_object_or_404(ContactMessage, id=message_id)
        message.delete()
        return JsonResponse({'success': True, 'message': 'Message deleted successfully'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
    



    # core/views.py

from .models import AboutPage  # Ensure this is imported

def about(request):
    about_content, created = AboutPage.objects.get_or_create(id=1)

    return render(request, 'about.html', {
        'about': about_content
    })


@login_required
def admin_about_editor(request):
    if not request.user.is_staff:
        return redirect('home')

    about_content, created = AboutPage.objects.get_or_create(id=1)

    if request.method == 'POST':
        # Manually save fields (or use a ModelForm for cleaner code)
        about_content.hero_title = request.POST.get('hero_title')
        about_content.hero_subtitle = request.POST.get('hero_subtitle')
        
        about_content.philosophy_title = request.POST.get('philosophy_title')
        about_content.philosophy_text_1 = request.POST.get('philosophy_text_1')
        about_content.philosophy_text_2 = request.POST.get('philosophy_text_2')
        
        about_content.founder_name = request.POST.get('founder_name')
        about_content.founder_story_1 = request.POST.get('founder_story_1')
        about_content.founder_quote = request.POST.get('founder_quote')
        about_content.video_url = request.POST.get('video_url')

        # Handle Images
        if request.FILES.get('hero_bg_image'):
            about_content.hero_bg_image = request.FILES.get('hero_bg_image')
        if request.FILES.get('philosophy_image'):
            about_content.philosophy_image = request.FILES.get('philosophy_image')
        if request.FILES.get('founder_image'):
            about_content.founder_image = request.FILES.get('founder_image')

        about_content.save()
        messages.success(request, "About Page updated successfully!")
        return redirect('admin_about_editor')

    return render(request, 'admin/about_editor.html', {'about': about_content})

from decimal import Decimal, InvalidOperation
from django.views.decorators.http import require_GET, require_POST


def get_site_settings():
    settings_obj, _ = SiteSetting.objects.get_or_create(id=1)
    return settings_obj


def get_customer_for_user(user):
    customer, _ = Customer.objects.get_or_create(
        user=user,
        defaults={
            'full_name': user.get_full_name() or user.username,
            'email': user.email or f'{user.username}@example.com',
        },
    )
    changed = False
    if user.email and customer.email != user.email:
        customer.email = user.email
        changed = True
    full_name = user.get_full_name() or user.username
    if full_name and customer.full_name != full_name:
        customer.full_name = full_name
        changed = True
    if changed:
        customer.save()
    return customer


def parse_checkout_items(raw_items):
    parsed_items = []
    product_ids = []

    for raw_item in raw_items:
        product_id = raw_item.get('id')
        quantity = raw_item.get('quantity', 1)

        try:
            product_id = int(product_id)
            quantity = int(quantity)
        except (TypeError, ValueError):
            continue

        if quantity <= 0:
            continue

        product_ids.append(product_id)
        parsed_items.append({'id': product_id, 'quantity': quantity})

    products = Product.objects.filter(id__in=product_ids, available=True)
    product_map = {product.id: product for product in products}

    valid_items = []
    subtotal = Decimal('0.00')

    for item in parsed_items:
        product = product_map.get(item['id'])
        if not product:
            continue

        quantity = min(item['quantity'], max(product.stock, 1)) if product.stock else item['quantity']
        line_total = product.price * quantity
        subtotal += line_total
        valid_items.append({
            'product': product,
            'quantity': quantity,
            'line_total': line_total,
        })

    return valid_items, subtotal


def build_checkout_totals(items, site_info):
    subtotal = sum((item['line_total'] for item in items), Decimal('0.00'))
    shipping_rate = Decimal(str(site_info.shipping_flat_rate))
    tax_rate = Decimal(str(site_info.tax_rate))
    shipping = shipping_rate if items else Decimal('0.00')
    tax = (subtotal * tax_rate) / Decimal('100.00')
    total = subtotal + shipping + tax
    return {
        'subtotal': subtotal,
        'shipping': shipping,
        'tax': tax,
        'total': total,
    }


def create_order_records(customer, items, payment_method, totals, shipping_data):
    order = Order.objects.create(
        customer=customer,
        complete=False,
        payment_method=payment_method,
        status='Pending',
    )

    for item in items:
        OrderItem.objects.create(
            order=order,
            product=item['product'],
            quantity=item['quantity'],
        )

    ShippingAddress.objects.create(
        customer=customer,
        order=order,
        address=shipping_data['address'],
        city=shipping_data['city'],
        state=shipping_data['state'],
        zipcode=shipping_data['zipcode'],
    )

    return order


def finalize_order(order, payment_id=''):
    if order.complete:
        return order

    for order_item in order.orderitem_set.select_related('product'):
        product = order_item.product
        if not product:
            continue
        if product.stock >= order_item.quantity:
            product.stock -= order_item.quantity
        else:
            product.stock = 0
        product.available = product.stock > 0
        product.save(update_fields=['stock', 'available', 'updated_at'])

    order.complete = True
    order.status = 'Processing'
    if payment_id:
        order.razorpay_payment_id = payment_id
        order.transaction_id = payment_id
    elif order.payment_method == 'COD':
        order.transaction_id = f'COD-{order.id}'
    order.save()
    return order


def restock_order(order):
    if not order.complete:
        return order

    for order_item in order.orderitem_set.select_related('product'):
        product = order_item.product
        if not product:
            continue
        product.stock += order_item.quantity
        product.available = product.stock > 0
        product.save(update_fields=['stock', 'available', 'updated_at'])

    order.complete = False
    order.save(update_fields=['complete'])
    return order


def payment_keys_configured():
    key_id = getattr(settings, 'RAZORPAY_KEY_ID', '') or ''
    key_secret = getattr(settings, 'RAZORPAY_KEY_SECRET', '') or ''
    invalid_markers = {'rzp_test_YOUR_KEY_HERE', 'YOUR_SECRET_HERE', ''}
    return key_id not in invalid_markers and key_secret not in invalid_markers


def cart_page(request):
    featured_products = Product.objects.filter(available=True).select_related('category')[:4]
    return render(request, 'cart.html', {
        'featured_products': featured_products,
    })



def wishlist_page(request):
    featured_products = Product.objects.filter(available=True).select_related('category')[:6]
    return render(request, 'wishlist.html', {
        'featured_products': featured_products,
    })


@login_required
@require_GET
def checkout(request):
    customer = get_customer_for_user(request.user)
    site_info = get_site_settings()
    return render(request, 'checkout.html', {
        'customer': customer,
        'razorpay_key_id': settings.RAZORPAY_KEY_ID,
        'razorpay_enabled': payment_keys_configured(),
        'shipping_rate': site_info.shipping_flat_rate,
        'tax_rate': site_info.tax_rate,
    })


@login_required
@require_POST
def create_checkout_order(request):
    try:
        payload = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'error': 'Invalid checkout payload.'}, status=400)

    raw_items = payload.get('items', [])
    payment_method = (payload.get('payment_method') or 'COD').upper()
    shipping_data = {
        'full_name': (payload.get('full_name') or '').strip(),
        'email': (payload.get('email') or '').strip(),
        'phone': (payload.get('phone') or '').strip(),
        'address': (payload.get('address') or '').strip(),
        'city': (payload.get('city') or '').strip(),
        'state': (payload.get('state') or '').strip(),
        'zipcode': (payload.get('zipcode') or '').strip(),
    }

    required_fields = ['full_name', 'email', 'phone', 'address', 'city', 'state', 'zipcode']
    missing = [field for field in required_fields if not shipping_data[field]]
    if missing:
        return JsonResponse({'success': False, 'error': 'Please complete all checkout fields.'}, status=400)

    if payment_method not in {'COD', 'ONLINE'}:
        return JsonResponse({'success': False, 'error': 'Invalid payment method.'}, status=400)

    items, subtotal = parse_checkout_items(raw_items)
    if not items:
        return JsonResponse({'success': False, 'error': 'Your cart is empty.'}, status=400)

    customer = get_customer_for_user(request.user)
    customer.full_name = shipping_data['full_name']
    customer.email = shipping_data['email']
    customer.phone = shipping_data['phone']
    customer.address = shipping_data['address']
    customer.save()

    site_info = get_site_settings()
    totals = build_checkout_totals(items, site_info)
    order = create_order_records(customer, items, payment_method, totals, shipping_data)
    request.session['latest_order_id'] = order.id

    if payment_method == 'COD':
        return JsonResponse({
            'success': True,
            'mode': 'cod',
            'redirect_url': '/payment-success/',
        })

    if not payment_keys_configured():
        order.delete()
        return JsonResponse({'success': False, 'error': 'Razorpay keys are not configured in Django settings yet.'}, status=400)

    amount_paise = int(totals['total'] * 100)
    razorpay_order = client.order.create({
        'amount': amount_paise,
        'currency': 'INR',
        'payment_capture': '1',
    })

    order.razorpay_order_id = razorpay_order['id']
    order.transaction_id = razorpay_order['id']
    order.save(update_fields=['razorpay_order_id', 'transaction_id'])

    return JsonResponse({
        'success': True,
        'mode': 'online',
        'razorpay': {
            'key': settings.RAZORPAY_KEY_ID,
            'amount': amount_paise,
            'currency': 'INR',
            'name': site_info.store_name,
            'description': f'Order #{order.id}',
            'order_id': razorpay_order['id'],
            'prefill': {
                'name': shipping_data['full_name'],
                'email': shipping_data['email'],
                'contact': shipping_data['phone'],
            },
        },
    })


@csrf_exempt
@login_required
@require_POST
def verify_payment(request):
    payload = {
        'razorpay_payment_id': request.POST.get('razorpay_payment_id'),
        'razorpay_order_id': request.POST.get('razorpay_order_id'),
        'razorpay_signature': request.POST.get('razorpay_signature'),
    }

    if not all(payload.values()):
        return JsonResponse({'status': 'error', 'error': 'Missing payment verification data.'}, status=400)

    try:
        client.utility.verify_payment_signature(payload)
    except Exception:
        return JsonResponse({'status': 'error', 'error': 'Payment signature verification failed.'}, status=400)

    order = get_object_or_404(Order, razorpay_order_id=payload['razorpay_order_id'])
    order.razorpay_payment_id = payload['razorpay_payment_id']
    order.transaction_id = payload['razorpay_payment_id']
    order.status = 'Pending'
    order.save(update_fields=['razorpay_payment_id', 'transaction_id', 'status'])
    request.session['latest_order_id'] = order.id
    return JsonResponse({'status': 'success', 'redirect_url': '/payment-success/'})


@login_required
def payment_success(request):
    order_id = request.session.get('latest_order_id')
    order = None
    if order_id:
        order = Order.objects.filter(id=order_id).select_related('customer').prefetch_related('orderitem_set__product').first()
    return render(request, 'success.html', {'order': order})


@login_required
def my_orders(request):
    customer = get_customer_for_user(request.user)
    orders = (
        Order.objects.filter(customer=customer)
        .select_related('customer')
        .prefetch_related('orderitem_set__product', 'shippingaddress_set')
        .order_by('-date_ordered')
    )
    return render(request, 'my_orders.html', {'orders': orders})


@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_orders(request):
    orders = (
        Order.objects.all()
        .select_related('customer')
        .prefetch_related('orderitem_set__product', 'shippingaddress_set')
        .order_by('-date_ordered')
    )
    return render(request, 'admin/orders_realtime.html', {'orders': orders})


@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
@require_POST
def admin_update_order_status(request, order_id):
    order = get_object_or_404(
        Order.objects.select_related('customer').prefetch_related('orderitem_set__product'),
        id=order_id,
    )
    new_status = (request.POST.get('status') or '').strip()
    valid_statuses = {choice[0] for choice in Order.STATUS_CHOICES}
    fulfilled_statuses = {'Processing', 'Shipped', 'Delivered'}

    if new_status not in valid_statuses:
        messages.error(request, 'Invalid order status selected.')
        return redirect('admin_orders')

    if new_status in fulfilled_statuses and not order.complete:
        finalize_order(order, order.razorpay_payment_id or '')

    if new_status == 'Cancelled' and order.complete:
        restock_order(order)

    order.status = new_status
    order.save(update_fields=['status'])
    messages.success(request, f'Order #{order.id} updated to {new_status}.')
    return redirect('admin_orders')


@login_required(login_url='login')
@user_passes_test(admin_only, login_url='login')
def admin_settings(request):
    settings_obj, _ = SiteSetting.objects.get_or_create(id=1)

    if request.method == 'POST':
        settings_obj.store_name = request.POST.get('store_name', settings_obj.store_name)
        settings_obj.admin_email = request.POST.get('admin_email', settings_obj.admin_email)
        settings_obj.contact_phone = request.POST.get('contact_phone', settings_obj.contact_phone)
        settings_obj.currency = request.POST.get('currency', settings_obj.currency)

        try:
            settings_obj.tax_rate = Decimal(request.POST.get('tax_rate', settings_obj.tax_rate))
        except (TypeError, InvalidOperation):
            pass

        try:
            settings_obj.shipping_flat_rate = Decimal(request.POST.get('shipping_flat_rate', settings_obj.shipping_flat_rate))
        except (TypeError, InvalidOperation):
            pass

        settings_obj.maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        settings_obj.save()

        messages.success(request, 'Settings updated successfully!')
        return redirect('admin_settings')

    return render(request, 'admin/settings.html', {'settings': settings_obj})
