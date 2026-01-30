from django.contrib import admin
from django.urls import path
from django.conf import settings 
from django.conf.urls.static import static
from core import views

urlpatterns = [
    # Main Site
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    
    # --- NEW: PRODUCT DETAIL PATH ---
    # This line connects the URL "product/5/" to the product_detail view
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    # --------------------------------
    
    path('offers/', views.offers, name='offers'),
    path('gallery/', views.gallery, name='gallery'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='Contact'),
    path('login/', views.login_page, name='login'),

    # Admin Panel - Core
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),
    
    # Admin Panel - Catalog
    path('admin-products/', views.admin_products, name='admin_products'),
    path('admin-add-product/', views.admin_add_product, name='admin_add_product'),
    path('admin-categories/', views.admin_categories, name='admin_categories'),
    path('admin-inventory/', views.admin_inventory, name='admin_inventory'),
    path('admin-reviews/', views.admin_reviews, name='admin_reviews'),

    # Admin Panel - Sales
    path('admin-orders/', views.admin_orders, name='admin_orders'),
    path('admin-invoices/', views.admin_invoices, name='admin_invoices'),
    path('admin-shipments/', views.admin_shipments, name='admin_shipments'),
    path('admin-returns/', views.admin_returns, name='admin_returns'),

    # Admin Panel - People
    path('admin-customers/', views.admin_customers, name='admin_customers'),
    path('admin-segments/', views.admin_segments, name='admin_segments'),
    path('admin-staff/', views.admin_staff, name='admin_staff'),

    # Admin Panel - Marketing & Content
    path('admin-discounts/', views.admin_discounts, name='admin_discounts'),
    path('admin-campaigns/', views.admin_campaigns, name='admin_campaigns'),
    path('admin-blog/', views.admin_blog, name='admin_blog'),
    path('admin-media/', views.admin_media, name='admin_media'),
    
    # Admin Panel - System
    path('admin-settings/', views.admin_settings, name='admin_settings'),
    
    # API Paths
    path('api/signup/', views.signup_api, name='signup_api'),
    path('api/login/', views.login_api, name='login_api'),
    path('api/logout/', views.logout_api, name='logout_api'),
]

# IMPORTANT: enable media file serving during development
# This makes sure product images (uploaded in Admin) actually show up
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)