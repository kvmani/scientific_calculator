# Changelog

## 0.6.0 — 2026-08-28

- The **Periodic Table** tab now carries characteristic X-ray data: for every element up to
  californium, all twenty-six Siegbahn emission lines (Kα1, Kα2, Kα3, Kβ1–Kβ5, Lα1, Lα2,
  Lβ1–Lβ6, Lγ1–Lγ6, Lℓ, Lη, Mα, Mβ, Mγ, Mζ) and all twenty-four absorption edges (K, L1–L3,
  M1–M5, N1–N7, O1–O5, P1–P3), each with its energy in eV and keV, its wavelength in ångströms,
  the transition it comes from, and — for edges — the fluorescence yield and jump ratio.
  Cu Kα1 reads 8.0463 keV / 1.5409 Å, the number every powder pattern is indexed against.

- Added an **X-ray line finder**: give the energy of an unlabelled peak and it lists every
  characteristic line within a tolerance, nearest first. This is the question a spectrum actually
  poses — not "what is iron's Kα1" but "what could this 6.4 keV peak be" — and it is the one a
  printed table answers worst, because answering it means scanning every row.

- Added thirty further properties per element: successive ionization energies, electron affinity,
  the Allen electronegativity scale, covalent (Cordero), van der Waals (Alvarez) and metallic
  radii, atomic volume, dipole polarizability, lattice structure and constant, thermal
  conductivity, molar and specific heat capacity, the heats of fusion, vaporization and
  atomization, seawater abundance, Goldschmidt and geochemical class, CAS registry number, CPK
  colour, Mendeleev and Pettifor numbers, indicative price and supply risk, discoverers, name
  origin, and a description of the element's sources and uses. Natural isotopes are listed with
  their abundances and masses.

- The detail view is now grouped into collapsible sections rather than one flat list of forty
  rows, and the groups you open are remembered as you move between elements — someone comparing
  K-edges down a group should not have to reopen the same section for each one.

- Cell shading now offers twenty-six properties rather than six, grouped by kind, including the
  X-ray energies and the CPK colours. Properties spanning many decades — crustal and seawater
  abundance, price, thermal conductivity — are shaded logarithmically, because oxygen is four
  hundred million times as abundant as rhodium and on a linear scale that is not a comparison but
  a single outlier. The legend now labels both ends of the ramp with their values instead of
  saying only "darker is higher".

- **Every number now says where it came from.** Each group of properties in the detail view
  carries a citation with a direct link — CIAAW for atomic weights, NIST for configurations,
  isotopic compositions and ionization energies, the Elam/Ravel/Sieber paper and its DOI for the
  X-ray tables, Cordero and Alvarez for the radii — and a "where these numbers come from" panel
  under the table lists all of them, with a cross-check link to the NIST X-ray Transition
  Energies database. The provenance is data (`sources.py`, served at `/api/sources`), not prose
  in a template, and a test fails if any reported property is not claimed by a source.

- The X-ray and extra-property tables are **generated, not typed**: `scripts/generate_reference_data.py`
  reads them out of the published `xraydb` and `mendeleev` databases and writes vendored Python
  modules, so the service still runs with no outside connection and no new runtime dependency.
  Ninety-eight elements times twenty-six lines is two and a half thousand four-figure numbers,
  which is not a thing to transcribe by hand.

- The tests check the new data against physics rather than against itself: Moseley's law (every
  line and edge energy rises with Z, which no transposed digit survives), that no emission line
  exceeds the edge whose vacancy it fills, that fluorescence yields are probabilities, that
  isotopic abundances sum to 100%, and that a covalent radius is smaller than a van der Waals
  one. Two findings came out of writing them and are recorded rather than smoothed over: the 4f
  levels of the lanthanides lie *below* the 6s shell outside them, so "deeper shell, higher
  energy" is false past the M shell; and for nine elements — the 5d metals and early actinides —
  the NIST and CRC ionization energies genuinely differ by up to four percent.

- New endpoints: `/api/xray/<symbol>`, `/api/xray/identify`, `/api/sources`. `/api/periodic_table`
  now leaves the per-element X-ray tables and prose out of the whole-table payload, which would
  otherwise have grown from 60 kB to 800 kB to draw a grid that uses none of it; everything the
  grid shades, filters or searches by is still in that one request, and opening an element costs
  a further 10 kB.

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
