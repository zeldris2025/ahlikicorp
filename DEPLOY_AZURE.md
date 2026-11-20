# Deploying to Azure App Service (Web App)

Every push to `main` deploys the **code only**. The database and uploaded
images are never part of a deploy, so pushing never resets them.

## How the data is protected

| What | Where it lives on Azure | Touched by a deploy? |
|---|---|---|
| Code | `/home/site/wwwroot` | Yes, replaced each push |
| Database (`db.sqlite3`) | `/home/data/db.sqlite3` | **No** |
| Uploaded media | `/home/data/media/` | **No** |
| Logs | `/home/LogFiles/debug.log` | No |

- `db.sqlite3`, `media/`, `.env` and `venv/` are in `.gitignore`, and the
  workflow (`main_ahliki.yml`) deploys only what is committed to git. It also
  stops the deploy if a database or media folder is ever committed.
- `startup.sh` runs `migrate`, which only applies new migrations. It never
  flushes or recreates the database. Demo data is **not** seeded unless you
  set `SEED_DEMO_DATA=true`.

## One-time setup

1. **Create the Web App** in the Azure Portal: Publish = *Code*,
   Runtime = *Python 3.12* (or 3.13), OS = *Linux*.
2. **Configuration → Application settings**, add:
   - `DJANGO_SECRET_KEY`: a long random string. The site won't start without it.
     Generate one with
     `python -c "import secrets; print(secrets.token_urlsafe(50))"`
   - `SCM_DO_BUILD_DURING_DEPLOYMENT` = `true` (Azure installs `requirements.txt`)
   - `SITE_BASE_URL` = `https://<your-app>.azurewebsites.net`
   - Optional: `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` for a
     custom domain (e.g. `ahliki.com` / `https://ahliki.com`), plus the email
     settings from `.env.example`.
3. **Configuration → General settings → Startup Command**: `bash startup.sh`
4. **Connect GitHub** (done): Deployment Center → GitHub created
   `.github/workflows/main_ahliki.yml` and its own login secrets.
5. **Push to `main`.** The workflow deploys the code, and the first start
   creates an empty database at `/home/data/db.sqlite3`.

## Copying your existing local data up (once)

The first deploy starts with an empty database. To use your local data instead,
upload it once. After that, the site's own data on Azure is the live copy, so
don't upload again or you'll overwrite it.

Use the publish-profile username/password (`userName` / `userPWD` in the file):

```bash
APP=ahliki                  # your app name
USER='$AhLiki'              # userName from the publish profile
PASS='...'                  # userPWD from the publish profile

# Database
curl -u "$USER:$PASS" -X PUT --data-binary @db.sqlite3 \
  "https://$APP.scm.azurewebsites.net/api/vfs/data/db.sqlite3"

# Media (product images, logos, etc.)
(cd media && zip -r ../media.zip .)
curl -u "$USER:$PASS" -X PUT --data-binary @media.zip \
  "https://$APP.scm.azurewebsites.net/api/zip/data/media/"
rm media.zip
```

Then restart the app in the Portal.

## Scaling up later

SQLite is fine for a modest site, but it runs with one Gunicorn worker on
Azure's shared storage. For more traffic, create an *Azure Database for
PostgreSQL* and set `DATABASE_URL=postgresql://...` in Application settings.
`startup.sh` then switches to multiple workers automatically.

## Custom domain (ahliki.com)

The code already expects `ahliki.com`: on Azure it accepts `ahliki.com` and
`www.ahliki.com`, redirects `www.` and plain `http://` to
`https://ahliki.com`, and uses that address in emails and share previews.
(Set `SITE_DOMAIN` in Application settings only to use a different domain.)

1. **App Service → Custom domains → Add custom domain**, domain `ahliki.com`.
   Azure shows two DNS records to create at your domain registrar:
   - `A` record, host `@`, value = the app's IP address
   - `TXT` record, host `asuid`, value = the verification ID
2. Add `www.ahliki.com` the same way: a `CNAME` record, host `www`, value
   `<your-app>.azurewebsites.net`, plus `TXT` host `asuid.www` with the same ID.
3. When both validate, choose **Add binding → App Service Managed Certificate**
   for each, so HTTPS works (free, renewed automatically).
4. **Configuration → General settings → HTTPS Only = On.**
5. Optional, once `https://ahliki.com` works: set `REDIRECT_TO_SITE_DOMAIN=true`
   so the `*.azurewebsites.net` address also forwards to `ahliki.com`.

If reCAPTCHA is switched back on, add `ahliki.com` to the key's domain list
in the Google reCAPTCHA console first.
