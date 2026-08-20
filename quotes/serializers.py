from rest_framework import serializers
from .models import Quote, QuoteItem
from products.serializers import ProductSerializer

class QuoteItemSerializer(serializers.ModelSerializer):
    product = ProductSerializer(read_only=True)
    product_id = serializers.IntegerField(write_only=True)
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    margin = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = QuoteItem
        fields = ('id', 'product', 'product_id', 'quantity', 'unit_price', 'line_total', 'margin')

class QuoteSerializer(serializers.ModelSerializer):
    items = QuoteItemSerializer(many=True, read_only=True)
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tax_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Quote
        fields = ('id', 'reference', 'customer', 'customer_email', 'customer_name', 'company', 'email', 'phone',
                  'delivery_location', 'delivery_address', 'notes', 'status', 'items', 'tax_rate', 'valid_until',
                  'subtotal', 'tax_total', 'total', 'created_at', 'updated_at')
        read_only_fields = ('id', 'reference', 'created_at', 'updated_at')
