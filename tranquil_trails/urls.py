from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from core import views


urlpatterns = [

    # ===== MAIN SITE PAGES =====
    path('', views.home, name='home'),
    path('shop/', views.shop, name='shop'),
    path('product/<int:pk>/', views.product_detail, name='product_detail'),

    # Gallery
    path('gallery/', views.gallery, name='gallery'),
    path('gallery/<int:pk>/', views.gallery_detail, name='gallery_detail'),

    # Info Pages
    path('offers/', views.offers, name='offers'),
    path('about/', views.about, name='about'),
    # FIXED: Changed 'Contact' to 'contact' to match your template request
    path('contact-us/', views.contact, name='contact'),

    # Contact Submit + Admin contact
    path('contact/submit/', views.contact_submit, name='contact_submit'),
    path('admin/contact-messages/', views.admin_contact_messages, name='admin_contact_messages'),
    path('admin/contact-message/<int:message_id>/mark-read/', views.mark_message_read, name='mark_message_read'),
    path('admin/contact-message/<int:message_id>/delete/', views.delete_contact_message, name='delete_contact_message'),

    # ===== Authentication =====
    path('login/', views.login_page, name='login'),
    path('signup/', views.signup_page, name='signup'),

    # API Endpoints
    path('api/signup/', views.signup_api, name='signup_api'),
    path('api/login/', views.login_api, name='login_api'),
    path('api/logout/', views.logout_api, name='logout_api'),

    # ===== Cart & Payments =====
    path('cart/', views.cart_page, name='cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('verify-payment/', views.verify_payment, name='verify_payment'),
    path('payment-success/', views.payment_success, name='payment_success'),

    # ===== CUSTOM ADMIN PANEL =====

    # Dashboard & Analytics
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-analytics/', views.admin_analytics, name='admin_analytics'),

    # Products
    path('admin-products/', views.admin_products, name='admin_products'),
    path('admin/products/', views.admin_products, name='admin_products'),
    path('admin-add-product/', views.admin_add_product, name='admin_add_product'),
    path('admin/products/add/', views.admin_add_product, name='admin_add_product'),
    path('admin-edit-product/<int:pk>/', views.admin_edit_product, name='admin_edit_product'),
    path('admin-delete-product/<int:pk>/', views.admin_delete_product, name='admin_delete_product'),

    # Categories
    path('admin-categories/', views.admin_categories, name='admin_categories'),
    path('admin/categories/', views.admin_categories, name='admin_categories'),
    path('admin-edit-category/<int:pk>/', views.admin_edit_category, name='admin_edit_category'),
    path('admin-delete-category/<int:pk>/', views.admin_delete_category, name='admin_delete_category'),

    # Gallery / Media
    path('admin-media/', views.admin_media, name='admin_media'),
    path('admin/media/', views.admin_media, name='admin_media'),
    path('admin-edit-gallery-item/<int:pk>/', views.admin_edit_gallery_item, name='admin_edit_gallery_item'),
    path('admin-delete-gallery-item/<int:pk>/', views.admin_delete_gallery_item, name='admin_delete_gallery_item'),

    # Inventory
    path('admin-inventory/', views.admin_inventory, name='admin_inventory'),
    path('admin/inventory/', views.admin_inventory, name='admin_inventory'),
    path('admin-dashboard/inventory/', views.admin_inventory, name='admin_inventory'),
    path('admin-dashboard/inventory/update/<int:pk>/', views.admin_update_stock, name='admin_update_stock'),

    # Orders
    path('admin-orders/', views.admin_orders, name='admin_orders'),
    path('admin/orders/', views.admin_orders, name='admin_orders'),

    # Reviews
    path('admin-reviews/', views.admin_reviews, name='admin_reviews'),
    path('admin/reviews/', views.admin_reviews, name='admin_reviews'),
    path('admin-dashboard/reviews/', views.admin_reviews, name='admin_reviews'),
    path('admin-dashboard/reviews/delete/<int:pk>/', views.admin_delete_review, name='admin_delete_review'),
    path('admin-dashboard/reviews/toggle-heart/<int:pk>/', views.admin_toggle_heart, name='admin_toggle_heart'),

    # Other Admin Pages
    path('admin-invoices/', views.admin_invoices, name='admin_invoices'),
    path('admin-shipments/', views.admin_shipments, name='admin_shipments'),
    path('admin-returns/', views.admin_returns, name='admin_returns'),
    path('admin-customers/', views.admin_customers, name='admin_customers'),
    path('admin-segments/', views.admin_segments, name='admin_segments'),
    path('admin-staff/', views.admin_staff, name='admin_staff'),

    # Discounts & Campaigns
    path('admin-discounts/', views.admin_discounts, name='admin_discounts'),
    path('admin-discounts/delete/<int:pk>/', views.admin_delete_discount, name='admin_delete_discount'),
    path('admin-campaigns/', views.admin_campaigns, name='admin_campaigns'),

    # Blog & Settings
    path('admin-blog/', views.admin_blog, name='admin_blog'),
    path('admin-settings/', views.admin_settings, name='admin_settings'),
    path('admin/settings/', views.admin_settings, name='admin_settings'),

    # Museum Manager
    path('admin-dashboard/museum-manager/', views.admin_museum_manager, name='museum_manager'),

    # ===== DJANGO BUILT-IN ADMIN (LAST) =====
    path('admin/', admin.site.urls),
    path('admin-dashboard/about-editor/', views.admin_about_editor, name='admin_about_editor'),
]


# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)