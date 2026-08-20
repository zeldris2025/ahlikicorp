from rest_framework import serializers
from .models import Brand, Category, Product, ProductImage

class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ('id', 'image', 'alt_text')

class ProductSerializer(serializers.ModelSerializer):
    gallery = ProductImageSerializer(many=True, read_only=True)
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)

    class Meta:
        model = Product
        fields = ('id', 'name', 'slug', 'sku', 'brand', 'brand_name', 'category', 'category_name',
                  'description', 'image', 'gallery', 'is_exclusive', 'is_active', 'stock_quantity',
                  'cost_price', 'specifications', 'created_at')
        read_only_fields = ('id', 'created_at', 'slug')

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')

class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ('id', 'name', 'slug', 'tagline', 'description', 'accent_color', 'logo')
