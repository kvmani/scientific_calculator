"""Regenerate the vendored element reference tables from their upstream databases.

Why a generator rather than a hand-typed table
----------------------------------------------
The periodic table module already refuses to type anything it can derive, on the
grounds that a wrong number in a reference table looks exactly like a right one.
The same argument applies with more force to the X-ray data: 98 elements times
twenty-six emission lines is two and a half thousand four-digit numbers, and no
amount of proof-reading makes hand transcription of that safe.

So the numbers are not typed. They are read out of two published databases and
written into ``xray_data.py`` and ``element_extras.py`` as generated modules,
which the service then imports with no runtime dependency on either database.
Re-running this script is the only supported way to change those two files.

Usage
-----
    python -m pip install xraydb mendeleev
    python scripts/generate_reference_data.py

Sources
-------
* X-ray emission lines and absorption edges: the ``xraydb`` package (M. Newville,
  MIT licence), which packages the tables of W. T. Elam, B. D. Ravel and
  J. R. Sieber, *Radiation Physics and Chemistry* 63 (2002) 121. Elam covers
  Z = 1 to 98; beyond californium no element has enough of a measured X-ray
  spectrum to tabulate, and this script writes nothing there rather than
  extrapolating.
* Everything else: the ``mendeleev`` package (L. M. Mentel, MIT licence), which
  compiles CRC Handbook, NIST and IUPAC values.

Both are permissively licensed and their data is drawn from published
compilations; the generated modules name the source in their own docstrings.
"""

from __future__ import annotations

import datetime as _dt
from pathlib import Path
from typing import Any

import xraydb
from mendeleev import element as _element
from xraydb import atomic_symbol

HERE = Path(__file__).resolve().parent
PACKAGE = HERE.parent / "src" / "scientific_calculator_service"

#: Elements the X-ray tables cover. Elam stops at californium.
MAX_XRAY_Z = 98
MAX_Z = 118


def _round(value: Any, digits: int) -> Any:
    return None if value is None else round(float(value), digits)


def _clean(text: Any) -> Any:
    """Collapse whitespace in a prose field, or return ``None`` if it is empty."""

    if text is None:
        return None
    collapsed = " ".join(str(text).split())
    return collapsed or None


def _xray_tables() -> tuple[dict[int, dict], dict[int, dict]]:
    edges: dict[int, dict] = {}
    lines: dict[int, dict] = {}
    for number in range(1, MAX_XRAY_Z + 1):
        symbol = atomic_symbol(number)
        element_edges = {
            level: (
                _round(edge.energy, 2),
                _round(edge.fyield, 6),
                _round(edge.jump_ratio, 4),
            )
            for level, edge in sorted(xraydb.xray_edges(symbol).items())
        }
        element_lines = {
            name: (
                _round(line.energy, 2),
                _round(line.intensity, 6),
                line.initial_level,
                line.final_level,
            )
            for name, line in sorted(xraydb.xray_lines(symbol).items())
        }
        if element_edges:
            edges[number] = element_edges
        if element_lines:
            lines[number] = element_lines
    return edges, lines


#: ``(attribute on a mendeleev element, name in the generated table, rounding)``.
#:
#: Only properties the periodic-table module does not already carry are taken
#: from here. Where both sources have a value - density, melting point,
#: electronegativity - the existing hand-checked table stays authoritative, so
#: that one number never has two possible answers depending on which field a
#: caller happens to read.
_NUMERIC_FIELDS: tuple[tuple[str, str, int], ...] = (
    ("electron_affinity", "electron_affinity_ev", 4),
    ("covalent_radius_cordero", "covalent_radius_pm", 1),
    ("vdw_radius_alvarez", "van_der_waals_radius_pm", 1),
    ("metallic_radius", "metallic_radius_pm", 1),
    ("atomic_volume", "atomic_volume_cm3_per_mol", 3),
    ("thermal_conductivity", "thermal_conductivity_w_per_m_k", 3),
    ("molar_heat_capacity", "molar_heat_capacity_j_per_mol_k", 3),
    ("specific_heat_capacity", "specific_heat_j_per_g_k", 4),
    ("fusion_heat", "heat_of_fusion_kj_per_mol", 3),
    ("evaporation_heat", "heat_of_vaporization_kj_per_mol", 3),
    ("heat_of_formation", "heat_of_atomization_kj_per_mol", 2),
    ("dipole_polarizability", "dipole_polarizability_au", 3),
    ("en_allen", "electronegativity_allen_ev", 3),
    ("abundance_sea", "abundance_seawater_mg_per_l", 8),
    ("lattice_constant", "lattice_constant_angstrom", 4),
    ("price_per_kg", "price_usd_per_kg", 4),
    ("relative_supply_risk", "supply_risk_index", 2),
    ("mendeleev_number", "mendeleev_number", 0),
    ("pettifor_number", "pettifor_number", 0),
)

_TEXT_FIELDS: tuple[tuple[str, str], ...] = (
    ("cas", "cas_number"),
    ("lattice_structure", "lattice_structure"),
    ("goldschmidt_class", "goldschmidt_class"),
    ("geochemical_class", "geochemical_class"),
    ("jmol_color", "cpk_colour"),
    ("discoverers", "discoverers"),
    ("discovery_location", "discovery_location"),
    ("name_origin", "name_origin"),
    ("description", "description"),
    ("uses", "uses"),
    ("sources", "sources"),
)

#: How many successive ionization energies to keep.
#:
#: Five is where the chemistry stops being routine: the jump between the last
#: valence electron and the first core one is the thing these numbers are read
#: for, and five reaches it for every main-group element without carrying the
#: dozens of core values nobody consults from a periodic table.
_IONIZATION_STAGES = 5


def _extra_properties() -> tuple[dict[int, dict], dict[int, tuple]]:
    properties: dict[int, dict] = {}
    isotopes: dict[int, tuple] = {}
    for number in range(1, MAX_Z + 1):
        item = _element(number)
        record: dict[str, Any] = {}
        for attribute, name, digits in _NUMERIC_FIELDS:
            value = getattr(item, attribute, None)
            if value is None:
                continue
            record[name] = int(value) if digits == 0 else _round(value, digits)
        for attribute, name in _TEXT_FIELDS:
            value = _clean(getattr(item, attribute, None))
            if value is not None:
                record[name] = value
        energies = getattr(item, "ionenergies", None) or {}
        staged: list[float] = []
        for stage in range(1, _IONIZATION_STAGES + 1):
            value = _round(energies.get(stage), 4)
            # Stop at the first gap rather than carrying a null through it. A
            # list with a hole in the middle reads as a list, and a client that
            # indexes it gets the wrong stage for every entry after the hole.
            if value is None:
                break
            staged.append(value)
        if staged:
            record["ionization_energies_ev"] = staged
        properties[number] = record

        natural = tuple(
            (isotope.mass_number, _round(isotope.abundance, 6), _round(isotope.mass, 8))
            for isotope in sorted(item.isotopes, key=lambda i: i.mass_number)
            if isotope.abundance
        )
        if natural:
            isotopes[number] = natural
    return properties, isotopes


def _write(path: Path, header: list[str], tables: list[tuple[str, str, dict]]) -> None:
    out = list(header)
    for name, annotation, table in tables:
        out.append(f"{name}: {annotation} = {{")
        for key, value in table.items():
            out.append(f"    {key}: {value!r},")
        out.append("}")
        out.append("")
    path.write_text("\n".join(out), encoding="utf-8")


def _write_xray(edges: dict[int, dict], lines: dict[int, dict]) -> None:
    header = [
        '"""Characteristic X-ray edges and emission lines. Generated; do not edit.',
        "",
        "Regenerate with ``python scripts/generate_reference_data.py``.",
        "",
        "Energies are in electronvolts. Absorption edges are",
        "``level: (energy_eV, fluorescence_yield, jump_ratio)``; emission lines are",
        "``Siegbahn name: (energy_eV, relative_intensity, initial_level, final_level)``,",
        "where the relative intensity is normalised within the line's own series, so",
        "comparing Ka1 with Ka2 is meaningful and comparing Ka1 with La1 is not.",
        "",
        "Source: W. T. Elam, B. D. Ravel and J. R. Sieber, Radiation Physics and",
        "Chemistry 63 (2002) 121, via the ``xraydb`` package. The tables cover",
        f"Z = 1 to {MAX_XRAY_Z}; heavier elements are absent because their X-ray spectra",
        "have not been measured, not because this file is incomplete.",
        "",
        f"Generated {_dt.date.today().isoformat()} from xraydb {xraydb.__version__}.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        '__all__ = ["MAX_XRAY_Z", "XRAY_EDGES", "XRAY_LINES"]',
        "",
        f"MAX_XRAY_Z = {MAX_XRAY_Z}",
        "",
    ]
    _write(
        PACKAGE / "xray_data.py",
        header,
        [
            ("XRAY_EDGES", "dict[int, dict[str, tuple[float, float, float]]]", edges),
            (
                "XRAY_LINES",
                "dict[int, dict[str, tuple[float, float, str, str]]]",
                lines,
            ),
        ],
    )


def _write_extras(properties: dict[int, dict], isotopes: dict[int, tuple]) -> None:
    import mendeleev

    header = [
        '"""Element properties beyond the core table. Generated; do not edit.',
        "",
        "Regenerate with ``python scripts/generate_reference_data.py``.",
        "",
        "These are the properties the hand-checked table in ``periodic_table`` does",
        "not carry. Nothing here duplicates a value that table already has, so no",
        "property has two possible answers depending on which field a caller reads.",
        "A property missing from an element's dictionary has no published value.",
        "",
        "``NATURAL_ISOTOPES`` lists only isotopes with a measured natural abundance,",
        "as ``(mass number, abundance percent, atomic mass in u)``. An element absent",
        "from it has no primordial isotopes: it is synthetic, or every isotope of it",
        "is too short-lived to survive in nature.",
        "",
        "Source: the ``mendeleev`` package, compiling CRC Handbook, NIST and IUPAC",
        "values.",
        "",
        f"Generated {_dt.date.today().isoformat()} from mendeleev {mendeleev.__version__}.",
        '"""',
        "",
        "from __future__ import annotations",
        "",
        "from typing import Any",
        "",
        '__all__ = ["EXTRA_PROPERTIES", "NATURAL_ISOTOPES"]',
        "",
    ]
    _write(
        PACKAGE / "element_extras.py",
        header,
        [
            ("EXTRA_PROPERTIES", "dict[int, dict[str, Any]]", properties),
            (
                "NATURAL_ISOTOPES",
                "dict[int, tuple[tuple[int, float, float], ...]]",
                isotopes,
            ),
        ],
    )


def main() -> None:
    edges, lines = _xray_tables()
    properties, isotopes = _extra_properties()
    _write_xray(edges, lines)
    _write_extras(properties, isotopes)
    print(
        f"Wrote X-ray data for {len(lines)} elements and extra properties for "
        f"{len(properties)}, with natural isotopes for {len(isotopes)}."
    )


if __name__ == "__main__":
    main()
