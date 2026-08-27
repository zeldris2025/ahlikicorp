from django import forms
from .models import Product, Brand, Category, ExclusiveBrand

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
    accidentally create two products that collide on URL. SKU is auto-generated
    from the name. Brand is always Ah Liki Wholesale.
    """

    class Meta:
        model = Product
        fields = (
            'name', 'brand', 'category', 'description',
            'image', 'cost_price', 'stock_quantity',
            'is_exclusive', 'is_active', 'specifications',
        )
        widgets = {
            'name': forms.TextInput(attrs={'class': 'f-input', 'placeholder': 'e.g. Long Grain White Rice 25kg Sack'}),
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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from products.views import ProductListView
        self.fields['brand'].queryset = Brand.objects.filter(slug=ProductListView.CATALOGUE_BRAND_SLUG)
        self.fields['brand'].initial = Brand.objects.filter(slug=ProductListView.CATALOGUE_BRAND_SLUG).first()
        self.fields['brand'].disabled = True

    def clean_name(self):
        name = self.cleaned_data.get('name', '').strip()
        if not name:
            raise forms.ValidationError('Product name is required.')
        return name

    def save(self, commit=True):
        product = super().save(commit=False)
        product.name = product.name.strip()

        if not product.slug:
            from django.utils.text import slugify
            base = slugify(product.name)[:45] or 'product'
            slug, n = base, 2
            existing = Product.objects.exclude(pk=product.pk)
            while existing.filter(slug=slug).exists():
                slug = f'{base}-{n}'
                n += 1
            product.slug = slug

        if not product.sku:
            from django.utils.text import slugify
            base = slugify(product.name).upper()[:20]
            if not base:
                base = 'PRODUCT'
            sku, n = base, 2
            existing = Product.objects.exclude(pk=product.pk)
            while existing.filter(sku__iexact=sku).exists():
                sku = f'{base}-{n}'
                n += 1
            product.sku = sku

        if commit:
            product.save()
        return product


class ProductBulkUploadForm(forms.Form):
    """CSV file upload for bulk product creation.

    CSV format (header row required):
    name,category,description,cost_price,stock_quantity,is_exclusive,specifications

    The SKU and slug are auto-generated from the name. Brand is always
    Ah Liki Wholesale.
    """

    csv_file = forms.FileField(
        label='CSV File',
        help_text='Upload a CSV file with columns: name, category, description, cost_price, stock_quantity, is_exclusive, specifications',
        widget=forms.FileInput(attrs={'class': 'f-input', 'accept': '.csv'})
    )

    def clean_csv_file(self):
        file = self.cleaned_data.get('csv_file')
        if file:
            if not file.name.endswith('.csv'):
                raise forms.ValidationError('Please upload a CSV file.')
        return file


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


class ExclusiveBrandForm(forms.ModelForm):
    """Logo of a brand we distribute exclusively, for the home page marquee."""

    class Meta:
        model = ExclusiveBrand
        fields = ('name', 'logo', 'website', 'note', 'sort_order', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={'class': 'f-input', 'placeholder': 'e.g. Vailima'}),
            'logo': forms.FileInput(attrs={'class': 'f-input', 'accept': 'image/*'}),
            'website': forms.URLInput(attrs={'class': 'f-input', 'placeholder': 'https://…'}),
            'note': forms.TextInput(attrs={'class': 'f-input', 'placeholder': 'e.g. Beverages'}),
            'sort_order': forms.NumberInput(attrs={'class': 'f-input', 'min': '0'}),
        }
        labels = {
            'note': 'Caption',
            'sort_order': 'Order',
            'is_active': 'Show on the home page',
        }
        help_texts = {
            'logo': 'A PNG with a transparent background works best. It is scaled to fit the card.',
            'website': 'Optional. Makes the logo a link to the brand.',
            'note': 'Optional small label under the logo.',
            'sort_order': 'Lowest number shows first.',
        }
