from django.core.management.base import BaseCommand
from django.contrib.auth.models import User, Group, Permission
from django.utils.text import slugify
from core.models import Location, NewsletterSubscriber
from products.models import Brand, Category, Product
from quotes.models import Quote

class Command(BaseCommand):
    help = 'Seed initial data for the application'

    def handle(self, *args, **options):
        self.stdout.write('Starting data seeding...')

        # Create groups and permissions
        self.create_groups()

        # Create locations
        self.create_locations()

        # Create brands
        self.create_brands()

        # Create categories
        self.create_categories()

        # Create demo users
        self.create_demo_users()

        # Create sample products
        self.create_products()

        self.stdout.write(self.style.SUCCESS('✓ Data seeding completed successfully!'))

    def create_groups(self):
        for group_name in ['Customer', 'Finance', 'Admin']:
            group, created = Group.objects.get_or_create(name=group_name)
            if created:
                self.stdout.write(f'Created group: {group_name}')

    def create_locations(self):
        locations_data = [
            {'name': 'Farmer Joe - Fugalei', 'address': 'Fugalei St, Apia', 'island': 'Upolu', 'is_headquarters': False},
            {'name': 'Farmer Joe - Vaitele', 'address': 'Vaitele, Apia', 'island': 'Upolu', 'is_headquarters': False},
            {'name': 'Farmer Joe - Ululoloa', 'address': 'Ululoloa, Apia', 'island': 'Upolu', 'is_headquarters': False},
            {'name': 'Ah Liki Headquarters', 'address': 'Main Office, Apia', 'island': 'Upolu', 'is_headquarters': True},
            {'name': 'Savai\'i Distribution', 'address': 'Savai\'i', 'island': 'Savai\'i', 'is_headquarters': False},
        ]
        for loc_data in locations_data:
            Location.objects.get_or_create(**loc_data)
        self.stdout.write(f'Created {len(locations_data)} locations')

    def create_brands(self):
        brands_data = [
            {'name': 'Ah Liki Samoa Wholesale', 'slug': 'ahliki-wholesale', 'tagline': 'Premium bulk food distribution', 'description': 'Serving the Pacific', 'accent_color': '#1e3a5f'},
            {'name': 'Farmer Joe Supermarket', 'slug': 'farmer-joe', 'tagline': 'Quality products, great prices', 'description': 'Your local supermarket', 'accent_color': '#0e7c86'},
            {'name': 'Taula Beverage Limited', 'slug': 'taula-beverage', 'tagline': '100% Samoan-owned brewery', 'description': 'Fine beverages', 'accent_color': '#8b6f47'},
            {'name': 'Burger Bills', 'slug': 'burger-bills', 'tagline': 'Fast food excellence', 'description': 'Quality burgers and more', 'accent_color': '#d4af37'},
            {'name': 'Tanumapua Farm', 'slug': 'tanumapua-farm', 'tagline': 'Sustainable agriculture', 'description': 'Fresh, local produce', 'accent_color': '#2d6a3e'},
        ]
        for brand_data in brands_data:
            Brand.objects.get_or_create(**brand_data)
        self.stdout.write(f'Created {len(brands_data)} brands')

    def create_categories(self):
        categories_data = [
            {'name': 'Beverages', 'slug': 'beverages'},
            {'name': 'Snacks', 'slug': 'snacks'},
            {'name': 'Dairy', 'slug': 'dairy'},
            {'name': 'Produce', 'slug': 'produce'},
            {'name': 'Frozen', 'slug': 'frozen'},
            {'name': 'Pantry', 'slug': 'pantry'},
        ]
        for cat_data in categories_data:
            Category.objects.get_or_create(**cat_data)
        self.stdout.write(f'Created {len(categories_data)} categories')

    def create_demo_users(self):
        demo_users = [
            {'username': 'admin@example.com', 'email': 'admin@example.com', 'password': 'AdminPass123!', 'groups': ['Admin'], 'is_staff': True, 'is_superuser': True},
            # Finance works in the staff portal at /manage/, not Django Admin, so no is_staff.
            {'username': 'finance@example.com', 'email': 'finance@example.com', 'password': 'FinancePass123!', 'groups': ['Finance']},
            {'username': 'customer@example.com', 'email': 'customer@example.com', 'password': 'CustomerPass123!', 'groups': ['Customer']},
        ]
        for user_data in demo_users:
            groups = user_data.pop('groups')
            user, created = User.objects.get_or_create(username=user_data['username'], defaults=user_data)
            if created:
                user.set_password(user_data['password'])
                user.save()
            for group_name in groups:
                group = Group.objects.get(name=group_name)
                user.groups.add(group)
        self.stdout.write(f'Created {len(demo_users)} demo users')

    def create_products(self):
        brands = Brand.objects.all()
        categories = Category.objects.all()
        if not (brands.exists() and categories.exists()):
            return

        products_data = [
            {'name': 'Samoa Lager 330ml Pack (6)', 'sku': 'TAULA-LAG-6', 'brand': brands.first(), 'category': categories.first(), 'cost_price': 12.50, 'is_exclusive': True},
            {'name': 'Local Coconut Oil 500ml', 'sku': 'TAN-COIL-500', 'brand': brands.last(), 'category': categories.get(slug='pantry'), 'cost_price': 8.00, 'is_exclusive': False},
            {'name': 'Fresh Taro Root 5kg', 'sku': 'TAN-TARO-5K', 'brand': brands.last(), 'category': categories.get(slug='produce'), 'cost_price': 15.00, 'is_exclusive': False},
            {'name': 'Burger Bills Combo Pack', 'sku': 'BB-COMBO-50', 'brand': brands.get(slug='burger-bills'), 'category': categories.first(), 'cost_price': 45.00, 'is_exclusive': True},
        ]
        for prod_data in products_data:
            prod_data['description'] = f"High-quality {prod_data['name']}"
            prod_data['slug'] = slugify(prod_data['name'])
            Product.objects.get_or_create(sku=prod_data['sku'], defaults=prod_data)
        self.stdout.write(f'Created sample products')
