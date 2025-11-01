from django import forms
from django.core.validators import RegexValidator
from .models import ProductReview, Address, Order
from django_countries.fields import CountryField
from django_countries import countries

class ProductReviewForm(forms.ModelForm):
    RATING_CHOICES = [
        (1, '1 - Très mauvais'),
        (2, '2 - Mauvais'),
        (3, '3 - Moyen'),
        (4, '4 - Bon'),
        (5, '5 - Excellent'),
    ]
    
    rating = forms.ChoiceField(
        choices=RATING_CHOICES,
        widget=forms.RadioSelect,
        label='Note'
    )
    title = forms.CharField(
        max_length=100,
        label='Titre',
        widget=forms.TextInput(attrs={'placeholder': 'Donnez un titre à votre avis'})
    )
    comment = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Décrivez votre expérience avec ce produit...'
        }),
        label='Commentaire'
    )

    class Meta:
        model = ProductReview
        fields = ['rating', 'title', 'comment']

    def clean_rating(self):
        rating = self.cleaned_data.get('rating')
        if not rating:
            raise forms.ValidationError("Veuillez sélectionner une note")
        return int(rating)

class AddressForm(forms.ModelForm):
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Le numéro de téléphone doit être au format: '+22812345678'. Jusqu'à 15 chiffres autorisés."
    )
    
    phone = forms.CharField(
        validators=[phone_regex],
        max_length=17,
        widget=forms.TextInput(attrs={'placeholder': '+22812345678'})
    )
    first_name = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Prénom'})
    )
    last_name = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Nom'})
    )
    address_line1 = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Adresse ligne 1'})
    )
    address_line2 = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Adresse ligne 2 (facultatif)'})
    )
    city = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Ville'})
    )
    state = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Région'})
    )
    postal_code = forms.CharField(
        widget=forms.TextInput(attrs={'placeholder': 'Code postal'})
    )
    country = forms.ChoiceField(
        choices=countries,
        initial='TG',
        widget=forms.Select()
    )
    is_default = forms.BooleanField(
        required=False,
        label='Définir comme adresse par défaut'
    )

    class Meta:
        model = Address
        fields = [
            'first_name', 'last_name', 'phone',
            'address_line1', 'address_line2',
            'city', 'state', 'postal_code', 'country',
            'is_default'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['country'].label = 'Pays'

class CheckoutForm(forms.Form):
    PAYMENT_METHOD_CHOICES = [
        ('mobile_money', 'Mobile Money'),
        ('credit_card', 'Carte de crédit'),
        ('cash', 'Paiement à la livraison'),
        ('bank_transfer', 'Virement bancaire'),
    ]
    
    shipping_address = forms.ModelChoiceField(
        queryset=None,
        label="Adresse de livraison",
        widget=forms.RadioSelect,
        empty_label=None
    )
    billing_address = forms.ModelChoiceField(
        queryset=None,
        label="Adresse de facturation",
        widget=forms.RadioSelect,
        empty_label=None,
        required=False
    )
    same_billing_address = forms.BooleanField(
        required=False,
        initial=True,
        label="Utiliser la même adresse pour la facturation"
    )
    payment_method = forms.ChoiceField(
        choices=PAYMENT_METHOD_CHOICES,
        widget=forms.RadioSelect,
        label="Méthode de paiement"
    )
    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'rows': 3,
            'placeholder': 'Notes supplémentaires (facultatif)'
        }),
        label="Note pour la commande"
    )

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            addresses = Address.objects.filter(user=user)
            self.fields['shipping_address'].queryset = addresses
            self.fields['billing_address'].queryset = addresses

    def clean(self):
        cleaned_data = super().clean()
        same_billing_address = cleaned_data.get('same_billing_address')
        
        if not same_billing_address and not cleaned_data.get('billing_address'):
            self.add_error('billing_address', "Veuillez sélectionner une adresse de facturation")
        
        return cleaned_data

    def clean_shipping_address(self):
        shipping_address = self.cleaned_data.get('shipping_address')
        if not shipping_address:
            raise forms.ValidationError("Veuillez sélectionner une adresse de livraison")
        return shipping_address

class NewsletterSubscriptionForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Votre adresse email',
            'class': 'form-control'
        }),
        label="Email"
    )
    agree_to_terms = forms.BooleanField(
        required=True,
        label="J'accepte de recevoir des newsletters et des offres promotionnelles"
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        # Ici, vous pourriez ajouter une validation supplémentaire
        # comme vérifier si l'email est déjà inscrit
        return email

class ContactForm(forms.Form):
    name = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Votre nom'}),
        label="Nom"
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Votre email'}),
        label="Email"
    )
    subject = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Sujet'}),
        label="Sujet"
    )
    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5,
            'placeholder': 'Votre message...'
        }),
        label="Message"
    )
    copy_to_sender = forms.BooleanField(
        required=False,
        label="Recevoir une copie du message"
    )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 2:
            raise forms.ValidationError("Veuillez entrer un nom valide")
        return name

    def clean_message(self):
        message = self.cleaned_data.get('message')
        if len(message) < 10:
            raise forms.ValidationError("Votre message est trop court")
        return message