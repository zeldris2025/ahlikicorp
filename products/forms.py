from django import forms
from .models import Product, Brand, Category

class ProductSearchForm(forms.Form):
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border border-gray-300 rounded-lg',
            'placeholder': 'Search products...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label='All Categories',
        widget=forms.Select(attrs={'class': 'px-4 py-2 border border-gray-300 rounded-lg'})
    )
    is_exclusive = forms.BooleanField(required=False, label='Exclusive Items Only')
