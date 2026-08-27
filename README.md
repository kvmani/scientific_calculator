# Scientific Calculator

## Release 0.5.0

This release adds a **Periodic Table** tab: all 118 elements, clickable, with the
properties a working scientist looks up — atomic mass, group, period, block,
category, electron configuration and electrons per shell, oxidation states,
electronegativity, first ionization energy, atomic radius, state at room
temperature, melting and boiling points, density, crystal structure,
radioactivity, crustal abundance and discovery. Shade the table by category,
block, state, electronegativity, melting point or density; search by name,
symbol or atomic number. `GET /api/periodic_table` returns the whole table in one
request and `GET /api/periodic_table/<symbol>` returns one element, so the tab
works with no outside connection.

Most of the table is derived rather than transcribed — group, period and block
from the layout, the electron configuration from the Madelung ordering with its
established exceptions listed explicitly, the state at room temperature from the
transition points, and the atomic mass from the same table the composition
converter uses. An absent value says which absence it is: "not measured",
"known since antiquity" and "made, not found" are different facts.

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

The browser UI supports named variables, `^` power notation, approved math functions, degree/radian modes, one-variable plots, two-variable surface heatmaps, atom-fraction/mass-fraction composition conversion, and a full periodic table of the elements. The API also keeps the legacy-compatible `/api/scientific_calculator/evaluate` and `/api/scientific_calculator/plot` routes.

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
