# vittorio-coffee - rules for Claude sessions

Vittorio Gourmet Espresso catalogue and trade-order site. Flask (`app.py`, `create_app()`), Jinja
templates in `templates/`, catalogue data in `data/products.json`, static assets in `static/`.
The site represents two brands in Cyprus: Vittorio Gourmet Espresso (coffee) and Jean Paul Lab (beverages,
teas, dessert mixes); each product has a `brand` field. Deployed on Render (Starter plan, Frankfurt) from
`render.yaml`; auto-deploys on push since 2026-09-24 (Render's GitHub app was given access to this repo).

## Run and test (Windows, from the repo root)
- Virtualenv already set up: `.venv\Scripts\python -m pip install -r requirements.txt` after a fresh clone
  (`python -m venv .venv` first).
- Tests: `.venv\Scripts\python -m pytest -q` (86 at 2026-09-24, all green).
- Local server: `.venv\Scripts\python -m flask --app app run --debug`, then open http://127.0.0.1:5000.
- Mail needs `.env` (copy `.env.example`; SMTP_PASSWORD is a Gmail app password). Never commit `.env`.
  Without it, a local test order falls back to FormSubmit and lands in the real depot inbox.
- Product photos: after adding or replacing one, run `python tools/optimize_images.py` (needs Pillow) to
  rebuild the WebP versions in `static/images/products/web/` and the `image.web` entries in products.json.
- `summary` in products.json is the shop's original text (refreshed by `tools/sync_descriptions.py`);
  `description` is the short edited copy shown on the site.
- `tools/optimize_images.py` also builds the homepage hero cut-outs (`static/images/hero/`), the link
  preview `brand/share.jpg`, and the B2B counter pieces (`static/images/scene/`), including the Vittorio
  decals on the three brand machines (official photos in `static/images/machines/brand/`).
- Page map: home = product-counter hero with hover cards + brand panels + shelves; `/cyprus` = B2B
  scroll story (chapters fill a counter, zooms on the machine first, machines rotate). `/refer` = partner
  referral form (1 kg espresso reward). Menu starts with a bold Home link. Visit, supply,
  machines, philosophy, story and journal pages still exist but are not in the nav.
- Greek site: every page is served in English at `/...` and in Greek at `/el/...` (`localized()` in app.py).
  UI and content strings are wrapped in `_("English text")` in templates (`tr()` in Python). The Greek
  text lives in `EL` in `i18n.py`, keyed by the English. Greek product copy is in `data/products_el.json`
  (keyed by slug, kept apart because `tools/build_catalog.py` rewrites products.json). When you add or
  change English copy, add the Greek too: `tests/test_greek.py` fails on any string without a translation.
  Brand and product names stay in English.

## Copy and design rules from the owner
- Terse, professional distributor tone. No how-it-works steps, no "delivered by car", no long blurbs.
- No AI-generated people or machines (they came out illogical); use real product and brand photos.
- The machine brand is "Appia Life" (Nuova Simonelli), never "Apia".

## Shipping (carried over from `.cursor/rules/auto-ship.mdc`)
- After a substantive change: run the tests, fix failures, then commit and `git push origin main`
  WITHOUT asking - pushing to `main` IS the publish step (Render auto-deploys on commit).
- Stage explicit files only; never `.env`, credentials, scratch probes or `candidates/`.
- Commit messages say why the change matters.
- If the live site still serves an old build after a successful push, say so once (Manual Deploy on Render).

## Secrets on Render
SMTP_PASSWORD lives on the Render service's Environment tab or as a Secret File `smtp_password`
(`/etc/secrets/smtp_password`) - never in `render.yaml`. `tools/set_render_smtp.py` sets it via the Render API.

## Separate from the FightCamp game
This project has nothing to do with the FightCamp repo. Its rules (agent_comms, HANDOFF, Godot) do not apply here.

## Domains, Google and site behaviour (2026-09-24)
- Live at https://vittoriocyprus.com (Render custom domain). `www` and the old onrender host 301 to it
  (`move_to_own_domain` in app.py; /health is exempt). `SITE_URL` in mailing.py builds email links;
  FormSubmit stays pinned to the onrender origin because its activation is tied to it.
- Planned next: make vittoriocoffee.com (the old WordPress shop, DNS at Hostinger) the main domain and 301 its
  old WordPress paths. Keep its Hostinger MX/SPF records, because info@vittoriocoffee.com mail runs there.
- `BUSINESS` in content.py: `reviews` (Google review link, footer + customer email), `trustpilot` (empty),
  `search_console` (list of verification codes, one per Search Console property).
- Order form: `address` is required (cash on delivery). Google Places suggestions (static/js/address.js)
  load only when the `GOOGLE_MAPS_KEY` env var is set on Render.
- Add to order posts via fetch (`X-Requested-With: fetch` returns JSON) and shows a toast; without JS it
  returns to the referring page. Never send shoppers to /order after adding an item.
- Never write or post reviews for the business; Google treats owner reviews as fake.
