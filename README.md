# Scientific Calculator

## Release 0.6.0

This release turns the Periodic Table tab into a working X-ray reference. Every
element up to californium now carries all twenty-six Siegbahn **emission lines**
(Kα1, Kα2, Kβ1, Lα1, Lβ1, Mα … ) and all twenty-four **absorption edges**
(K, L1–L3, M1–M5, N1–N7, O1–O5, P1–P3), each with its energy in eV and keV, its
wavelength in ångströms, the transition it comes from, and — for edges — the
fluorescence yield and jump ratio. Copper Kα1 reads 8.0463 keV / 1.5409 Å.

An **X-ray line finder** answers the question a spectrum actually poses: give the
energy of an unlabelled peak and it lists every characteristic line within a
tolerance, nearest first, with the offset in eV.

Thirty further properties join the table — successive ionization energies,
electron affinity, the Allen electronegativity scale, covalent, van der Waals and
metallic radii, atomic volume, polarizability, lattice structure and constant,
thermal conductivity, heat capacities, the heats of fusion, vaporization and
atomization, seawater abundance, Goldschmidt and geochemical class, CAS number,
CPK colour, Mendeleev and Pettifor numbers, price and supply risk, discoverers,
name origin, natural isotopes with their abundances, and a description of each
element's sources and uses. Cells can be shaded by any of twenty-six properties,
with a logarithmic ramp for the ones spanning many decades.

**Every number says where it came from.** Each group of properties carries a
citation with a direct link — CIAAW, NIST, the Elam/Ravel/Sieber paper and its
DOI, Cordero, Alvarez — and a panel under the table lists them all, including a
cross-check link to the NIST X-ray Transition Energies database. The provenance
is served at `GET /api/sources`.

The X-ray and extra-property tables are generated from the published `xraydb` and
`mendeleev` databases by `scripts/generate_reference_data.py` and vendored as
Python modules, so the service still runs with no outside connection and no new
runtime dependency. Regenerate with:

```
python -m pip install xraydb mendeleev
python scripts/generate_reference_data.py
```

New endpoints: `GET /api/xray/<symbol>`, `GET /api/xray/identify?energy_kev=…`,
`GET /api/sources`.

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

The browser UI supports named variables, `^` power notation, approved math functions, degree/radian modes, one-variable plots, two-variable surface heatmaps, atom-fraction/mass-fraction composition conversion, a full periodic table of the elements with their characteristic X-ray lines and absorption edges, and an X-ray line finder. The API also keeps the legacy-compatible `/api/scientific_calculator/evaluate` and `/api/scientific_calculator/plot` routes.

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
