# universepro/context_processors.py
from .models import Cart, SiteSetting

def cart_context(request):
    """Context processor pour le panier"""
    cart_items = []
    cart_total = 0
    cart_count = 0
    
    if request.user.is_authenticated:
        try:
            cart = Cart.objects.get(user=request.user)
            cart_items = cart.items.all()
            # Calculate total by summing all items' totals
            cart_total = sum(item.product.price * item.quantity for item in cart_items)
            cart_count = cart.items.count()
        except Cart.DoesNotExist:
            pass
    
    return {
        'cart_items': cart_items,
        'cart_total': cart_total,
        'cart_count': cart_count,
    }

def site_settings(request):
    """Context processor pour les paramètres du site"""
    settings = SiteSetting.objects.first()
    return {
        'site_settings': settings,
        'whatsapp_phone': settings.whatsapp_phone if settings else '',
        'whatsapp_message': settings.whatsapp_message if settings else '',
    }