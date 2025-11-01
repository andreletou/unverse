from django.contrib import admin
from django.utils.html import format_html
from .models import *

# SiteSetting Admin
@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'email', 'phone', 'currency', 'is_maintenance_mode')
    list_editable = ('is_maintenance_mode',)
    fieldsets = (
        ('Informations de base', {
            'fields': ('site_name', 'site_logo', 'favicon')
        }),
        ('Coordonnées', {
            'fields': ('email', 'phone', 'address')
        }),
        ('Réseaux sociaux', {
            'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'whatsapp_phone', 'whatsapp_message')
        }),
        ('Paramètres e-commerce', {
            'fields': ('currency', 'currency_symbol', 'free_shipping_threshold', 'default_shipping_cost')
        }),
        ('Maintenance', {
            'fields': ('is_maintenance_mode', 'maintenance_message')
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords')
        }),
    )

    def has_add_permission(self, request):
        # Permettre seulement une instance de SiteSetting
        return not SiteSetting.objects.exists()

# Category Admin
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent', 'is_active', 'created_at')
    list_filter = ('is_active', 'parent')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(Category, CategoryAdmin)

# Product Admin
class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'alt_text', 'is_featured', 'order')

class ProductFeatureInline(admin.TabularInline):
    model = ProductFeature
    extra = 1

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'price', 'original_price', 'in_stock', 'stock_quantity', 'rating', 'is_active', 'featured')
    list_filter = ('category', 'is_active', 'featured', 'in_stock')
    search_fields = ('name', 'description', 'sku')
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ('price', 'original_price', 'in_stock', 'stock_quantity', 'is_active', 'featured')
    readonly_fields = ('created_at', 'updated_at', 'rating', 'reviews_count')
    inlines = [ProductImageInline, ProductFeatureInline]
    fieldsets = (
        (None, {
            'fields': ('name', 'slug', 'category', 'sku')
        }),
        ('Prix et stock', {
            'fields': ('price', 'original_price', 'in_stock', 'stock_quantity')
        }),
        ('Détails', {
            'fields': ('description', 'short_description', 'colors', 'weight', 'dimensions')
        }),
        ('Évaluations', {
            'fields': ('rating', 'reviews_count')
        }),
        ('Statut', {
            'fields': ('featured', 'is_active')
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

# ProductImage Admin
@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ('product', 'image_preview', 'is_featured', 'order')
    list_editable = ('is_featured', 'order')
    list_filter = ('is_featured', 'product__category')
    search_fields = ('product__name', 'alt_text')

    def image_preview(self, obj):
        return format_html('<img src="{}" height="50" />', obj.image.url) if obj.image else "-"
    image_preview.short_description = 'Preview'

# ProductReview Admin
@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display = ('product', 'user', 'rating', 'title', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_approved', 'product__category')
    search_fields = ('product__name', 'user__username', 'title', 'comment')
    list_editable = ('is_approved',)
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('product', 'user')

# Coupon Admin
@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('code', 'discount_type', 'discount_value', 'valid_from', 'valid_to', 'is_active', 'current_uses', 'max_uses')
    list_filter = ('discount_type', 'is_active')
    search_fields = ('code', 'description')
    list_editable = ('is_active',)
    filter_horizontal = ('categories', 'products')
    readonly_fields = ('current_uses', 'created_at', 'updated_at')
    date_hierarchy = 'valid_from'

# Cart Admin
class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ('added_at', 'updated_at')

@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_key', 'item_count', 'subtotal', 'coupon_discount', 'shipping_cost', 'total', 'created_at')
    list_filter = ('user',)
    search_fields = ('user__username', 'session_key')
    inlines = [CartItemInline]
    readonly_fields = ('created_at', 'updated_at')

    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'

    def subtotal(self, obj):
        return obj.subtotal
    subtotal.admin_order_field = 'subtotal'

    def total(self, obj):
        return obj.total
    total.admin_order_field = 'total'

# Address Admin
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'first_name', 'last_name', 'city', 'state', 'is_default')
    list_filter = ('city', 'state', 'country', 'is_default')
    search_fields = ('user__username', 'first_name', 'last_name', 'city')
    list_editable = ('is_default',)

# Order Admin
class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('created_at',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_number', 'user', 'status', 'payment_status', 'total', 'created_at')
    list_filter = ('status', 'payment_status', 'payment_method', 'created_at')
    search_fields = ('order_number', 'user__username')
    inlines = [OrderItemInline]
    readonly_fields = ('order_number', 'created_at', 'updated_at')
    fieldsets = (
        (None, {
            'fields': ('order_number', 'user', 'cart', 'status')
        }),
        ('Adresses', {
            'fields': ('shipping_address', 'billing_address')
        }),
        ('Paiement', {
            'fields': ('payment_method', 'payment_status')
        }),
        ('Montants', {
            'fields': ('subtotal', 'coupon_discount', 'shipping_cost', 'total')
        }),
        ('Livraison', {
            'fields': ('tracking_number', 'tracking_url', 'whatsapp_confirmation_sent')
        }),
        ('Notes', {
            'fields': ('note',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    actions = ['mark_as_paid', 'mark_as_shipped']

    def mark_as_paid(self, request, queryset):
        queryset.update(payment_status=True)
    mark_as_paid.short_description = "Marquer comme payé"

    def mark_as_shipped(self, request, queryset):
        queryset.update(status='shipped')
    mark_as_shipped.short_description = "Marquer comme expédié"

# Payment Admin
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('order', 'amount', 'method', 'status', 'created_at')
    list_filter = ('method', 'status')
    search_fields = ('order__order_number', 'transaction_id')
    readonly_fields = ('created_at', 'updated_at')
    list_editable = ('status',)

# ShippingMethod Admin
@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'free_shipping_threshold', 'estimated_delivery', 'is_active')
    list_editable = ('price', 'is_active')
    list_filter = ('is_active',)

# Notification Admin
@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read')
    search_fields = ('user__username', 'title', 'message')
    list_editable = ('is_read',)
    readonly_fields = ('created_at',)

# TrendingProduct Admin
@admin.register(TrendingProduct)
class TrendingProductAdmin(admin.ModelAdmin):
    list_display = ('product', 'period', 'rank', 'views', 'clicks', 'date')
    list_filter = ('period', 'date')
    search_fields = ('product__name',)
    list_editable = ('rank',)

# Wishlist Admin
class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0

@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ('user', 'item_count', 'created_at', 'updated_at')
    search_fields = ('user__username',)
    inlines = [WishlistItemInline]
    readonly_fields = ('created_at', 'updated_at')

    def item_count(self, obj):
        return obj.products.count()
    item_count.short_description = 'Items'

# Register remaining models with basic admin
admin.site.register([Favorite, ProductFeature, OrderItem, WishlistItem])