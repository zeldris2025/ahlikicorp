"""FAQ content for the site assistant.

Answers are drawn from the company overview and from data already on the site.
Nothing here should state a fact that is not verifiable — where a detail is not
known (exact opening hours, minimum order values), the answer points the
visitor at the contact page rather than guessing.

Edit this module to change what the assistant knows.
"""

FAQ_TOPICS = [
    {
        'id': 'about',
        'q': 'Who is Ah Liki Investment Corporation?',
        'keywords': ['who', 'about', 'company', 'corporation', 'history', 'ah liki'],
        'a': (
            'Ah Liki Investment Corporation Limited is a Samoan-owned, multi-venture company '
            'that has operated for more than two decades. We run a large supply-chain network '
            'serving the entire Samoan market as well as Samoans abroad, across wholesale '
            'distribution, supermarket retail, brewing, restaurants and agriculture.'
        ),
        'links': [{'label': 'About us', 'url': 'core:about'}],
    },
    {
        'id': 'companies',
        'q': 'What companies are in the group?',
        'keywords': ['companies', 'brands', 'subsidiaries', 'ventures', 'businesses', 'group'],
        'a': (
            'There are five: Ah Liki Samoa Wholesale (bulk food and non-food distribution), '
            'Farmer Joe Supermarket (retail), Taula Beverage Limited (a 100% Samoan-owned '
            'brewery), Burger Bills (restaurants) and Tanumapua Farm (sustainable agriculture).'
        ),
        'links': [{'label': 'Our companies', 'url': 'core:companies'}],
    },
    {
        'id': 'quote',
        'q': 'How do I request a quote?',
        'keywords': ['quote', 'quotation', 'pricing', 'price', 'cost', 'order', 'buy', 'purchase'],
        'a': (
            'Browse the wholesale catalogue, add the products you need with the quantities you '
            'want, then open your quote request and submit your contact details. Our team '
            'prepares your pricing and sends a formal quote by email, usually within 24 hours.'
        ),
        'links': [
            {'label': 'Browse catalogue', 'url': 'products:list'},
            {'label': 'My quote request', 'url': 'quotes:basket'},
        ],
    },
    {
        'id': 'prices',
        'q': 'Why are prices not shown on the site?',
        'keywords': ['price', 'prices', 'pricing', 'cost', 'how much', 'rate', 'not shown'],
        'a': (
            'Wholesale pricing depends on quantity, delivery location and account terms, so it '
            'is prepared per customer rather than published. Send a quote request and we will '
            'price your specific list.'
        ),
        'links': [{'label': 'Start a quote', 'url': 'products:list'}],
    },
    {
        'id': 'catalogue',
        'q': 'What products do you supply?',
        'keywords': ['products', 'catalogue', 'catalog', 'supply', 'stock', 'goods', 'items', 'sell'],
        'a': (
            'Ah Liki Samoa Wholesale supplies bulk food and foodstuff along with non-food lines '
            '— rice and grains, canned goods, cooking essentials, beverages, snacks, household '
            'products and paper disposables — to trade, hospitality and institutional customers.'
        ),
        'links': [{'label': 'View catalogue', 'url': 'products:list'}],
    },
    {
        'id': 'locations',
        'q': 'Where are you located?',
        'keywords': ['location', 'locations', 'where', 'address', 'store', 'stores', 'branch', 'find'],
        'a': (
            'We operate across Samoa, including Farmer Joe supermarkets at Fugalei, Vaitele, '
            'Ululoloa and Saleimoa. The locations page lists every site with its address and '
            'contact details.'
        ),
        'links': [{'label': 'Find a location', 'url': 'core:locations'}],
    },
    {
        'id': 'delivery',
        'q': 'Do you deliver?',
        'keywords': ['deliver', 'delivery', 'shipping', 'freight', 'transport', 'send'],
        'a': (
            'Our supply-chain network covers the Samoan market. Include your delivery location '
            'and address when you submit a quote request and we will confirm delivery options '
            'and any freight cost with your pricing.'
        ),
        'links': [{'label': 'Request a quote', 'url': 'products:list'}],
    },
    {
        'id': 'trade',
        'q': 'Can I open a trade account?',
        'keywords': ['account', 'trade', 'credit', 'wholesale account', 'business', 'register', 'sign up'],
        'a': (
            'Yes — we supply retailers, hospitality and institutional customers. Create an '
            'account on the site to keep track of your quote requests, and mention your trading '
            'requirements in your first request so our team can set you up correctly.'
        ),
        'links': [
            {'label': 'Create an account', 'url': 'accounts:register'},
            {'label': 'Contact us', 'url': 'core:contact'},
        ],
    },
    {
        'id': 'taula',
        'q': 'Tell me about Taula Beverage',
        'keywords': ['taula', 'beer', 'brewery', 'beverage', 'drinks', 'water', 'soft drink'],
        'a': (
            'Taula Beverage Limited is a 100% Samoan-owned brewery and beverage producer within '
            'the group, making beers, soft drinks and bottled water locally for the Samoan '
            'market and for Samoans overseas.'
        ),
        'links': [{'label': 'Our companies', 'url': 'core:companies'}],
    },
    {
        'id': 'contact',
        'q': 'How do I contact a person?',
        'keywords': ['contact', 'phone', 'call', 'email', 'talk', 'speak', 'human', 'someone', 'help'],
        'a': (
            'Use the contact form and your message goes straight to our team, or reach us on the '
            'phone and email listed at the bottom of every page. For anything about pricing or '
            'stock, a quote request is usually the fastest route.'
        ),
        'links': [{'label': 'Contact us', 'url': 'core:contact'}],
    },
]

# Shown as opening suggestions.
STARTER_IDS = ['quote', 'catalogue', 'companies', 'locations']
