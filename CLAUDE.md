# vittorio-coffee - rules for Claude sessions

Vittorio Gourmet Espresso catalogue and trade-order site. Flask (`app.py`, `create_app()`), Jinja
templates in `templates/`, catalogue data in `data/products.json`, static assets in `static/`.
Deployed on Render (free web service, Frankfurt) from `render.yaml`; `autoDeployTrigger: commit`.

## Run and test (Windows, from the repo root)
- Virtualenv already set up: `.venv\Scripts\python -m pip install -r requirements.txt` after a fresh clone
  (`python -m venv .venv` first).
- Tests: `.venv\Scripts\python -m pytest -q` (34 at 2026-09-24, all green).
- Local server: `.venv\Scripts\python -m flask --app app run --debug`, then open http://127.0.0.1:5000.
- Mail needs `.env` (copy `.env.example`; SMTP_PASSWORD is a Gmail app password). Never commit `.env`.

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
