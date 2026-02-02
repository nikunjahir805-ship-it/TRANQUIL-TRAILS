from django.contrib import admin
from django.urls import path
from django.conf import settings 
from django.conf.urls.static import static
from core import views

urlpatterns = [
    # --- 1. Main Site Pages ---
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    
    path('shop/', views.shop, name='shop'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),
    
    # Gallery
    path('gallery/', views.gallery, name='gallery'),
    path('gallery/<int:pk>/', views.gallery_detail, name='gallery_detail'),

    # Info Pages
    path('offers/', views.offers, name='offers'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='Contact'),

    # --- 2. Authentication Pages ---
    path('login/', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),

    # --- 3. Admin Panel Views ---
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),
    
    # Products
    path('admin-products/', views.admin_products, name='admin_products'),
    path('admin-add-product/', views.admin_add_product, name='admin_add_product'),
    path('admin-delete-product/<int:pk>/', views.admin_delete_product, name='admin_delete_product'),

    # Categories (Management)
    path('admin-categories/', views.admin_categories, name='admin_categories'),
    path('admin-delete-category/<int:pk>/', views.admin_delete_category, name='admin_delete_category'),

    # Gallery Management
    path('admin-media/', views.admin_media, name='admin_media'),
    path('admin-delete-gallery-item/<int:pk>/', views.admin_delete_gallery_item, name='admin_delete_gallery_item'),

    # Other Admin Tables
    path('admin-inventory/', views.admin_inventory, name='admin_inventory'),
    path('admin-reviews/', views.admin_reviews, name='admin_reviews'),
    path('admin-orders/', views.admin_orders, name='admin_orders'),
    path('admin-invoices/', views.admin_invoices, name='admin_invoices'),
    path('admin-shipments/', views.admin_shipments, name='admin_shipments'),
    path('admin-returns/', views.admin_returns, name='admin_returns'),
    path('admin-customers/', views.admin_customers, name='admin_customers'),
    path('admin-segments/', views.admin_segments, name='admin_segments'),
    path('admin-staff/', views.admin_staff, name='admin_staff'),
    
    # --- DISCOUNTS & OFFERS (Fixed) ---
    path('admin-discounts/', views.admin_discounts, name='admin_discounts'),
    # This line was missing, causing the error:
    path('admin-discounts/delete/<int:pk>/', views.admin_delete_discount, name='admin_delete_discount'),

    path('admin-campaigns/', views.admin_campaigns, name='admin_campaigns'),
    path('admin-blog/', views.admin_blog, name='admin_blog'),
    path('admin-settings/', views.admin_settings, name='admin_settings'),
    
    # --- 4. API Endpoints (Backend Logic) ---
    path('api/signup/', views.signup_api, name='signup_api'),
    path('api/login/', views.login_api, name='login_api'),
    path('api/logout/', views.logout_api, name='logout_api'),

    # Reviews Management
    path('admin-dashboard/reviews/', views.admin_reviews, name='admin_reviews'),
    path('admin-dashboard/reviews/delete/<int:pk>/', views.admin_delete_review, name='admin_delete_review'),
    path('admin-dashboard/reviews/toggle-heart/<int:pk>/', views.admin_toggle_heart, name='admin_toggle_heart'),
]

# Enable Image Loading
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    