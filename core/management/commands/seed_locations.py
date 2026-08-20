"""Seed the group's site list with company links and map coordinates.

IMPORTANT — the coordinates below are approximate, placed at the town or
district level from general geography rather than surveyed shopfronts. They put
each pin in the right area, not on the right doorstep. Correct them in the
admin (Core → Locations) before launch so customers navigating to a store are
not sent to the wrong spot.
"""

from decimal import Decimal

from django.core.management.base import BaseCommand

from core.models import Location
from products.models import Brand

# (name, company slug, address, island, lat, lng, hours, hq, order)
SITES = [
    ('Ah Liki Wholesale — Head Office', 'ahliki-wholesale',
     'Apia, Upolu', 'Upolu', '-13.833300', '-171.766700',
     'Mon–Fri 8:00–17:00, Sat 8:00–13:00', True, 1),

    ('Ah Liki Wholesale — Distribution Centre', 'ahliki-wholesale',
     'Vaitele Industrial Area, Apia', 'Upolu', '-13.826700', '-171.818900',
     'Mon–Fri 7:30–17:00', False, 2),

    ('Farmer Joe — Fugalei', 'farmer-joe',
     'Fugalei Street, Apia', 'Upolu', '-13.841900', '-171.764500',
     'Mon–Sat 7:00–20:00', False, 3),

    ('Farmer Joe — Vaitele', 'farmer-joe',
     'Vaitele, Apia', 'Upolu', '-13.826700', '-171.818900',
     'Mon–Sat 7:00–20:00', False, 4),

    ('Farmer Joe — Ululoloa', 'farmer-joe',
     'Ululoloa, Apia', 'Upolu', '-13.865600', '-171.779700',
     'Mon–Sat 7:00–20:00', False, 5),

    ('Farmer Joe — Saleimoa', 'farmer-joe',
     'Saleimoa, Upolu', 'Upolu', '-13.831700', '-171.933300',
     'Mon–Sat 7:00–20:00', False, 6),

    ('Taula Beverage — Brewery', 'taula-beverage',
     'Vaitele, Apia', 'Upolu', '-13.822000', '-171.812000',
     'Mon–Fri 8:00–17:00', False, 7),

    ('Burger Bills — Apia', 'burger-bills',
     'Apia town centre, Upolu', 'Upolu', '-13.834500', '-171.759000',
     'Mon–Sun 10:00–21:00', False, 8),

    ('Tanumapua Farm', 'tanumapua-farm',
     'Tanumapua, Upolu', 'Upolu', '-13.869000', '-171.796000',
     'Mon–Fri 8:00–16:00', False, 9),

    ("Savai'i Distribution", 'ahliki-wholesale',
     'Salelologa, Savai\'i', "Savai'i", '-13.737800', '-172.327200',
     'Mon–Fri 8:00–17:00', False, 10),
]


class Command(BaseCommand):
    help = "Seed group locations with company links and approximate coordinates."

    def handle(self, *args, **options):
        brands = {b.slug: b for b in Brand.objects.all()}
        created = updated = 0

        for name, slug, address, island, lat, lng, hours, hq, order in SITES:
            _, was_created = Location.objects.update_or_create(
                name=name,
                defaults={
                    'company': brands.get(slug),
                    'address': address,
                    'island': island,
                    'latitude': Decimal(lat),
                    'longitude': Decimal(lng),
                    'opening_hours': hours,
                    'is_headquarters': hq,
                    'sort_order': order,
                    'phone': '',
                    'email': '',
                },
            )
            created += was_created
            updated += not was_created

        # Remove the earlier placeholder rows superseded by the list above.
        stale = Location.objects.exclude(name__in=[s[0] for s in SITES])
        if stale.exists():
            self.stdout.write('Removing superseded placeholder sites:')
            for site in stale:
                self.stdout.write(f'  - {site.name}')
            stale.delete()

        self.stdout.write(self.style.SUCCESS(f'Locations seeded — created {created}, updated {updated}'))
        self.stdout.write(self.style.WARNING(
            'Coordinates are town-level approximations. Verify each pin in the admin '
            'before launch so customers are not directed to the wrong place.'
        ))
