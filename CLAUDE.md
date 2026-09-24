# vittorio-coffee - rules for Claude sessions

Vittorio Gourmet Espresso catalogue and trade-order site. Flask (`app.py`, `create_app()`), Jinja
templates in `templates/`, catalogue data in `data/products.json`, static assets in `static/`.
The site represents two brands in Cyprus: Vittorio Gourmet Espresso (coffee) and Jean Paul Lab (beverages,
teas, dessert mixes); each product has a `brand` field. Deployed on Render (Starter plan, Frankfurt) from
`render.yaml`; auto-deploys on push since 2026-09-24 (Render's GitHub app was given access to this repo).

## Run and test (Windows, from the repo root)
- Virtualenv already set up: `.venv\Scripts\python -m pip install -r requirements.txt` after a fresh clone
  (`python -m venv .venv` first).
- Tests: `.venv\Scripts\python -m pytest -q` (45 at 2026-09-24, all green).
- Local server: `.venv\Scripts\python -m flask --app app run --debug`, then open http://127.0.0.1:5000.
- Mail needs `.env` (copy `.env.example`; SMTP_PASSWORD is a Gmail app password). Never commit `.env`.
  Without it, a local test order falls back to FormSubmit and lands in the real depot inbox.
- Product photos: after adding or replacing one, run `python tools/optimize_images.py` (needs Pillow) to
  rebuild the WebP versions in `static/images/products/web/` and the `image.web` entries in products.json.
- `summary` in products.json is the shop's original text (refreshed by `tools/sync_descriptions.py`);
  `description` is the short edited copy shown on the site.

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
