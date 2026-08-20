from django import forms
from django.forms import inlineformset_factory
from .models import Quote, QuoteItem
from core.models import Location
from products.models import Product

class QuoteRequestForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ('customer_name', 'company', 'email', 'phone', 'delivery_location', 'delivery_address', 'notes')
        widgets = {
            'customer_name': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'placeholder': 'Full Name', 'required': True}),
            'company': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'placeholder': 'Company Name'}),
            'email': forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'placeholder': 'Email', 'required': True}),
            'phone': forms.TextInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'placeholder': 'Phone Number', 'required': True}),
            'delivery_location': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg'}),
            'delivery_address': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'rows': 3, 'placeholder': 'Delivery Address (optional)'}),
            'notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'rows': 3, 'placeholder': 'Special notes or requests'}),
        }

class QuoteItemForm(forms.ModelForm):
    product = forms.ModelChoiceField(queryset=Product.objects.filter(is_active=True), widget=forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg'}))

    class Meta:
        model = QuoteItem
        fields = ('product', 'quantity')
        widgets = {
            'quantity': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'min': 1}),
        }

QuoteItemFormSet = inlineformset_factory(Quote, QuoteItem, form=QuoteItemForm, extra=1, can_delete=True)

class QuoteStatusForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ('status', 'internal_notes', 'tax_rate', 'valid_until')
        widgets = {
            'status': forms.Select(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg'}),
            'internal_notes': forms.Textarea(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'rows': 4}),
            'tax_rate': forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'step': '0.01'}),
            'valid_until': forms.DateInput(attrs={'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg', 'type': 'date'}),
        }
