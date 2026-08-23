# Scientific Calculator

## Release 0.4.0

This release adds an "Atom % ⇄ Mass %" composition tab, converting between atomic
(mole) fraction and mass fraction for a list of elements using IUPAC conventional
standard atomic weights (`GET /api/elements`, `POST /api/composition/convert`).

## Release 0.3.0

This release adds a comprehensive `/help` surface with the parser algorithm,
angle equation, input roles, limitations, and an SVG workflow. It also adds
production response headers and a Waitress-backed `scientific-calculator`
entry point while preserving all 0.2 APIs.

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e .
scientific-calculator
```

Verify `GET /api/health` before switching the reverse proxy to port 5055. To
roll back, reinstall the previous pinned wheel or Git tag and restart the
service.

Standalone local service for safe, reproducible engineering and scientific expressions. It is intentionally separate from the portal and from PyTex's crystallographic calculator.

The browser UI supports named variables, `^` power notation, approved math functions, degree/radian modes, one-variable plots, two-variable surface heatmaps, and atom-fraction/mass-fraction composition conversion. The API also keeps the legacy-compatible `/api/scientific_calculator/evaluate` and `/api/scientific_calculator/plot` routes.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5055`.

## Deployment modes

The calculator is a complete standalone web app and can be developed, tested, and deployed on its
own. The Office Scientific Tools portal may link to its service URL, but `ml_server` and the other
tools are not required dependencies.
