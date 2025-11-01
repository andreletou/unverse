from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from decimal import Decimal

# universepro/models.py
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

class SiteSetting(models.Model):
    # Informations de base
    site_name = models.CharField(_('site name'), max_length=100, default='Universepro')
    site_logo = models.ImageField(_('site logo'), upload_to='site/', blank=True)
    favicon = models.ImageField(_('favicon'), upload_to='site/', blank=True)
    
    # Coordonnées
    email = models.EmailField(_('email'), default='contact@universepro.com')
    phone = models.CharField(_('phone'), max_length=20, default='+22893020525')
    address = models.TextField(_('address'), blank=True)
    
    # Réseaux sociaux
    facebook_url = models.URLField(_('facebook url'), blank=True)
    twitter_url = models.URLField(_('twitter url'), blank=True)
    instagram_url = models.URLField(_('instagram url'), blank=True)
    whatsapp_phone = models.CharField(_('whatsapp phone'), max_length=20, default='+22893020525')
    whatsapp_message = models.TextField(
        _('whatsapp default message'),
        default="Bonjour, j'ai une question sur votre boutique en ligne."
    )
    
    # Paramètres e-commerce
    currency = models.CharField(_('currency'), max_length=10, default='FCFA')
    currency_symbol = models.CharField(_('currency symbol'), max_length=3, default='F')
    free_shipping_threshold = models.DecimalField(
        _('free shipping threshold'),
        max_digits=10,
        decimal_places=2,
        default=100000.00
    )
    default_shipping_cost = models.DecimalField(
        _('default shipping cost'),
        max_digits=10,
        decimal_places=2,
        default=5000.00
    )
    
    # Maintenance
    is_maintenance_mode = models.BooleanField(_('maintenance mode'), default=False)
    maintenance_message = models.TextField(_('maintenance message'), blank=True)
    
    # SEO
    meta_title = models.CharField(_('meta title'), max_length=200, blank=True)
    meta_description = models.TextField(_('meta description'), blank=True)
    meta_keywords = models.TextField(_('meta keywords'), blank=True)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('site setting')
        verbose_name_plural = _('site settings')
        
    def __str__(self):
        return self.site_name

    @classmethod
    def get_default_settings(cls):
        """Retourne les paramètres par défaut ou crée une nouvelle instance si elle n'existe pas"""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings

class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    icon = models.CharField(max_length=50, blank=True, null=True)  # Pour les icônes FontAwesome

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f'/category/{self.slug}/'


class Product(models.Model):
    COLOR_CHOICES = [
        ('Noir', 'Noir'),
        ('Blanc', 'Blanc'),
        ('Rouge', 'Rouge'),
        ('Bleu', 'Bleu'),
        ('Vert', 'Vert'),
        ('Jaune', 'Jaune'),
        ('Rose', 'Rose'),
        ('Gris', 'Gris'),
        ('Argent', 'Argent'),
        ('Or', 'Or'),
        ('Autre', 'Autre'),
    ]

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=160, blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    original_price = models.DecimalField(
        max_digits=12, decimal_places=2, 
        validators=[MinValueValidator(0)], 
        null=True, blank=True
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    rating = models.FloatField(
        default=0, 
        validators=[MinValueValidator(0), MaxValueValidator(5)]
    )
    reviews_count = models.PositiveIntegerField(default=0)
    in_stock = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    sku = models.CharField(max_length=50, unique=True, blank=True, null=True)
    colors = models.JSONField(default=list)  # Liste des couleurs disponibles
    featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    weight = models.DecimalField(max_digits=6, decimal_places=2, default=0)  # en grammes
    dimensions = models.CharField(max_length=50, blank=True)  # "L x l x H" en cm

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if not self.sku:
            # Générer un SKU unique basé sur l'ID et le nom
            self.sku = f"{slugify(self.name[:5]).upper()}-{Product.objects.count() + 1}"
        
        # Si original_price n'est pas défini, le définir comme égal à price
        if self.original_price is None:
            self.original_price = self.price
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f'/product/{self.slug}/'

    def get_discount_percentage(self):
        if self.original_price and self.original_price > self.price:
            return round((1 - (self.price / self.original_price)) * 100)
        return 0

    def is_on_sale(self):
        return self.original_price and self.original_price > self.price

    def is_available(self):
        return self.in_stock and (self.stock_quantity > 0 if self.stock_quantity is not None else True)
    
    def update_average_rating(self):
        """Met à jour la note moyenne et le nombre d'avis"""
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            self.rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.reviews_count = reviews.count()
            self.save(update_fields=['rating', 'reviews_count'])


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=100, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.product.name}"


class ProductFeature(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='features')
    name = models.CharField(max_length=100)
    value = models.CharField(max_length=255, blank=True)
    icon = models.CharField(max_length=50, blank=True)  # Pour les icônes FontAwesome

    def __str__(self):
        return f"{self.name}: {self.value}"


class ProductReview(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='reviews')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    title = models.CharField(max_length=100)
    comment = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_approved = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['product', 'user']  # Un utilisateur ne peut donner qu'un avis par produit

    def __str__(self):
        return f"Review by {self.user.username} for {self.product.name}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mettre à jour la note moyenne du produit
        reviews = ProductReview.objects.filter(product=self.product, is_approved=True)
        if reviews.exists():
            self.product.rating = reviews.aggregate(models.Avg('rating'))['rating__avg']
            self.product.reviews_count = reviews.count()
            self.product.save()


class Favorite(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'product']  # Un produit ne peut être ajouté qu'une fois aux favoris

    def __str__(self):
        return f"{self.user.username} - {self.product.name}"


class Coupon(models.Model):
    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Pourcentage'),
        ('fixed', 'Montant fixe'),
        ('free_shipping', 'Livraison gratuite'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    min_order_amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)], default=0)
    max_discount_amount = models.DecimalField(
        max_digits=12, decimal_places=2, 
        validators=[MinValueValidator(0)], 
        null=True, blank=True
    )
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    max_uses = models.PositiveIntegerField(default=1)
    current_uses = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    categories = models.ManyToManyField(Category, blank=True)
    products = models.ManyToManyField(Product, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.code

    def is_valid(self, user=None, cart=None):
        now = timezone.now()
        if not self.is_active:
            return False
        if now < self.valid_from or now > self.valid_to:
            return False
        if self.current_uses >= self.max_uses:
            return False
        
        # Vérifier si le coupon est applicable au panier
        if cart:
            # Vérifier le montant minimum de la commande
            if cart.subtotal < self.min_order_amount:
                return False
            
            # Vérifier les catégories ou produits spécifiques
            if self.categories.exists() or self.products.exists():
                valid_items = False
                for item in cart.items.all():
                    if self.products.filter(id=item.product.id).exists():
                        valid_items = True
                        break
                    if self.categories.filter(id=item.product.category.id).exists():
                        valid_items = True
                        break
                if not valid_items:
                    return False
        
        return True

    def calculate_discount(self, amount):
        if not self.is_valid():
            return Decimal('0.00')
        
        if self.discount_type == 'percentage':
            discount = amount * (self.discount_value / Decimal('100.00'))
            if self.max_discount_amount and discount > self.max_discount_amount:
                return self.max_discount_amount
            return discount
        elif self.discount_type == 'fixed':
            return min(self.discount_value, amount)
        elif self.discount_type == 'free_shipping':
            return Decimal('0.00')  # Le calcul de la livraison se fera ailleurs
        
        return Decimal('0.00')

    def use_coupon(self):
        if self.current_uses < self.max_uses:
            self.current_uses += 1
            if self.current_uses >= self.max_uses:
                self.is_active = False
            self.save()


class Cart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='carts', null=True, blank=True)
    session_key = models.CharField(max_length=40, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    coupon_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    shipping_method = models.CharField(max_length=50, blank=True, null=True)
    note = models.TextField(blank=True)

    class Meta:
        unique_together = ['user', 'session_key']

    def __str__(self):
        if self.user:
            return f"Panier de {self.user.username}"
        return f"Panier session {self.session_key}"

    @property
    def subtotal(self):
        return sum(item.total_price for item in self.items.all())

    @property
    def total(self):
        total = self.subtotal - self.coupon_discount + self.shipping_cost
        return max(total, Decimal('0.00'))

    def apply_coupon(self, coupon_code):
        try:
            coupon = Coupon.objects.get(code=coupon_code, is_active=True)
            if coupon.is_valid(cart=self):
                self.coupon = coupon
                self.coupon_discount = coupon.calculate_discount(self.subtotal)
                self.save()
                return True
        except Coupon.DoesNotExist:
            pass
        return False

    def clear_coupon(self):
        self.coupon = None
        self.coupon_discount = 0
        self.save()

    def calculate_shipping(self, address=None):
        # Logique de calcul des frais de livraison
        # Pourrait être basée sur le poids, la destination, etc.
        free_shipping_threshold = Decimal('100000.00')  # 100 000 FCFA
        base_shipping_cost = Decimal('5000.00')  # 5 000 FCFA
        
        if self.subtotal >= free_shipping_threshold:
            self.shipping_cost = Decimal('0.00')
        else:
            self.shipping_cost = base_shipping_cost
        
        self.save()
        return self.shipping_cost

    def merge_with_session_cart(self, session_cart):
        # Fusionner deux paniers (utilisé lorsqu'un utilisateur se connecte)
        for session_item in session_cart.items.all():
            item, created = self.items.get_or_create(
                product=session_item.product,
                defaults={'quantity': session_item.quantity}
            )
            if not created:
                item.quantity += session_item.quantity
                item.save()
        session_cart.delete()


class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1, validators=[MinValueValidator(1)])
    price = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['cart', 'product']

    def __str__(self):
        return f"{self.quantity} x {self.product.name}"

    @property
    def total_price(self):
        return self.price * self.quantity

    def save(self, *args, **kwargs):
        # S'assurer que le prix est toujours celui du produit
        if not self.price or self.price != self.product.price:
            self.price = self.product.price
        super().save(*args, **kwargs)

    def clean(self):
        if not self.product.is_available():
            raise ValidationError("Ce produit n'est pas disponible")
        if self.product.stock_quantity and self.quantity > self.product.stock_quantity:
            raise ValidationError("Quantité demandée supérieure au stock disponible")


class Address(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="Togo")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Addresses"

    def __str__(self):
        return f"{self.first_name} {self.last_name}, {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # S'assurer qu'il n'y a qu'une seule adresse par défaut
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def get_full_address(self):
        return f"{self.address_line1}\n{self.address_line2}\n{self.city}, {self.state}\n{self.postal_code}, {self.country}"


class Order(models.Model):
    PAYMENT_METHOD_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('credit_card', 'Carte de crédit'),
        ('cash', 'Paiement à la livraison'),
        ('bank_transfer', 'Virement bancaire'),
    ]

    ORDER_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('confirmed', 'Confirmé'),
        ('processing', 'En traitement'),
        ('shipped', 'Expédié'),
        ('delivered', 'Livré'),
        ('cancelled', 'Annulé'),
        ('refunded', 'Remboursé'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='orders')
    order_number = models.CharField(max_length=20, unique=True)
    cart = models.OneToOneField(Cart, on_delete=models.PROTECT)
    shipping_address = models.ForeignKey(
        Address, 
        on_delete=models.PROTECT, 
        related_name='shipping_orders',
        null=True, blank=True
    )
    billing_address = models.ForeignKey(
        Address, 
        on_delete=models.PROTECT, 
        related_name='billing_orders',
        null=True, blank=True
    )
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    coupon_discount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    shipping_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    payment_status = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default='pending')
    note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    whatsapp_confirmation_sent = models.BooleanField(default=False)
    tracking_number = models.CharField(max_length=50, blank=True)
    tracking_url = models.URLField(blank=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Commande #{self.order_number}"
    
    

    def save(self, *args, **kwargs):
        if not self.order_number:
            # Générer un numéro de commande unique
            prefix = "CMD"
            last_order = Order.objects.order_by('-id').first()
            last_id = last_order.id if last_order else 0
            self.order_number = f"{prefix}-{last_id + 1:06d}"
        
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return f'/order/{self.order_number}/'

    def get_payment_method_display(self):
        """Retourne l'affichage du mode de paiement"""
        method_display = {
            'mobile_money': 'Mobile Money',
            'credit_card': 'Carte bancaire',
            'cash_on_delivery': 'Paiement à la livraison',
            'bank_transfer': 'Virement bancaire'
        }
        return method_display.get(self.payment_method, self.payment_method)
    def update_status(self, new_status):
        self.status = new_status
        self.save()
        # Ici, vous pourriez ajouter une notification au client

    def cancel_order(self):
        if self.status in ['pending', 'confirmed', 'processing']:
            self.status = 'cancelled'
            self.save()
            # Potentiellement rembourser le paiement et restocker les produits


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=12, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} x {self.product.name} (Commande #{self.order.order_number})"


class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('refunded', 'Remboursé'),
    ]

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=Order.PAYMENT_METHOD_CHOICES)
    transaction_id = models.CharField(max_length=100, blank=True)
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    payment_details = models.JSONField(default=dict)  # Pour stocker des détails spécifiques au mode de paiement

    def __str__(self):
        return f"Paiement de {self.amount} pour la commande #{self.order.order_number}"

    def mark_as_paid(self, transaction_id=None):
        self.status = 'completed'
        if transaction_id:
            self.transaction_id = transaction_id
        self.save()
        self.order.payment_status = True
        self.order.save()

    def mark_as_failed(self):
        self.status = 'failed'
        self.save()

    def refund(self):
        if self.status == 'completed':
            self.status = 'refunded'
            self.save()
            # Logique de remboursement selon le mode de paiement


class ShippingMethod(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    free_shipping_threshold = models.DecimalField(
        max_digits=12, decimal_places=2, 
        null=True, blank=True
    )
    estimated_delivery = models.CharField(max_length=100)  # "2-5 jours"
    is_active = models.BooleanField(default=True)
    regions = models.JSONField(default=list)  # Liste des régions où cette méthode est disponible

    def __str__(self):
        return self.name

    def calculate_cost(self, cart):
        if (self.free_shipping_threshold is not None and 
            cart.subtotal >= self.free_shipping_threshold):
            return Decimal('0.00')
        return self.price


class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('order', 'Commande'),
        ('payment', 'Paiement'),
        ('shipment', 'Livraison'),
        ('promo', 'Promotion'),
        ('account', 'Compte'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=100)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    related_content_type = models.CharField(max_length=50, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Notification pour {self.user.username}: {self.title}"

    def mark_as_read(self):
        self.is_read = True
        self.save()


class TrendingProduct(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    period = models.CharField(max_length=20, choices=[
        ('daily', 'Quotidien'),
        ('weekly', 'Hebdomadaire'),
        ('monthly', 'Mensuel'),
    ])
    rank = models.PositiveIntegerField(default=0)
    views = models.PositiveIntegerField(default=0)
    clicks = models.PositiveIntegerField(default=0)
    date = models.DateField()

    class Meta:
        unique_together = ['product', 'period', 'date']
        ordering = ['period', 'date', 'rank']

    def __str__(self):
        return f"{self.product.name} - {self.get_period_display()} - {self.date}"


class Wishlist(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product, through='WishlistItem')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Liste de souhaits de {self.user.username}"


class WishlistItem(models.Model):
    wishlist = models.ForeignKey(Wishlist, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['wishlist', 'product']

    def __str__(self):
        return f"{self.product.name} dans la liste de {self.wishlist.user.username}"

class PaymentAttempt(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payment_attempts')
    request_data = models.JSONField()
    response_data = models.JSONField()
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='pending')
    
    class Meta:
        ordering = ['-timestamp']


def send_whatsapp_confirmation(self):
    from .paygate import send_whatsapp_message
    
    site_settings = SiteSetting.get_default_settings()
    message = (f"Confirmation de commande #{self.order_number}\n"
              f"Montant: {self.total} {site_settings.currency}\n"
              f"Statut: Paiement confirmé\n\n"
              f"Merci pour votre achat!")
    
    send_whatsapp_message(
        phone=site_settings.whatsapp_phone,
        message=message
    )
    self.whatsapp_confirmation_sent = True
    self.save()