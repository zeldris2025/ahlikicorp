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


class ProductForm(forms.ModelForm):
    """Full product form for the staff portal.

    The slug is derived from the name rather than asked for, so staff cannot
    accidentally create two products that collide on URL.
    """

    class Meta:
        model = Product
        fields = (
            'name', 'sku', 'brand', 'category', 'description',
            'image', 'cost_price', 'stock_quantity',
            'is_exclusive', 'is_active', 'specifications',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'f-input', 'placeholder': 'e.g. Long Grain White Rice 25kg Sack'}),
            'sku': forms.TextInput(attrs={'class': 'f-input', 'placeholder': 'e.g. AW-RICE-25'}),
            'brand': forms.Select(attrs={'class': 'f-input'}),
            'category': forms.Select(attrs={'class': 'f-input'}),
            'description': forms.Textarea(attrs={'class': 'f-input', 'rows': 5}),
            'cost_price': forms.NumberInput(attrs={'class': 'f-input', 'step': '0.01', 'min': '0'}),
            'stock_quantity': forms.NumberInput(attrs={'class': 'f-input', 'min': '0'}),
            'specifications': forms.Textarea(attrs={'class': 'f-input', 'rows': 3,
                                                    'placeholder': '{"Pack size": "25kg sack"}'}),
        }
        help_texts = {
            'cost_price': 'Internal only — never shown to customers.',
            'is_exclusive': 'Adds the Exclusive badge on the catalogue.',
            'is_active': 'Untick to withdraw from the catalogue without deleting.',
            'specifications': 'Optional. JSON object of label/value pairs.',
        }

    def clean_sku(self):
        sku = (self.cleaned_data.get('sku') or '').strip().upper()
        clash = Product.objects.filter(sku__iexact=sku)
        if self.instance.pk:
            clash = clash.exclude(pk=self.instance.pk)
        if clash.exists():
            raise forms.ValidationError('Another product already uses this SKU.')
        return sku

    def save(self, commit=True):
        product = super().save(commit=False)
        if not product.slug:
            from django.utils.text import slugify
            base = slugify(product.name)[:45] or 'product'
            slug, n = base, 2
            existing = Product.objects.exclude(pk=product.pk)
            while existing.filter(slug=slug).exists():
                slug = f'{base}-{n}'
                n += 1
            product.slug = slug
        if commit:
            product.save()
        return product


class CategoryForm(forms.ModelForm):
    class Meta:
        model = Category
        fields = ('name',)
        widgets = {'name': forms.TextInput(attrs={'class': 'f-input', 'placeholder': 'e.g. Frozen Goods'})}

    def save(self, commit=True):
        category = super().save(commit=False)
        if not category.slug:
            from django.utils.text import slugify
            category.slug = slugify(category.name)
        if commit:
            category.save()
        return category
