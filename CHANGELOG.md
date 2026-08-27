# Changelog

## 0.5.0 — 2026-08-27

- Added a **Periodic Table** tab: all 118 elements as a clickable table, with atomic mass,
  group/period/block, category, electron configuration and electrons per shell, valence electrons,
  common oxidation states, electronegativity, first ionization energy, atomic radius, state at
  room temperature, melting and boiling points, density, crystal structure, radioactivity, crustal
  abundance and discovery. Cells can be shaded by category, block, state, electronegativity,
  melting point or density; the search box takes a name, a symbol or an atomic number. The whole
  table arrives in one request (`/api/periodic_table`, plus `/api/periodic_table/<symbol>`) and
  every interaction after that is local, so the tab works with no outside connection.

  Most of the table is **derived rather than transcribed**, because a wrong number in a reference
  table does not look wrong: group, period and block come from the layout, the electron
  configuration from the Madelung ordering with its twenty established exceptions listed
  explicitly, the state at room temperature from the transition points, and the atomic mass from
  the same `elements.py` the composition converter uses — so the two tabs cannot disagree about a
  mass. The genuinely empirical values are entered once, and are checked by tests against rules
  that hold independently of them rather than against themselves.

  An absent value states *which* absence it is. "Not measured", "known since antiquity" and
  "made, not found" are three different facts, and a blank cell distinguishes none of them. No
  melting point, boiling point or density is quoted for elements 100 to 118: none has ever been
  produced in a weighable amount, so every such figure in the literature is a prediction, and a
  number in this table means a measurement.

- Fixed: the packaged version and the version reported by `/api/health` had drifted apart
  (`0.3.0` against `0.4.0`) because the test transcribed the expected string instead of reading
  it. Both are now `0.5.0`, and the test asserts that they agree.

## 0.4.0 — 2026-08-23

- Added an Atom % ⇄ Mass % composition conversion tab, backed by a 118-element IUPAC standard
  atomic weight table (`elements.py`), `/api/composition/convert`, and `/api/elements`.

## 0.3.0 — 2026-08-23

- Added a scientific help page covering expression evaluation, sampling, equations, critical
  bounds, and an SVG workflow.
- Added versioned health metadata, security headers, and a Waitress production entry point.
- Repackaged the service so wheels contain the application, templates, JavaScript, and SVG assets.

## 0.2.0

- Added the safe expression evaluator and bounded one- and two-variable plotting APIs.
