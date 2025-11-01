from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'core'

urlpatterns = [
    # Pages statiques
    path('', views.home, name='home'),
    path('contact/', views.contact_view, name='contact'),
    path('about/', views.about_view, name='about'),
    path('terms/', views.terms_view, name='terms'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('faq/', views.faq_view, name='faq'),
    
    # Produits
    path('products/', views.ProductListView.as_view(), name='product_list'),
    path('products/category/<slug:category_slug>/', views.ProductListView.as_view(), name='product_list_by_category'),
    path('products/<slug:slug>/', views.ProductDetailView.as_view(), name='product_detail'),

    path('api/toggle-favorite/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('api/add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('api/submit-review/<int:product_id>/', views.submit_review, name='submit_review'),
    path('clear', views.clear_cart, name='clear_cart'),
    
    # Favoris
    path('favorites/', views.FavoriteListView.as_view(), name='favorite_list'),
    path('favorites/toggle/<int:product_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('products/<int:product_id>/toggle-favorite/', views.toggle_favorite, name='toggle_favorite'),
    

    
    # Panier
    path('cart/', views.cart_view, name='cart_view'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('cart/remove/<int:item_id>/', views.remove_cart_item, name='remove_cart_item'),
    path('cart/apply-coupon/', views.apply_coupon, name='apply_coupon'),
    
    # Checkout
    path('checkout/', views.checkout_view, name='checkout'),
    path('checkout/confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('checkout/finalize/', views.finalize_order, name='finalize_order'),
    
    # Compte utilisateur
    path('account/orders/', views.order_history, name='order_history'),
    path('account/orders/<str:order_number>/', views.order_detail, name='order_detail'),
    path('account/addresses/', views.address_list, name='address_list'),
    path('account/addresses/add/', views.address_create, name='address_create'),
    path('account/addresses/<int:pk>/edit/', views.address_update, name='address_update'),
    path('account/addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),
    path('account/wishlist/', views.wishlist_view, name='wishlist'),
    path('account/wishlist/add/<int:product_id>/', views.wishlist_add, name='wishlist_add'),
    path('account/wishlist/remove/<int:product_id>/', views.wishlist_remove, name='wishlist_remove'),
    
    # Authentification (basique - à adapter selon votre système d'authentification)
    path('login/', auth_views.LoginView.as_view(template_name='account/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    
    # Newsletter
    path('newsletter/subscribe/', views.newsletter_subscribe, name='newsletter_subscribe'),
    path('payment/processing/<int:payment_id>/', views.payment_processing, name='payment_processing'),
    path('paygate/callback/', views.paygate_callback, name='paygate_callback'),
    path('api/check-payment-status/<int:payment_id>/', views.check_payment_status, name='check_payment_status'),
]