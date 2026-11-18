# Ah Liki Investment Corporation – Django Website

A production-ready, high-performance full-stack Django website for Ah Liki Investment Corporation Limited, a Samoan multi-venture company.

## Features

- **Multi-Brand Showcase**: Highlight all five subsidiaries (Ah Liki Samoa Wholesale, Farmer Joe Supermarket, Taula Beverage Limited, Burger Bills, Tanumapua Farm)
- **Product Catalogue**: Searchable, filterable product listings with detailed views
- **Quote System**: Full workflow for customers to request quotes and finance team to manage/approve them
  - Customer quote submission with cart
  - Finance dashboard for quote management
  - PDF quote generation using ReportLab
  - Email notifications
- **Role-Based Access Control**: Customer, Finance, and Admin groups with Django permissions
- **Admin Customization**: Heavily customized Django Admin with inline editors and dashboards
- **Responsive Design**: Mobile-first design using Tailwind CSS
- **Performance Optimized**: Redis caching, query optimization, lazy loading
- **REST API**: DRF endpoints for programmatic access to products and quotes
- **Production Ready**: Docker setup, WhiteNoise static files, security hardening

## Tech Stack

- **Backend**: Django 5.2.17 + Django REST Framework
- **Database**: PostgreSQL (SQLite for development)
- **Cache**: Redis (with fallback to in-memory)
- **Frontend**: Django Templates + Tailwind CSS + Alpine.js
- **PDF**: ReportLab
- **Email**: Django email backend (console in dev, SMTP/Resend in production)
- **Server**: Gunicorn + Nginx + WhiteNoise
- **Containerization**: Docker + docker-compose

## Quick Start

### Local Development

1. **Clone and set up environment**:
   ```bash
   cd ahlikicorp
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Run migrations**:
   ```bash
   python manage.py migrate
   python manage.py seed_data  # Load sample data
   ```

4. **Create superuser** (optional):
   ```bash
   python manage.py createsuperuser
   ```

5. **Run development server**:
   ```bash
   python manage.py runserver
   ```
   Visit `http://localhost:8000`

### Demo Credentials

After running `seed_data`, use these test accounts:
- **Admin**: `admin@example.com` / `AdminPass123!`
- **Finance**: `finance@example.com` / `FinancePass123!`
- **Customer**: `customer@example.com` / `CustomerPass123!`

## Project Structure

```
ahlikicorp/
├── ahlikicorp/           # Project settings & config
│   ├── settings.py       # Django settings
│   ├── urls.py          # Root URL patterns
│   └── wsgi.py
├── accounts/            # User authentication & profiles
├── core/                # Home, about, locations, newsletter
├── products/            # Product catalogue & DRF API
├── quotes/              # Quote workflow (critical module)
│   ├── views.py        # Quote CRUD + PDF generation
│   ├── email.py        # Email notifications
│   ├── pdf.py          # PDF generation using ReportLab
│   └── forms.py        # Quote forms & formsets
├── templates/           # HTML templates (Tailwind CSS)
├── static/              # CSS, JS, images
├── manage.py            # Django CLI
├── requirements.txt     # Python dependencies
├── Dockerfile           # Docker image definition
├── docker-compose.yml   # Multi-container setup
└── README.md            # This file
```

## API Endpoints

### Products API (Read-Only)
```
GET  /api/products/products/              # List all active products
GET  /api/products/products/{id}/         # Product detail
GET  /api/products/brands/                # List brands
GET  /api/products/categories/            # List categories
```

Query parameters: `?brand=`, `?category=`, `?is_exclusive=`, `?search=`, `?ordering=`

### Quotes API (Authenticated)
```
GET  /api/quotes/quotes/                   # List user's quotes (or all if Finance/Admin)
GET  /api/quotes/quotes/{id}/              # Quote detail
POST /api/quotes/quotes/                   # Create quote (API)
PATCH /api/quotes/quotes/{id}/             # Update quote
POST /api/quotes/quotes/{id}/mark_quoted/  # Mark as quoted
```

## Configuration

### Environment Variables (`.env`)

```
DEBUG=False
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,example.com
DATABASE_URL=postgresql://user:pass@localhost:5432/ahlikicorp
REDIS_URL=redis://localhost:6379/0
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.resend.com
QUOTE_NOTIFICATION_EMAIL=sales@ahliki.com
DEFAULT_FROM_EMAIL=noreply@ahliki.com
```

### Database

**Development**: SQLite (default, no setup needed)
**Production**: PostgreSQL via `DATABASE_URL` env var

### Caching

**Development**: In-memory cache (default)
**Production**: Redis via `REDIS_URL` env var

### Email

**Development**: Console backend (prints emails to terminal)
**Production**: Configure `EMAIL_HOST`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`

## Quote Workflow

1. **Customer Request**: Fill contact form on `/quotes/create/`
2. **Confirmation**: Email sent to customer + finance team notified
3. **Finance Review**: Finance user logs in to `/quotes/` (Finance dashboard)
4. **Add Items**: Finance adds products and prices to quote
5. **Generate PDF**: Click "PDF" button to generate professional quote
6. **Send to Customer**: Finance clicks "Mark as Quoted" to email PDF
7. **Customer Review**: Customer can view/download quote from `/quotes/{id}/`
8. **Status Update**: Finance updates status (Accepted/Rejected)

## Admin Panel

Access at `/admin/` with superuser credentials.

- **Products**: Full CRUD with inline product gallery management
- **Quotes**: Dashboard with filtering, inline items, status badges, email actions
- **Users**: Permission management via Groups (Customer/Finance/Admin)
- **Locations**: Store locations management
- **Newsletter**: Email subscriber list with bulk actions

## Deployment

### Docker

```bash
# Build image
docker build -t ahlikicorp .

# Run with docker-compose (includes PostgreSQL + Redis)
docker-compose up -d

# Run migrations inside container
docker exec ahlikicorp python manage.py migrate

# Seed data
docker exec ahlikicorp python manage.py seed_data
```

Production environment file for docker-compose:
```bash
cp .env.example .env.docker
# Edit .env.docker with production values
docker-compose --env-file .env.docker up -d
```

### Manual Deployment

1. Install Python 3.11+, PostgreSQL, Redis
2. Clone repo, install requirements: `pip install -r requirements.txt`
3. Set environment variables in `.env`
4. Run migrations: `python manage.py migrate`
5. Collect static files: `python manage.py collectstatic --noinput`
6. Start Gunicorn: `gunicorn ahlikicorp.wsgi:application --bind 0.0.0.0:8000`
7. Configure Nginx as reverse proxy (see `nginx.conf` example)

## Security

- CSRF protection enabled
- Password validation (12+ chars, complexity)
- SQL injection protection via ORM
- XSS protection via template escaping
- Secure headers (HSTS, X-Frame-Options, etc.)
- Permission-based access control (finance/admin views)

## Performance

- **Query Optimization**: `select_related()` and `prefetch_related()` on all list views
- **Caching**: Homepage brands/products, quote PDFs cached 24h
- **Static Files**: WhiteNoise with gzip compression
- **Database Indexes**: `is_active` + `is_exclusive` on products
- **Lazy Loading**: Images use `loading="lazy"`
- **Minimal JS**: Alpine.js + GSAP only where needed (navbar, animations)

## Testing

Run Django system checks:
```bash
python manage.py check
```

Run migrations test:
```bash
python manage.py migrate --plan
```

(Comprehensive test suite can be added with pytest-django)

## Troubleshooting

### Import Error: No module named 'X'
```bash
pip install -r requirements.txt
```

### Migration conflicts
```bash
python manage.py migrate --fake-initial
```

### Static files not loading in production
```bash
python manage.py collectstatic
```

### Quote PDF not generating
Ensure `reportlab` is installed: `pip install reportlab`

## License

Copyright (c) 2026 Charlie Wilson Ah Kuoi. All rights reserved.

Proprietary software. It may not be used, copied, modified or distributed
without the prior written permission of Charlie Wilson Ah Kuoi. See
[LICENSE](LICENSE) for the full terms.

## Support

Contact: info@ahliki.com  
Sales: sales@ahliki.com  
Quotes: quotes@ahliki.com

---

Built with Django ❤️ and hosted with pride from Samoa 🇼🇸
