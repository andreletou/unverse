from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.generic import ListView, DetailView, TemplateView
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.http import JsonResponse, HttpResponseBadRequest
from django.db.models import Q, Count, Avg
from django.contrib import messages
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.db.models import F, Sum
from django.db import models
import json
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
import requests

from .models import (
    Product, Category, ProductReview, Favorite, Cart, CartItem,
    Order, OrderItem, Coupon, Address, ShippingMethod, TrendingProduct,
    Wishlist, WishlistItem, Notification, Payment
)
from .forms import (
    ProductReviewForm, AddressForm, CheckoutForm, 
    NewsletterSubscriptionForm, ContactForm
)

# Classe helper pour PayGateGlobal
class PayGatePayment:
    @staticmethod
    def initiate_payment(order, phone_number, network):
        """
        Initie un paiement via PayGateGlobal
        """
        payload = {
            "auth_token": settings.PAYGATE_API_KEY,
            "phone_number": phone_number,
            "amount": str(order.total),
            "identifier": order.order_number,
            "network": network.upper(),  # FLOOZ ou TMONEY
            "description": f"Paiement pour la commande #{order.order_number}"
        }
        
        try:
            response = requests.post(
                settings.PAYGATE_PAY_URL,
                json=payload,
                timeout=30
            )
            data = response.json()
            
            if data.get('status') == 0:  # Succès
                # Créez l'enregistrement de paiement
                payment = Payment.objects.create(
                    order=order,
                    amount=order.total,
                    method='mobile_money',
                    status='pending',
                    payment_details={
                        'tx_reference': data['tx_reference'],
                        'network': network,
                        'phone_number': phone_number
                    }
                )
                return True, payment
            else:
                return False, f"Erreur PayGate: {data.get('message', 'Erreur inconnue')}"
                
        except Exception as e:
            return False, str(e)

    @staticmethod
    def check_payment_status(tx_reference):
        """
        Vérifie le statut d'un paiement
        """
        payload = {
            "auth_token": settings.PAYGATE_API_KEY,
            "tx_reference": tx_reference
        }
        
        try:
            response = requests.post(
                settings.PAYGATE_STATUS_URL,
                json=payload,
                timeout=30
            )
            return response.json()
        except Exception as e:
            return {'status': 'error', 'message': str(e)}

# Vues existantes (conservées)
def home(request):
    featured_products = Product.objects.filter(
        featured=True, 
        is_active=True
    ).order_by('-created_at').prefetch_related('images', 'reviews')[:8]
    
    new_products = Product.objects.filter(
        is_active=True
    ).order_by('-created_at').prefetch_related('images', 'reviews')[:8]
    
    discounted_products = Product.objects.filter(
        is_active=True,
        original_price__isnull=False
    ).exclude(original_price=0).prefetch_related('images', 'reviews')[:8]
    
    trending_products = TrendingProduct.objects.filter(
        date=timezone.now().date(),
        period='daily'
    ).select_related('product').order_by('rank')[:8]
    
    main_categories = Category.objects.filter(
        parent__isnull=True,
        is_active=True
    )[:6]
    
    context = {
        'featured_products': featured_products,
        'new_products': new_products,
        'discounted_products': discounted_products,
        'trending_products': [tp.product for tp in trending_products],
        'main_categories': main_categories,
    }
    
    return render(request, 'index.html', context)

class ProductListView(ListView):
    model = Product
    template_name = 'products/product_list.html'
    context_object_name = 'products'
    paginate_by = 12
    
    def get_queryset(self):
        queryset = Product.objects.filter(is_active=True)
        
        category_slug = self.kwargs.get('category_slug')
        if category_slug:
            category = get_object_or_404(Category, slug=category_slug)
            subcategories = category.children.all()
            if subcategories.exists():
                queryset = queryset.filter(
                    Q(category=category) | Q(category__in=subcategories)
                )
            else:
                queryset = queryset.filter(category=category)
        
        search_query = self.request.GET.get('q')
        if search_query:
            queryset = queryset.filter(
                Q(name__icontains=search_query) |
                Q(description__icontains=search_query) |
                Q(short_description__icontains=search_query)
            )
        
        sort_by = self.request.GET.get('sort_by')
        if sort_by == 'price_asc':
            queryset = queryset.order_by('price')
        elif sort_by == 'price_desc':
            queryset = queryset.order_by('-price')
        elif sort_by == 'rating':
            queryset = queryset.annotate(
                avg_rating=Avg('reviews__rating')
            ).order_by('-avg_rating')
        elif sort_by == 'name':
            queryset = queryset.order_by('name')
        elif sort_by == 'newest':
            queryset = queryset.order_by('-created_at')
        elif sort_by == 'popular':
            queryset = queryset.annotate(
                review_count=Count('reviews')
            ).order_by('-review_count')
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.filter(
            parent__isnull=True,
            is_active=True
        )
        context['current_category'] = self.kwargs.get('category_slug')
        context['search_query'] = self.request.GET.get('q', '')
        context['sort_by'] = self.request.GET.get('sort_by', '')
        return context

class ProductDetailView(DetailView):
    model = Product
    template_name = 'products/product_detail.html'
    context_object_name = 'product'
    slug_url_kwarg = 'slug'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        product = self.object
        
        images = product.images.all().order_by('order')
        context['main_image'] = images.filter(is_featured=True).first() or images.first()
        context['other_images'] = images.exclude(id=context['main_image'].id) if context['main_image'] else []
        
        reviews = product.reviews.filter(is_approved=True).select_related('user')
        context['reviews'] = reviews
        
        rating_stats = {}
        for i in range(5, 0, -1):
            rating_stats[i] = reviews.filter(rating=i).count()
        context['rating_stats'] = rating_stats
        context['total_reviews'] = reviews.count()
        
        if self.request.user.is_authenticated:
            user_review = reviews.filter(user=self.request.user).first()
            context['review_form'] = ProductReviewForm(instance=user_review)
        else:
            context['review_form'] = ProductReviewForm()
        
        similar_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(id=product.id)[:4]
        context['similar_products'] = similar_products
        
        if self.request.user.is_authenticated:
            context['is_favorite'] = Favorite.objects.filter(
                user=self.request.user,
                product=product
            ).exists()
        else:
            context['is_favorite'] = False
        
        if self.request.user.is_authenticated:
            today = timezone.now().date()
            try:
                trending_product = TrendingProduct.objects.get(
                    product=product,
                    period='daily',
                    date=today
                )
                trending_product.views = F('views') + 1
                trending_product.save()
            except TrendingProduct.DoesNotExist:
                TrendingProduct.objects.create(
                    product=product,
                    period='daily',
                    date=today,
                    views=1
                )
        
        return context

@require_POST
def clear_cart(request):
    if request.user.is_authenticated:
        cart = get_object_or_404(Cart, user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            return JsonResponse({'status': 'error', 'message': 'Session invalide'})
        
        cart = get_object_or_404(Cart, session_key=session_key)
    
    cart.items.all().delete()
    cart.coupon = None
    cart.coupon_discount = Decimal('0.00')
    cart.shipping_cost = Decimal('0.00')
    cart.save()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'cleared',
            'message': 'Votre panier a été vidé avec succès',
            'cart_items_count': 0,
            'subtotal': '0.00',
            'shipping': '0.00',
            'total': '0.00'
        })
    
    messages.success(request, "Votre panier a été vidé avec succès")
    return redirect('core:view')

@login_required
def toggle_favorite(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    favorite, created = Favorite.objects.get_or_create(
        user=request.user,
        product=product
    )
    
    if not created:
        favorite.delete()
        return JsonResponse({'status': 'removed', 'message': 'Produit retiré des favoris'})
    
    return JsonResponse({'status': 'added', 'message': 'Produit ajouté aux favoris'})

class FavoriteListView(ListView):
    model = Favorite
    template_name = 'products/favorites.html'
    context_object_name = 'favorites'
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def get_queryset(self):
        return Favorite.objects.filter(user=self.request.user).select_related('product')

def cart_view(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    cart.calculate_shipping()
    
    context = {
        'cart': cart,
        'free_shipping_threshold': settings.FREE_SHIPPING_THRESHOLD,
    }
    
    return render(request, 'cart/cart.html', context)

@require_POST
def update_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            return HttpResponseBadRequest("Accès non autorisé")
    else:
        if cart_item.cart.session_key != request.session.session_key:
            return HttpResponseBadRequest("Accès non autorisé")
    
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity < 1:
        cart_item.delete()
        return JsonResponse({'status': 'removed'})
    
    if cart_item.product.stock_quantity and quantity > cart_item.product.stock_quantity:
        return JsonResponse({
            'status': 'error',
            'message': 'Quantité demandée supérieure au stock disponible'
        }, status=400)
    
    cart_item.quantity = quantity
    cart_item.save()
    
    cart = cart_item.cart
    cart.calculate_shipping()
    
    return JsonResponse({
        'status': 'updated',
        'subtotal': str(cart.subtotal),
        'shipping': str(cart.shipping_cost),
        'total': str(cart.total),
        'item_total': str(cart_item.total_price)
    })

@require_POST
def remove_cart_item(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    
    if request.user.is_authenticated:
        if cart_item.cart.user != request.user:
            return HttpResponseBadRequest("Accès non autorisé")
    else:
        if cart_item.cart.session_key != request.session.session_key:
            return HttpResponseBadRequest("Accès non autorisé")
    
    cart_item.delete()
    
    cart = cart_item.cart
    cart.calculate_shipping()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'removed',
            'subtotal': str(cart.subtotal),
            'shipping': str(cart.shipping_cost),
            'total': str(cart.total)
        })
    
    messages.success(request, "L'article a été retiré de votre panier")
    return redirect('core:view')

@require_POST
def apply_coupon(request):
    coupon_code = request.POST.get('coupon_code', '').strip()
    
    if request.user.is_authenticated:
        cart = get_object_or_404(Cart, user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            return JsonResponse({'status': 'error', 'message': 'Session invalide'})
        
        cart = get_object_or_404(Cart, session_key=session_key)
    
    try:
        coupon = Coupon.objects.get(code=coupon_code, is_active=True)
        if cart.apply_coupon(coupon_code):
            return JsonResponse({
                'status': 'success',
                'message': 'Coupon appliqué avec succès',
                'discount': str(cart.coupon_discount),
                'subtotal': str(cart.subtotal),
                'shipping': str(cart.shipping_cost),
                'total': str(cart.total)
            })
        else:
            return JsonResponse({
                'status': 'error',
                'message': 'Ce coupon ne peut pas être appliqué à votre panier'
            }, status=400)
    except Coupon.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'message': 'Coupon invalide ou expiré'
        }, status=400)

# Vue checkout mise à jour avec PayGateGlobal
@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.exists():
        messages.warning(request, "Votre panier est vide")
        return redirect('core:view')
    
    for item in cart.items.all():
        if not item.product.is_available():
            messages.error(request, f"{item.product.name} n'est plus disponible")
            return redirect('core:view')
        if item.product.stock_quantity and item.quantity > item.product.stock_quantity:
            messages.error(request, f"Stock insuffisant pour {item.product.name}")
            return redirect('core:view')
    
    addresses = Address.objects.filter(user=request.user)
    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            # Créer la commande
            order = Order.objects.create(
                user=request.user,
                cart=cart,
                shipping_address=form.cleaned_data['shipping_address'],
                billing_address=form.cleaned_data['billing_address'],
                subtotal=cart.subtotal,
                coupon_discount=cart.coupon_discount,
                shipping_cost=cart.shipping_cost,
                total=cart.total,
                payment_method=form.cleaned_data['payment_method'],
                note=form.cleaned_data['note']
            )
            
            # Créer les articles de la commande
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.price,
                    total_price=cart_item.total_price
                )
            
            # Mettre à jour le stock
            for cart_item in cart.items.all():
                if cart_item.product.stock_quantity:
                    cart_item.product.stock_quantity -= cart_item.quantity
                    cart_item.product.save()
            
            # Gestion du paiement selon la méthode choisie
            if form.cleaned_data['payment_method'] == 'mobile_money':
                phone_number = form.cleaned_data['mobile_money_phone']
                network = form.cleaned_data['mobile_money_network']
                
                success, result = PayGatePayment.initiate_payment(order, phone_number, network)
                
                if success:
                    payment = result
                    return redirect('core:payment_processing', payment_id=payment.id)
                else:
                    messages.error(request, f"Erreur de paiement: {result}")
                    return redirect('core:checkout')
            
            # Si autre méthode de paiement (carte bancaire, etc.)
            elif form.cleaned_data['payment_method'] == 'credit_card':
                # Ici vous intégrerez votre solution de paiement par carte
                pass
            
            # Rediriger vers la confirmation pour les autres méthodes
            return redirect('core:order_confirmation', order_number=order.order_number)
    else:
        form = CheckoutForm(user=request.user)
    
    context = {
        'cart': cart,
        'addresses': addresses,
        'shipping_methods': shipping_methods,
        'form': form,
    }
    
    return render(request, 'checkout/checkout.html', context)

# Vues pour le traitement des paiements
@login_required
def payment_processing(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    return render(request, 'payment/processing.html', {'payment': payment})


@login_required
def check_payment_status(request, payment_id):
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    
    if payment.status == 'completed':
        return JsonResponse({'status': 'completed'})
    
    # Vérifier auprès de PayGateGlobal si le statut a changé
    tx_reference = payment.payment_details.get('tx_reference')
    if tx_reference:
        result = PayGatePayment.check_payment_status(tx_reference)
        if result.get('status') == 0:  # Paiement réussi
            payment.status = 'completed'
            payment.save()
            payment.order.payment_status = True
            payment.order.save()
            return JsonResponse({'status': 'completed'})
    
    return JsonResponse({'status': 'pending'})

@csrf_exempt
@require_POST
def add_to_cart(request, product_id):
    """
    Ajoute un produit au panier avec gestion des sessions et AJAX
    """
    product = get_object_or_404(Product, id=product_id)
    
    if not product.is_available():
        return JsonResponse({
            'status': 'error', 
            'message': "Ce produit n'est pas disponible"
        }, status=400)
    
    # Gestion du panier pour utilisateur connecté ou anonyme
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        
        cart, created = Cart.objects.get_or_create(session_key=session_key)
    
    # Gestion de la quantité (par défaut 1)
    quantity = int(request.POST.get('quantity', 1))
    
    # Création ou mise à jour de l'article du panier
    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={
            'quantity': quantity, 
            'price': product.price
        }
    )
    
    if not created:
        new_quantity = cart_item.quantity + quantity
        # Vérification du stock
        if product.stock_quantity and new_quantity > product.stock_quantity:
            return JsonResponse({
                'status': 'error', 
                'message': "Quantité demandée supérieure au stock disponible",
                'available_quantity': product.stock_quantity
            }, status=400)
        
        cart_item.quantity = new_quantity
        cart_item.save()
    
    # Mise à jour du compteur du panier
    cart_items_count = cart.items.aggregate(total=Sum('quantity'))['total'] or 0
    
    # Réponse JSON pour requêtes AJAX
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'success',
            'message': f"{product.name} a été ajouté à votre panier",
            'cart_items_count': cart_items_count,
            'product_id': product.id
        })
    
    # Redirection standard si pas AJAX
    messages.success(request, f"{product.name} a été ajouté à votre panier")
    return redirect('core:product_detail', slug=product.slug)

@csrf_exempt
@require_POST
@login_required
def submit_review(request, product_id):
    """
    Soumet un avis sur un produit avec modération
    """
    product = get_object_or_404(Product, id=product_id)
    form = ProductReviewForm(request.POST)
    
    if form.is_valid():
        # Création ou mise à jour de l'avis
        review, created = ProductReview.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={
                'rating': form.cleaned_data['rating'],
                'title': form.cleaned_data['title'],
                'comment': form.cleaned_data['comment'],
                'is_approved': False  # Modération avant publication
            }
        )
        
        # Mise à jour de la note moyenne du produit
        product.update_average_rating()
        
        # Réponse AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'status': 'success',
                'message': 'Merci pour votre avis! Il sera publié après modération.',
                'average_rating': product.rating,
                'total_reviews': product.reviews.count(),
                'user_review': {
                    'rating': review.rating,
                    'title': review.title,
                    'comment': review.comment,
                    'created_at': review.created_at.strftime('%d/%m/%Y')
                }
            })
        
        messages.success(request, "Merci pour votre avis! Il sera publié après modération.")
        return redirect('core:product_detail', slug=product.slug)
    
    # Gestion des erreurs de formulaire
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'errors': form.errors
        }, status=400)
    
    messages.error(request, "Veuillez corriger les erreurs ci-dessous.")
    return redirect('core:product_detail', slug=product.slug)

@login_required
def payment_processing(request, payment_id):
    """
    Affiche la page de traitement du paiement avec suivi en temps réel
    """
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    
    context = {
        'payment': payment,
        'order': payment.order,
        'polling_interval': 5000,  # Vérifier le statut toutes les 5 secondes
        'max_polling_time': 300000,  # Arrêter après 5 minutes
        'whatsapp_support': settings.WHATSAPP_SUPPORT_NUMBER
    }
    
    return render(request, 'payment/processing.html', context)

@login_required
def check_payment_status(request, payment_id):
    """
    Endpoint AJAX pour vérifier le statut du paiement
    """
    payment = get_object_or_404(Payment, id=payment_id, order__user=request.user)
    
    if payment.status == 'completed':
        return JsonResponse({
            'status': 'completed',
            'redirect_url': reverse('core:order_confirmation', args=[payment.order.order_number])
        })
    
    # Vérifier auprès de PayGateGlobal si le statut a changé
    tx_reference = payment.payment_details.get('tx_reference')
    if tx_reference:
        result = PayGatePayment.check_payment_status(tx_reference)
        
        if result.get('success'):
            # Paiement réussi
            payment.status = 'completed'
            payment.save()
            
            payment.order.payment_status = True
            payment.order.save()
            
            # Envoyer une confirmation
            if settings.WHATSAPP_ENABLED:
                payment.order.send_whatsapp_confirmation()
            
            return JsonResponse({
                'status': 'completed',
                'redirect_url': reverse('core:order_confirmation', args=[payment.order.order_number])
            })
    
    return JsonResponse({'status': 'pending'})

@csrf_exempt
def paygate_callback(request):
    """
    Callback pour les notifications de PayGateGlobal
    """
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Méthode non autorisée'}, status=405)
    
    try:
        data = json.loads(request.body)
        tx_reference = data.get('tx_reference')
        identifier = data.get('identifier')  # Numéro de commande
        status = data.get('status')
        
        if not tx_reference or not identifier:
            return JsonResponse({'status': 'error', 'message': 'Paramètres manquants'}, status=400)
        
        try:
            order = Order.objects.get(order_number=identifier)
            payment = Payment.objects.get(
                order=order,
                transaction_id=tx_reference
            )
            
            if status == 0:  # Paiement réussi
                payment.status = 'completed'
                payment.payment_details['callback_data'] = data
                payment.save()
                
                order.payment_status = True
                order.save()
                
                # Envoyer une confirmation
                if settings.WHATSAPP_ENABLED:
                    order.send_whatsapp_confirmation()
                
                return JsonResponse({'status': 'success'})
            else:
                payment.status = 'failed'
                payment.payment_details['callback_data'] = data
                payment.save()
                
                return JsonResponse({
                    'status': 'error',
                    'message': data.get('message', 'Paiement échoué')
                }, status=400)
                
        except Order.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Commande introuvable'}, status=404)
        except Payment.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Paiement introuvable'}, status=404)
            
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Données JSON invalides'}, status=400)
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
@login_required
def order_confirmation(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'checkout/confirmation.html', {'order': order})

@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'account/orders.html', {'orders': orders})

@login_required
def order_detail(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'account/order_detail.html', {'order': order})

@login_required
def address_list(request):
    addresses = Address.objects.filter(user=request.user)
    return render(request, 'account/addresses.html', {'addresses': addresses})

@login_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request, "Adresse enregistrée avec succès")
            return redirect('account:addresses')
    else:
        form = AddressForm()
    
    return render(request, 'account/address_form.html', {'form': form})

@login_required
def address_update(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Adresse mise à jour avec succès")
            return redirect('account:addresses')
    else:
        form = AddressForm(instance=address)
    
    return render(request, 'account/address_form.html', {'form': form})

@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Adresse supprimée avec succès")
        return redirect('account:addresses')
    
    return render(request, 'account/address_confirm_delete.html', {'address': address})

@login_required
def wishlist_view(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    return render(request, 'account/wishlist.html', {'wishlist': wishlist})

@login_required
@require_POST
def wishlist_add(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    
    WishlistItem.objects.get_or_create(
        wishlist=wishlist,
        product=product
    )
    
    messages.success(request, f"{product.name} a été ajouté à votre liste de souhaits")
    return redirect('products:detail', slug=product.slug)


@login_required
@require_POST
def wishlist_remove(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = get_object_or_404(Wishlist, user=request.user)
    
    WishlistItem.objects.filter(
        wishlist=wishlist,
        product=product
    ).delete()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'status': 'removed'})
    
    messages.success(request, f"{product.name} a été retiré de votre liste de souhaits")
    return redirect('account:wishlist')

@login_required
@require_POST
def finalize_order(request):
    """
    Finalise la commande après soumission du formulaire checkout
    """
    try:
        print("=== DÉBUT FINALIZE_ORDER ===")
        
        # Récupérer le panier de l'utilisateur
        try:
            cart = Cart.objects.get(user=request.user)
            print(f"Panier trouvé: {cart.id}")
        except Cart.DoesNotExist:
            return JsonResponse({
                'status': 'error', 
                'message': 'Votre panier est vide'
            }, status=400)

        if not cart.items.exists():
            return JsonResponse({
                'status': 'error', 
                'message': 'Votre panier est vide'
            }, status=400)

        # Vérifier la disponibilité des produits
        for item in cart.items.all():
            if not item.product.is_available():
                return JsonResponse({
                    'status': 'error',
                    'message': f"{item.product.name} n'est plus disponible"
                }, status=400)
            
            if item.product.stock_quantity and item.quantity > item.product.stock_quantity:
                return JsonResponse({
                    'status': 'error',
                    'message': f"Stock insuffisant pour {item.product.name}"
                }, status=400)

        # Récupérer les données JSON
        try:
            data = json.loads(request.body)
            print("Données reçues:", data)
        except json.JSONDecodeError as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Données invalides'
            }, status=400)

        # Créer l'adresse de livraison
        shipping_address = None
        shipping_address_id = data.get('shipping_address')
        
        print(f"Adresse sélectionnée: {shipping_address_id}")
        
        if shipping_address_id and shipping_address_id != 'new':
            # Utiliser une adresse existante
            try:
                shipping_address = Address.objects.get(
                    id=shipping_address_id, 
                    user=request.user
                )
                print(f"Adresse existante utilisée: {shipping_address.id}")
            except Address.DoesNotExist:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Adresse de livraison non trouvée'
                }, status=400)
        else:
            # Créer une nouvelle adresse
            try:
                # Extraire le nom complet
                full_name = data.get('shipping_full_name', '').strip()
                first_name = full_name
                last_name = ''
                
                if ' ' in full_name:
                    parts = full_name.split(' ', 1)
                    first_name = parts[0]
                    last_name = parts[1] if len(parts) > 1 else ''
                else:
                    first_name = full_name
                    last_name = request.user.last_name or ''
                
                shipping_address = Address.objects.create(
                    user=request.user,
                    first_name=first_name,
                    last_name=last_name,
                    phone=data.get('shipping_phone', ''),
                    address_line1=data.get('shipping_address_line1', ''),
                    address_line2=data.get('shipping_address_line2', ''),
                    city=data.get('shipping_city', ''),
                    state=data.get('shipping_state', ''),
                    postal_code=data.get('shipping_postal_code', ''),
                    country=data.get('shipping_country', 'Togo'),
                    is_default=not Address.objects.filter(user=request.user, is_default=True).exists()
                )
                print(f"Nouvelle adresse créée: {shipping_address.id}")
            except Exception as e:
                print(f"Erreur création adresse: {str(e)}")
                return JsonResponse({
                    'status': 'error',
                    'message': f'Erreur lors de la création de l\'adresse: {str(e)}'
                }, status=500)

        # Créer la commande
        try:
            order = Order.objects.create(
                user=request.user,
                cart=cart,
                shipping_address=shipping_address,
                billing_address=shipping_address,
                subtotal=cart.subtotal,
                coupon_discount=cart.coupon_discount,
                shipping_cost=cart.shipping_cost,
                total=cart.total,
                payment_method=data.get('payment_method', 'mobile_money'),
                payment_status=data.get('payment_method') == 'cash_on_delivery',
                status='confirmed',
                note=data.get('note', '')
            )
            print(f"Commande créée: {order.order_number}")
        except Exception as e:
            print(f"Erreur création commande: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur lors de la création de la commande: {str(e)}'
            }, status=500)

        # Créer les articles de la commande
        try:
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    quantity=cart_item.quantity,
                    price=cart_item.price,
                    total_price=cart_item.total_price
                )
                
                # Mettre à jour le stock
                if cart_item.product.stock_quantity:
                    cart_item.product.stock_quantity -= cart_item.quantity
                    if cart_item.product.stock_quantity <= 0:
                        cart_item.product.in_stock = False
                        cart_item.product.stock_quantity = 0
                    cart_item.product.save()
            
            print("Articles de commande créés et stocks mis à jour")
        except Exception as e:
            print(f"Erreur création articles: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Erreur lors de la création des articles: {str(e)}'
            }, status=500)

        # Utiliser le coupon s'il y en a un
        if cart.coupon:
            try:
                cart.coupon.use_coupon()
                print("Coupon utilisé")
            except Exception as e:
                print(f"Erreur utilisation coupon: {str(e)}")

        # Envoyer le reçu WhatsApp
        try:
            send_whatsapp_receipt(order)
            print("Reçu WhatsApp envoyé")
        except Exception as e:
            print(f"Erreur envoi WhatsApp: {str(e)}")

        # Créer une notification
        try:
            Notification.objects.create(
                user=request.user,
                notification_type='order',
                title='Commande confirmée',
                message=f'Votre commande #{order.order_number} a été confirmée avec succès.',
                related_object_id=order.id,
                related_content_type='order'
            )
            print("Notification créée")
        except Exception as e:
            print(f"Erreur création notification: {str(e)}")

        # Vider le panier
        try:
            cart.items.all().delete()
            cart.coupon = None
            cart.coupon_discount = Decimal('0.00')
            cart.shipping_cost = Decimal('0.00')
            cart.save()
            print("Panier vidé")
        except Exception as e:
            print(f"Erreur vidage panier: {str(e)}")

        print("=== FIN FINALIZE_ORDER - SUCCÈS ===")
        
        return JsonResponse({
            'status': 'success',
            'message': 'Commande créée avec succès',
            'redirect_url': reverse('core:order_confirmation', args=[order.order_number])
        })
        
    except Exception as e:
        print(f"=== ERREUR FINALIZE_ORDER: {str(e)} ===")
        import traceback
        print(traceback.format_exc())
        
        return JsonResponse({
            'status': 'error',
            'message': f'Erreur serveur: {str(e)}'
        }, status=500)


def send_whatsapp_receipt(order):
    """
    Envoie le reçu de commande via WhatsApp
    """
    try:
        from .paygate import send_whatsapp_message
        
        site_settings = SiteSetting.get_default_settings()
        
        # Préparer le message WhatsApp
        items_text = "\n".join([
            f"• {item.product.name} - {item.quantity} × {item.price} FCFA = {item.total_price} FCFA"
            for item in order.items.all()
        ])
        
        message = f"""
✅ COMMANDE CONFIRMÉE #{order.order_number}

🛍️ DÉTAILS DE LA COMMANDE:
{items_text}

💰 SOUS-TOTAL: {order.subtotal} FCFA
🎫 RÉDUCTION: -{order.coupon_discount} FCFA
🚚 FRAIS DE LIVRAISON: {order.shipping_cost} FCFA
💳 TOTAL: {order.total} FCFA

📦 LIVRAISON:
{order.shipping_address.first_name} {order.shipping_address.last_name}
{order.shipping_address.phone}
{order.shipping_address.address_line1}
{order.shipping_address.address_line2 + ', ' if order.shipping_address.address_line2 else ''}
{order.shipping_address.city}, {order.shipping_address.postal_code}
{order.shipping_address.country}

📝 NOTES: {order.note if order.note else 'Aucune note'}

⏰ DATE: {order.created_at.strftime('%d/%m/%Y à %H:%M')}

Merci pour votre confiance ! Nous traitons votre commande dans les plus brefs délais.

Pour toute question, contactez-nous au {site_settings.phone}
        """.strip()
        
        # Envoyer le message WhatsApp
        success = send_whatsapp_message(
            phone=order.shipping_address.phone,
            message=message
        )
        
        if success:
            order.whatsapp_confirmation_sent = True
            order.save()
            
            # Envoyer également une copie à l'admin
            admin_message = f"📦 NOUVELLE COMMANDE #{order.order_number}\nTotal: {order.total} FCFA\nClient: {order.shipping_address.first_name} {order.shipping_address.last_name}"
            send_whatsapp_message(
                phone=site_settings.whatsapp_phone,
                message=admin_message
            )
            
        return success
        
    except Exception as e:
        print(f"Erreur envoi WhatsApp: {str(e)}")
        return False

# Mettre à jour la vue checkout_view pour utiliser la nouvelle logique
@login_required
def checkout_view(request):
    cart = get_object_or_404(Cart, user=request.user)
    
    if not cart.items.exists():
        messages.warning(request, "Votre panier est vide")
        return redirect('core:cart_view')
    
    # Vérifications de stock...
    for item in cart.items.all():
        if not item.product.is_available():
            messages.error(request, f"{item.product.name} n'est plus disponible")
            return redirect('core:cart_view')
        if item.product.stock_quantity and item.quantity > item.product.stock_quantity:
            messages.error(request, f"Stock insuffisant pour {item.product.name}")
            return redirect('core:cart_view')
    
    addresses = Address.objects.filter(user=request.user)
    shipping_methods = ShippingMethod.objects.filter(is_active=True)
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST, user=request.user)
        if form.is_valid():
            # Pour les paiements mobiles, utiliser PayGate
            if form.cleaned_data['payment_method'] == 'mobile_money':
                # Logique PayGate existante...
                phone_number = form.cleaned_data['mobile_money_phone']
                network = form.cleaned_data['mobile_money_network']
                
                # Sauvegarder les données temporaires en session
                request.session['checkout_data'] = {
                    'shipping_address_id': form.cleaned_data.get('shipping_address'),
                    'shipping_first_name': form.cleaned_data.get('shipping_first_name'),
                    'shipping_last_name': form.cleaned_data.get('shipping_last_name'),
                    'shipping_phone': form.cleaned_data.get('shipping_phone'),
                    'shipping_address_line1': form.cleaned_data.get('shipping_address_line1'),
                    'shipping_address_line2': form.cleaned_data.get('shipping_address_line2'),
                    'shipping_city': form.cleaned_data.get('shipping_city'),
                    'shipping_postal_code': form.cleaned_data.get('shipping_postal_code'),
                    'shipping_country': form.cleaned_data.get('shipping_country'),
                    'payment_method': form.cleaned_data['payment_method'],
                    'note': form.cleaned_data.get('note', '')
                }
                
                success, result = PayGatePayment.initiate_payment(cart, phone_number, network)
                
                if success:
                    payment = result
                    return redirect('core:payment_processing', payment_id=payment.id)
                else:
                    messages.error(request, f"Erreur de paiement: {result}")
                    return redirect('core:checkout')
            
            # Pour les autres méthodes de paiement, créer la commande directement
            else:
                return finalize_order_direct(request, form)
    else:
        form = CheckoutForm(user=request.user)
    
    context = {
        'cart': cart,
        'addresses': addresses,
        'shipping_methods': shipping_methods,
        'form': form,
    }
    
    return render(request, 'checkout/checkout.html', context)
    

def finalize_order_direct(request, form):
    """
    Crée la commande directement pour les méthodes de paiement non-mobiles
    """
    try:
        cart = get_object_or_404(Cart, user=request.user)
        
        # Créer l'adresse
        shipping_address = None
        if form.cleaned_data.get('shipping_address'):
            shipping_address = form.cleaned_data['shipping_address']
        else:
            shipping_address = Address.objects.create(
                user=request.user,
                first_name=form.cleaned_data['shipping_first_name'],
                last_name=form.cleaned_data['shipping_last_name'],
                phone=form.cleaned_data['shipping_phone'],
                address_line1=form.cleaned_data['shipping_address_line1'],
                address_line2=form.cleaned_data.get('shipping_address_line2', ''),
                city=form.cleaned_data['shipping_city'],
                postal_code=form.cleaned_data['shipping_postal_code'],
                country=form.cleaned_data.get('shipping_country', 'Togo'),
                is_default=not Address.objects.filter(user=request.user, is_default=True).exists()
            )
        
        # Créer la commande
        order = Order.objects.create(
            user=request.user,
            cart=cart,
            shipping_address=shipping_address,
            billing_address=shipping_address,
            subtotal=cart.subtotal,
            coupon_discount=cart.coupon_discount,
            shipping_cost=cart.shipping_cost,
            total=cart.total,
            payment_method=form.cleaned_data['payment_method'],
            payment_status=form.cleaned_data['payment_method'] == 'cash_on_delivery',  # Paiement à la livraison
            status='confirmed',
            note=form.cleaned_data.get('note', '')
        )
        
        # Créer les articles et mettre à jour le stock
        for cart_item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=cart_item.product,
                quantity=cart_item.quantity,
                price=cart_item.price,
                total_price=cart_item.total_price
            )
            
            if cart_item.product.stock_quantity:
                cart_item.product.stock_quantity -= cart_item.quantity
                if cart_item.product.stock_quantity <= 0:
                    cart_item.product.in_stock = False
                cart_item.product.save()
        
        # Utiliser le coupon
        if cart.coupon:
            cart.coupon.use_coupon()
        
        # Envoyer WhatsApp
        send_whatsapp_receipt(order)
        
        # Vider le panier
        cart.items.all().delete()
        cart.coupon = None
        cart.coupon_discount = Decimal('0.00')
        cart.shipping_cost = Decimal('0.00')
        cart.save()
        
        messages.success(request, f"Commande #{order.order_number} créée avec succès!")
        return redirect('core:order_confirmation', order_number=order.order_number)
        
    except Exception as e:
        messages.error(request, f"Erreur lors de la création de la commande: {str(e)}")

        return redirect('core:checkout')

@login_required
def order_confirmation(request, order_number):
    """Affiche la page de confirmation de commande"""
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    return render(request, 'checkout/confirmation.html', {'order': order})

def contact_view(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Envoyer l'email
            messages.success(request, "Votre message a été envoyé avec succès!")
            return redirect('contact')
    else:
        form = ContactForm()
    
    return render(request, 'contact.html', {'form': form})

def newsletter_subscribe(request):
    if request.method == 'POST':
        form = NewsletterSubscriptionForm(request.POST)
        if form.is_valid():
            # Enregistrer l'abonnement
            messages.success(request, "Merci pour votre abonnement à notre newsletter!")
            return redirect('home')
    else:
        form = NewsletterSubscriptionForm()
    
    return render(request, 'newsletter_subscribe.html', {'form': form})

def about_view(request):
    return render(request, 'about.html')

def terms_view(request):
    return render(request, 'terms.html')

def privacy_view(request):
    return render(request, 'privacy.html')

def faq_view(request):
    return render(request, 'faq.html')
