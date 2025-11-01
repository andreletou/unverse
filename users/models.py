# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django_countries.fields import CountryField

class CustomUser(AbstractUser):
    # Désactiver le username par défaut puisque nous utilisons email
    username = None
    
    # Champs de base étendus
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(_('phone number'), max_length=20, blank=True)
    birth_date = models.DateField(_('birth date'), null=True, blank=True)
    
    # Adresse par défaut
    default_shipping_address = models.ForeignKey(
        'universepro.Address',
        related_name='+',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    default_billing_address = models.ForeignKey(
        'universepro.Address',
        related_name='+',
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    
    # Préférences utilisateur
    language = models.CharField(
        max_length=10,
        choices=settings.LANGUAGES,
        default='fr'
    )
    receive_newsletter = models.BooleanField(default=True)
    receive_promotions = models.BooleanField(default=True)
    
    # Métadonnées
    date_joined = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def get_default_shipping_address(self):
        """Retourne l'adresse de livraison par défaut"""
        return self.default_shipping_address

    def get_default_billing_address(self):
        """Retourne l'adresse de facturation par défaut"""
        return self.default_billing_address


class Address(models.Model):
    """
    Modèle d'adresse lié à l'utilisateur
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='addresses'
    )
    street_address = models.CharField(_('street address'), max_length=100)
    apartment_address = models.CharField(_('apartment address'), max_length=100, blank=True)
    country = CountryField()
    zip_code = models.CharField(_('zip code'), max_length=20)
    city = models.CharField(_('city'), max_length=50)
    phone = models.CharField(_('phone number'), max_length=20)
    default = models.BooleanField(_('default address'), default=False)
    address_type = models.CharField(
        max_length=10,
        choices=(
            ('S', _('Shipping')),
            ('B', _('Billing')),
            ('SB', _('Shipping & Billing'))
        ),
        verbose_name=_('address type')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')
        ordering = ['-default', '-updated_at']

    def __str__(self):
        return f"{self.street_address}, {self.city}, {self.country}"

    def set_default(self):
        """Définit cette adresse comme adresse par défaut pour son type"""
        Address.objects.filter(
            user=self.user,
            address_type=self.address_type
        ).update(default=False)
        self.default = True
        self.save()