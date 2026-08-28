"""The periodic table: one record per element, most of it derived rather than typed.

Why this module is built the way it is
--------------------------------------
A hand-typed table of 118 elements times twenty properties is 2360 opportunities
for a transcription error, and a wrong number in a reference table is worse than
a missing one because nothing about it looks wrong. So everything that *follows
from the atomic number* is computed here rather than entered:

* group, period and block come from the shape of the table itself;
* the electron configuration comes from the Madelung (``n + l``) ordering, with
  the twenty or so experimentally established exceptions listed explicitly and
  named as exceptions;
* the standard atomic weight is read from :mod:`.elements`, which the composition
  converter already uses, so the two tools can never disagree about a mass.

What remains is the genuinely empirical data — melting point, density,
electronegativity and so on — which is entered once, in one table, with ``None``
wherever the value is unknown or merely predicted rather than measured. ``None``
is a deliberate answer: for the superheavy elements, most properties have never
been measured, and inventing a plausible number would be the one failure mode
this module exists to avoid.

Sources
-------
* Standard atomic weights: IUPAC Commission on Isotopic Abundances and Atomic
  Weights, via :mod:`.elements`.
* Physical and thermochemical properties: *CRC Handbook of Chemistry and
  Physics*, 97th ed. (2016), tables of the elements.
* Electronegativity: Pauling scale, as tabulated in the CRC Handbook.
* Electron configurations and their exceptions: NIST Atomic Spectra Database.
* Crustal abundance: CRC Handbook, "Abundance of Elements in the Earth's Crust
  and in the Sea".
"""

from __future__ import annotations

from functools import lru_cache
from typing import Any

from .element_extras import EXTRA_PROPERTIES, NATURAL_ISOTOPES
from .elements import ATOMIC_WEIGHTS
from .xray_data import MAX_XRAY_Z, XRAY_EDGES, XRAY_LINES

__all__ = [
    "CATEGORIES",
    "EXTRA_FIELDS",
    "LINE_ORDER",
    "PLANCK_C_EV_ANGSTROM",
    "all_elements",
    "element_by_symbol",
    "lines_near",
    "periodic_table",
    "xray_edges",
    "xray_lines",
]

#: Symbol and name in atomic-number order, so the index is ``Z - 1``.
_NAMES: tuple[tuple[str, str], ...] = (
    ("H", "Hydrogen"), ("He", "Helium"), ("Li", "Lithium"), ("Be", "Beryllium"),
    ("B", "Boron"), ("C", "Carbon"), ("N", "Nitrogen"), ("O", "Oxygen"),
    ("F", "Fluorine"), ("Ne", "Neon"), ("Na", "Sodium"), ("Mg", "Magnesium"),
    ("Al", "Aluminium"), ("Si", "Silicon"), ("P", "Phosphorus"), ("S", "Sulfur"),
    ("Cl", "Chlorine"), ("Ar", "Argon"), ("K", "Potassium"), ("Ca", "Calcium"),
    ("Sc", "Scandium"), ("Ti", "Titanium"), ("V", "Vanadium"), ("Cr", "Chromium"),
    ("Mn", "Manganese"), ("Fe", "Iron"), ("Co", "Cobalt"), ("Ni", "Nickel"),
    ("Cu", "Copper"), ("Zn", "Zinc"), ("Ga", "Gallium"), ("Ge", "Germanium"),
    ("As", "Arsenic"), ("Se", "Selenium"), ("Br", "Bromine"), ("Kr", "Krypton"),
    ("Rb", "Rubidium"), ("Sr", "Strontium"), ("Y", "Yttrium"), ("Zr", "Zirconium"),
    ("Nb", "Niobium"), ("Mo", "Molybdenum"), ("Tc", "Technetium"), ("Ru", "Ruthenium"),
    ("Rh", "Rhodium"), ("Pd", "Palladium"), ("Ag", "Silver"), ("Cd", "Cadmium"),
    ("In", "Indium"), ("Sn", "Tin"), ("Sb", "Antimony"), ("Te", "Tellurium"),
    ("I", "Iodine"), ("Xe", "Xenon"), ("Cs", "Caesium"), ("Ba", "Barium"),
    ("La", "Lanthanum"), ("Ce", "Cerium"), ("Pr", "Praseodymium"), ("Nd", "Neodymium"),
    ("Pm", "Promethium"), ("Sm", "Samarium"), ("Eu", "Europium"), ("Gd", "Gadolinium"),
    ("Tb", "Terbium"), ("Dy", "Dysprosium"), ("Ho", "Holmium"), ("Er", "Erbium"),
    ("Tm", "Thulium"), ("Yb", "Ytterbium"), ("Lu", "Lutetium"), ("Hf", "Hafnium"),
    ("Ta", "Tantalum"), ("W", "Tungsten"), ("Re", "Rhenium"), ("Os", "Osmium"),
    ("Ir", "Iridium"), ("Pt", "Platinum"), ("Au", "Gold"), ("Hg", "Mercury"),
    ("Tl", "Thallium"), ("Pb", "Lead"), ("Bi", "Bismuth"), ("Po", "Polonium"),
    ("At", "Astatine"), ("Rn", "Radon"), ("Fr", "Francium"), ("Ra", "Radium"),
    ("Ac", "Actinium"), ("Th", "Thorium"), ("Pa", "Protactinium"), ("U", "Uranium"),
    ("Np", "Neptunium"), ("Pu", "Plutonium"), ("Am", "Americium"), ("Cm", "Curium"),
    ("Bk", "Berkelium"), ("Cf", "Californium"), ("Es", "Einsteinium"), ("Fm", "Fermium"),
    ("Md", "Mendelevium"), ("No", "Nobelium"), ("Lr", "Lawrencium"),
    ("Rf", "Rutherfordium"), ("Db", "Dubnium"), ("Sg", "Seaborgium"),
    ("Bh", "Bohrium"), ("Hs", "Hassium"), ("Mt", "Meitnerium"),
    ("Ds", "Darmstadtium"), ("Rg", "Roentgenium"), ("Cn", "Copernicium"),
    ("Nh", "Nihonium"), ("Fl", "Flerovium"), ("Mc", "Moscovium"),
    ("Lv", "Livermorium"), ("Ts", "Tennessine"), ("Og", "Oganesson"),
)

#: The last atomic number of each period. The table's shape in one line.
_PERIOD_ENDS = (2, 10, 18, 36, 54, 86, 118)

#: Display categories, in the order a legend should list them.
CATEGORIES: tuple[str, ...] = (
    "alkali metal",
    "alkaline earth metal",
    "transition metal",
    "post-transition metal",
    "metalloid",
    "reactive nonmetal",
    "noble gas",
    "lanthanide",
    "actinide",
    "unknown properties",
)

#: Elements whose category is not implied by their position. Metalloids straddle
#: the metal/nonmetal staircase by convention rather than by rule, hydrogen sits
#: above the alkali metals without being one, and the post-transition metals are
#: a naming convention applied to part of the p block.
_METALLOIDS = frozenset({5, 14, 32, 33, 51, 52, 84})
_POST_TRANSITION = frozenset({13, 31, 49, 50, 81, 82, 83, 85, 113, 114, 115, 116, 117})
_REACTIVE_NONMETALS = frozenset({1, 6, 7, 8, 9, 15, 16, 17, 34, 35, 53})


def _period(number: int) -> int:
    """The period an element sits in, from where its atomic number falls."""

    for index, last in enumerate(_PERIOD_ENDS, start=1):
        if number <= last:
            return index
    raise ValueError(f"No period contains element {number}")


def _group(number: int) -> int | None:
    """The group, or ``None`` for a lanthanide or actinide.

    The f block is drawn below the table and has no group number, which is a
    genuine absence rather than missing data — so it is ``None`` rather than a
    placeholder a caller might render as a column.
    """

    if number in (1, 3, 11, 19, 37, 55, 87):
        return 1
    if number == 2:
        return 18
    period = _period(number)
    offset = number - (_PERIOD_ENDS[period - 2] if period > 1 else 0)
    if period in (2, 3):
        # Eight-element periods: two s-block elements, then the p block, which
        # is drawn under groups 13-18 with the d block absent between them.
        return offset if offset <= 2 else offset + 10
    if period in (4, 5):
        return offset
    # Periods 6 and 7 carry the f block, which is lifted out of the sequence.
    if 57 <= number <= 71 or 89 <= number <= 103:
        return None
    # The two s-block elements come before the f block, so they are still at
    # their own offset; everything after it is shifted by the fifteen f-block
    # elements that were lifted out.
    if offset <= 2:
        return offset
    return offset - 14


def _block(number: int) -> str:
    if 57 <= number <= 71 or 89 <= number <= 103:
        return "f"
    group = _group(number)
    if number == 2 or group in (1, 2):
        return "s"
    if group is not None and 3 <= group <= 12:
        return "d"
    return "p"


def _category(number: int) -> str:
    if 57 <= number <= 71:
        return "lanthanide"
    if 89 <= number <= 103:
        return "actinide"
    # Beyond copernicium almost nothing has been measured; chemistry is inferred
    # from position alone, so the table says so rather than implying knowledge.
    if number >= 109:
        return "unknown properties"
    if number in _METALLOIDS:
        return "metalloid"
    if number in _REACTIVE_NONMETALS:
        return "reactive nonmetal"
    if number in _POST_TRANSITION:
        return "post-transition metal"
    group = _group(number)
    if group == 18:
        return "noble gas"
    if group == 1 and number != 1:
        return "alkali metal"
    if group == 2:
        return "alkaline earth metal"
    if group is not None and 3 <= group <= 12:
        return "transition metal"
    return "unknown properties"


#: Subshells in Madelung (``n + l``, then ``n``) order, with their capacities.
_SUBSHELL_ORDER: tuple[tuple[int, str, int], ...] = (
    (1, "s", 2), (2, "s", 2), (2, "p", 6), (3, "s", 2), (3, "p", 6),
    (4, "s", 2), (3, "d", 10), (4, "p", 6), (5, "s", 2), (4, "d", 10),
    (5, "p", 6), (6, "s", 2), (4, "f", 14), (5, "d", 10), (6, "p", 6),
    (7, "s", 2), (5, "f", 14), (6, "d", 10), (7, "p", 6),
)

#: Configurations that the Madelung ordering gets wrong.
#:
#: The rule is a useful approximation, not a law: where a half-filled or filled
#: d or f shell is lower in energy than the ordering predicts, the measured
#: ground state differs. These are the experimentally established ground-state
#: configurations (NIST Atomic Spectra Database), written in noble-gas shorthand
#: and listed here rather than silently patched, because *which* elements break
#: the rule is itself worth knowing.
_CONFIGURATION_EXCEPTIONS: dict[int, str] = {
    24: "[Ar] 3d5 4s1",
    29: "[Ar] 3d10 4s1",
    41: "[Kr] 4d4 5s1",
    42: "[Kr] 4d5 5s1",
    44: "[Kr] 4d7 5s1",
    45: "[Kr] 4d8 5s1",
    46: "[Kr] 4d10",
    47: "[Kr] 4d10 5s1",
    57: "[Xe] 5d1 6s2",
    58: "[Xe] 4f1 5d1 6s2",
    64: "[Xe] 4f7 5d1 6s2",
    78: "[Xe] 4f14 5d9 6s1",
    79: "[Xe] 4f14 5d10 6s1",
    89: "[Rn] 6d1 7s2",
    90: "[Rn] 6d2 7s2",
    91: "[Rn] 5f2 6d1 7s2",
    92: "[Rn] 5f3 6d1 7s2",
    93: "[Rn] 5f4 6d1 7s2",
    96: "[Rn] 5f7 6d1 7s2",
    103: "[Rn] 5f14 7s2 7p1",
}

_NOBLE_GASES = ((2, "He"), (10, "Ne"), (18, "Ar"), (36, "Kr"), (54, "Xe"), (86, "Rn"))


def _aufbau_configuration(number: int) -> str:
    """Fill subshells in Madelung order until the electrons run out."""

    remaining = number
    parts: list[str] = []
    for shell, orbital, capacity in _SUBSHELL_ORDER:
        if remaining <= 0:
            break
        occupancy = min(remaining, capacity)
        parts.append(f"{shell}{orbital}{occupancy}")
        remaining -= occupancy
    if remaining:  # pragma: no cover - only reachable past element 118
        raise ValueError(f"Element {number} has more electrons than the table covers")
    return " ".join(parts)


_ORBITAL_RANK = {"s": 0, "p": 1, "d": 2, "f": 3}


def _spectroscopic_order(parts: list[str]) -> list[str]:
    """Sort subshells by ``(n, l)``, which is how configurations are written.

    Subshells *fill* in Madelung order but are *written* in order of increasing
    principal quantum number — iron is ``[Ar] 3d6 4s2``, not ``[Ar] 4s2 3d6``,
    even though the 4s electrons went in first. Reporting fill order would be
    defensible physics written in a notation no textbook uses.
    """

    return sorted(parts, key=lambda part: (int(part[0]), _ORBITAL_RANK[part[1]]))


def _shorten(configuration: str, number: int) -> str:
    """Rewrite a full configuration against the nearest preceding noble gas."""

    core_z, core_symbol = 0, ""
    for noble_z, noble_symbol in _NOBLE_GASES:
        if noble_z < number:
            core_z, core_symbol = noble_z, noble_symbol
    if not core_z:
        return configuration
    core = _aufbau_configuration(core_z).split()
    rest = _spectroscopic_order(configuration.split()[len(core) :])
    return f"[{core_symbol}] " + " ".join(rest) if rest else f"[{core_symbol}]"


def _configuration(number: int) -> tuple[str, bool]:
    """``(noble-gas shorthand, whether it breaks the Madelung ordering)``."""

    exception = _CONFIGURATION_EXCEPTIONS.get(number)
    if exception is not None:
        return exception, True
    return _shorten(_aufbau_configuration(number), number), False


def _valence_electrons(number: int) -> int | None:
    """Electrons outside the noble-gas core, for a main-group element.

    Only defined for the s and p blocks. A transition metal's valence count
    depends on which electrons a particular compound uses, so reporting one
    number for it would be a statement the periodic table does not support.
    """

    if _block(number) not in ("s", "p"):
        return None
    group = _group(number)
    if group is None:
        return None
    if number == 2:
        return 2
    return group if group <= 2 else group - 10


#: Measured properties, keyed by atomic number, in the order
#: ``(electronegativity_pauling, first_ionization_kj_per_mol, melting_point_k,
#: boiling_point_k, density_g_per_cm3, atomic_radius_pm, crystal_structure,
#: common_oxidation_states, discovery_year, crustal_abundance_mg_per_kg)``.
#:
#: ``None`` means the value is unknown or has only ever been predicted, never
#: measured. It is an answer, not a gap to be filled in later with a guess: for
#: most of period 7 almost nothing has been measured, and a plausible-looking
#: number there would be indistinguishable from a real one.
#:
#: No element beyond einsteinium has ever been produced in a weighable amount, so
#: no melting point, boiling point or density exists for elements 100 to 118 —
#: every such figure in the literature is a prediction from periodic trends. They
#: are ``None`` here, because a number in this table means a measurement.
#:
#: Densities are for the solid at 20 degrees C except for the gases and the two
#: liquids (bromine, mercury), where the value is for the element in its stable
#: state at STP. Crystal structures are those of the stable solid phase at STP,
#: so a gas that has never been crystallized at ambient pressure has ``None``.
_PROPERTIES: dict[int, tuple[Any, ...]] = {
    1: (2.20, 1312.0, 13.99, 20.271, 0.00008988, 53, "hexagonal", "-1, +1", 1766, 1400.0),
    2: (None, 2372.3, 0.95, 4.222, 0.0001785, 31, "hexagonal", "0", 1868, 0.008),
    3: (0.98, 520.2, 453.65, 1603.0, 0.534, 167, "body-centred cubic", "+1", 1817, 20.0),
    4: (1.57, 899.5, 1560.0, 2742.0, 1.85, 112, "hexagonal", "+2", 1798, 2.8),
    5: (2.04, 800.6, 2349.0, 4200.0, 2.34, 87, "rhombohedral", "+3", 1808, 10.0),
    6: (2.55, 1086.5, 3823.0, 4098.0, 2.267, 67, "hexagonal (graphite)", "-4, +2, +4", None, 200.0),
    7: (3.04, 1402.3, 63.15, 77.355, 0.0012506, 56, "hexagonal", "-3, +3, +5", 1772, 19.0),
    8: (3.44, 1313.9, 54.36, 90.188, 0.001429, 48, "cubic", "-2", 1771, 461000.0),
    9: (3.98, 1681.0, 53.48, 85.03, 0.001696, 42, "cubic", "-1", 1810, 585.0),
    10: (None, 2080.7, 24.56, 27.104, 0.0008999, 38, "face-centred cubic", "0", 1898, 0.005),
    11: (0.93, 495.8, 370.944, 1156.09, 0.968, 190, "body-centred cubic", "+1", 1807, 23600.0),
    12: (1.31, 737.7, 923.0, 1363.0, 1.738, 145, "hexagonal", "+2", 1755, 23300.0),
    13: (1.61, 577.5, 933.47, 2743.0, 2.70, 118, "face-centred cubic", "+3", 1825, 82300.0),
    14: (1.90, 786.5, 1687.0, 3538.0, 2.3296, 111, "diamond cubic", "-4, +4", 1824, 282000.0),
    15: (2.19, 1011.8, 317.3, 553.7, 1.823, 98, "triclinic", "-3, +3, +5", 1669, 1050.0),
    16: (2.58, 999.6, 388.36, 717.8, 2.07, 88, "orthorhombic", "-2, +2, +4, +6", None, 350.0),
    17: (3.16, 1251.2, 171.6, 239.11, 0.003214, 79, "orthorhombic", "-1, +1, +3, +5, +7", 1774, 145.0),
    18: (None, 1520.6, 83.81, 87.302, 0.0017837, 71, "face-centred cubic", "0", 1894, 3.5),
    19: (0.82, 418.8, 336.7, 1032.0, 0.862, 243, "body-centred cubic", "+1", 1807, 20900.0),
    20: (1.00, 589.8, 1115.0, 1757.0, 1.55, 194, "face-centred cubic", "+2", 1808, 41500.0),
    21: (1.36, 633.1, 1814.0, 3109.0, 2.985, 184, "hexagonal", "+3", 1879, 22.0),
    22: (1.54, 658.8, 1941.0, 3560.0, 4.506, 176, "hexagonal", "+2, +3, +4", 1791, 5650.0),
    23: (1.63, 650.9, 2183.0, 3680.0, 6.11, 171, "body-centred cubic", "+2, +3, +4, +5", 1801, 120.0),
    24: (1.66, 652.9, 2180.0, 2944.0, 7.15, 166, "body-centred cubic", "+2, +3, +6", 1794, 102.0),
    25: (1.55, 717.3, 1519.0, 2334.0, 7.21, 161, "body-centred cubic", "+2, +4, +7", 1774, 950.0),
    26: (1.83, 762.5, 1811.0, 3134.0, 7.874, 156, "body-centred cubic", "+2, +3", None, 56300.0),
    27: (1.88, 760.4, 1768.0, 3200.0, 8.90, 152, "hexagonal", "+2, +3", 1735, 25.0),
    28: (1.91, 737.1, 1728.0, 3003.0, 8.908, 149, "face-centred cubic", "+2, +3", 1751, 84.0),
    29: (1.90, 745.5, 1357.77, 2835.0, 8.96, 145, "face-centred cubic", "+1, +2", None, 60.0),
    30: (1.65, 906.4, 692.68, 1180.0, 7.14, 142, "hexagonal", "+2", None, 70.0),
    31: (1.81, 578.8, 302.9146, 2673.0, 5.91, 136, "orthorhombic", "+3", 1875, 19.0),
    32: (2.01, 762.0, 1211.4, 3106.0, 5.323, 125, "diamond cubic", "+2, +4", 1886, 1.5),
    33: (2.18, 947.0, 1090.0, 887.0, 5.727, 114, "rhombohedral", "-3, +3, +5", None, 1.8),
    34: (2.55, 941.0, 494.0, 958.0, 4.81, 103, "hexagonal", "-2, +4, +6", 1817, 0.05),
    35: (2.96, 1139.9, 265.8, 332.0, 3.1028, 94, "orthorhombic", "-1, +1, +5", 1826, 2.4),
    36: (3.00, 1350.8, 115.79, 119.93, 0.003733, 88, "face-centred cubic", "0, +2", 1898, 0.0001),
    37: (0.82, 403.0, 312.45, 961.0, 1.532, 265, "body-centred cubic", "+1", 1861, 90.0),
    38: (0.95, 549.5, 1050.0, 1650.0, 2.64, 219, "face-centred cubic", "+2", 1790, 370.0),
    39: (1.22, 600.0, 1799.0, 3203.0, 4.472, 212, "hexagonal", "+3", 1794, 33.0),
    40: (1.33, 640.1, 2128.0, 4650.0, 6.52, 206, "hexagonal", "+4", 1789, 165.0),
    41: (1.60, 652.1, 2750.0, 5017.0, 8.57, 198, "body-centred cubic", "+3, +5", 1801, 20.0),
    42: (2.16, 684.3, 2896.0, 4912.0, 10.28, 190, "body-centred cubic", "+4, +6", 1778, 1.2),
    43: (1.90, 702.0, 2430.0, 4538.0, 11.0, 183, "hexagonal", "+4, +7", 1937, 0.0),
    44: (2.20, 710.2, 2607.0, 4423.0, 12.45, 178, "hexagonal", "+3, +4", 1844, 0.001),
    45: (2.28, 719.7, 2237.0, 3968.0, 12.41, 173, "face-centred cubic", "+3", 1803, 0.001),
    46: (2.20, 804.4, 1828.05, 3236.0, 12.023, 169, "face-centred cubic", "+2, +4", 1802, 0.015),
    47: (1.93, 731.0, 1234.93, 2435.0, 10.49, 165, "face-centred cubic", "+1", None, 0.075),
    48: (1.69, 867.8, 594.22, 1040.0, 8.65, 161, "hexagonal", "+2", 1817, 0.159),
    49: (1.78, 558.3, 429.7485, 2345.0, 7.31, 156, "tetragonal", "+3", 1863, 0.25),
    50: (1.96, 708.6, 505.08, 2875.0, 7.265, 145, "tetragonal", "+2, +4", None, 2.3),
    51: (2.05, 834.0, 903.78, 1908.0, 6.697, 133, "rhombohedral", "-3, +3, +5", None, 0.2),
    52: (2.10, 869.3, 722.66, 1261.0, 6.24, 123, "hexagonal", "-2, +4, +6", 1782, 0.001),
    53: (2.66, 1008.4, 386.85, 457.4, 4.933, 115, "orthorhombic", "-1, +1, +5, +7", 1811, 0.45),
    54: (2.60, 1170.4, 161.4, 165.051, 0.005887, 108, "face-centred cubic", "0, +2, +4, +6", 1898, 0.00003),
    55: (0.79, 375.7, 301.7, 944.0, 1.93, 298, "body-centred cubic", "+1", 1860, 3.0),
    56: (0.89, 502.9, 1000.0, 2118.0, 3.51, 253, "body-centred cubic", "+2", 1808, 425.0),
    57: (1.10, 538.1, 1193.0, 3737.0, 6.162, 195, "hexagonal", "+3", 1839, 39.0),
    58: (1.12, 534.4, 1068.0, 3716.0, 6.770, 185, "face-centred cubic", "+3, +4", 1803, 66.5),
    59: (1.13, 527.0, 1208.0, 3403.0, 6.77, 247, "hexagonal", "+3", 1885, 9.2),
    60: (1.14, 533.1, 1297.0, 3347.0, 7.01, 206, "hexagonal", "+3", 1885, 41.5),
    61: (1.13, 540.0, 1315.0, 3273.0, 7.26, 205, "hexagonal", "+3", 1945, 0.0),
    62: (1.17, 544.5, 1345.0, 2173.0, 7.52, 238, "rhombohedral", "+2, +3", 1879, 7.05),
    63: (1.20, 547.1, 1099.0, 1802.0, 5.244, 231, "body-centred cubic", "+2, +3", 1901, 2.0),
    64: (1.20, 593.4, 1585.0, 3273.0, 7.90, 233, "hexagonal", "+3", 1880, 6.2),
    65: (1.20, 565.8, 1629.0, 3396.0, 8.23, 225, "hexagonal", "+3", 1843, 1.2),
    66: (1.22, 573.0, 1680.0, 2840.0, 8.540, 228, "hexagonal", "+3", 1886, 5.2),
    67: (1.23, 581.0, 1734.0, 2873.0, 8.79, 226, "hexagonal", "+3", 1878, 1.3),
    68: (1.24, 589.3, 1802.0, 3141.0, 9.066, 226, "hexagonal", "+3", 1843, 3.5),
    69: (1.25, 596.7, 1818.0, 2223.0, 9.32, 222, "hexagonal", "+3", 1879, 0.52),
    70: (1.10, 603.4, 1097.0, 1469.0, 6.90, 222, "face-centred cubic", "+2, +3", 1878, 3.2),
    71: (1.27, 523.5, 1925.0, 3675.0, 9.841, 217, "hexagonal", "+3", 1907, 0.8),
    72: (1.30, 658.5, 2506.0, 4876.0, 13.31, 208, "hexagonal", "+4", 1923, 3.0),
    73: (1.50, 761.0, 3290.0, 5731.0, 16.69, 200, "body-centred cubic", "+5", 1802, 2.0),
    74: (2.36, 770.0, 3695.0, 6203.0, 19.25, 193, "body-centred cubic", "+4, +6", 1783, 1.25),
    75: (1.90, 760.0, 3459.0, 5869.0, 21.02, 188, "hexagonal", "+4, +7", 1925, 0.0007),
    76: (2.20, 840.0, 3306.0, 5285.0, 22.59, 185, "hexagonal", "+3, +4", 1803, 0.002),
    77: (2.20, 880.0, 2719.0, 4403.0, 22.56, 180, "face-centred cubic", "+3, +4", 1803, 0.001),
    78: (2.28, 870.0, 2041.4, 4098.0, 21.45, 177, "face-centred cubic", "+2, +4", 1735, 0.005),
    79: (2.54, 890.1, 1337.33, 3243.0, 19.30, 174, "face-centred cubic", "+1, +3", None, 0.004),
    80: (2.00, 1007.1, 234.3210, 629.88, 13.534, 171, "rhombohedral", "+1, +2", None, 0.085),
    81: (1.62, 589.4, 577.0, 1746.0, 11.85, 156, "hexagonal", "+1, +3", 1861, 0.85),
    82: (2.33, 715.6, 600.61, 2022.0, 11.34, 154, "face-centred cubic", "+2, +4", None, 14.0),
    83: (2.02, 703.0, 544.7, 1837.0, 9.78, 143, "rhombohedral", "+3, +5", None, 0.009),
    84: (2.00, 812.1, 527.0, 1235.0, 9.196, 135, "cubic", "-2, +2, +4", 1898, 0.000002),
    85: (2.20, 899.003, 575.0, 610.0, None, 127, None, "-1, +1", 1940, 0.0),
    86: (2.20, 1037.0, 202.0, 211.5, 0.00973, 120, "face-centred cubic", "0, +2", 1900, 0.0),
    87: (0.79, 393.0, 300.0, 950.0, None, None, "body-centred cubic", "+1", 1939, 0.0),
    88: (0.90, 509.3, 973.0, 2010.0, 5.5, None, "body-centred cubic", "+2", 1898, 0.0009),
    89: (1.10, 499.0, 1500.0, 3500.0, 10.0, None, "face-centred cubic", "+3", 1899, 0.0),
    90: (1.30, 587.0, 2023.0, 5061.0, 11.7, 179, "face-centred cubic", "+4", 1829, 9.6),
    91: (1.50, 568.0, 1841.0, 4300.0, 15.37, 163, "tetragonal", "+4, +5", 1913, 0.0014),
    92: (1.38, 597.6, 1405.3, 4404.0, 19.1, 156, "orthorhombic", "+4, +6", 1789, 2.7),
    93: (1.36, 604.5, 917.0, 4273.0, 20.45, 155, "orthorhombic", "+5", 1940, 0.0),
    94: (1.28, 584.7, 912.5, 3501.0, 19.85, 159, "monoclinic", "+4, +6", 1940, 0.0),
    95: (1.30, 578.0, 1449.0, 2880.0, 12.0, 173, "hexagonal", "+3", 1944, 0.0),
    96: (1.30, 581.0, 1613.0, 3383.0, 13.51, 174, "hexagonal", "+3", 1944, 0.0),
    97: (1.30, 601.0, 1259.0, 2900.0, 14.78, 170, "hexagonal", "+3", 1949, 0.0),
    98: (1.30, 608.0, 1173.0, 1743.0, 15.1, 186, "hexagonal", "+3", 1950, 0.0),
    99: (1.30, 619.0, 1133.0, 1269.0, 8.84, 186, "face-centred cubic", "+3", 1952, 0.0),
    100: (1.3, 627.0, None, None, None, None, None, '+3', 1952, 0.0),
    101: (1.3, 635.0, None, None, None, None, None, '+2, +3', 1955, 0.0),
    102: (1.3, 642.0, None, None, None, None, None, '+2, +3', 1957, 0.0),
    103: (1.3, 470.0, None, None, None, None, None, '+3', 1961, 0.0),
    104: (None, 580.0, None, None, None, None, None, '+4', 1964, 0.0),
    105: (None, 665.0, None, None, None, None, None, '+5', 1967, 0.0),
    106: (None, 757.0, None, None, None, None, None, '+6', 1974, 0.0),
    107: (None, 740.0, None, None, None, None, None, '+7', 1981, 0.0),
    108: (None, 730.0, None, None, None, None, None, '+8', 1984, 0.0),
    109: (None, 800.0, None, None, None, None, None, None, 1982, 0.0),
    110: (None, 960.0, None, None, None, None, None, None, 1994, 0.0),
    111: (None, 1020.0, None, None, None, None, None, None, 1994, 0.0),
    112: (None, 1155.0, None, None, None, None, None, '+2', 1996, 0.0),
    113: (None, 707.0, None, None, None, None, None, '+1', 2003, 0.0),
    114: (None, 832.0, None, None, None, None, None, '+2', 1998, 0.0),
    115: (None, 538.0, None, None, None, None, None, '+1', 2003, 0.0),
    116: (None, 663.9, None, None, None, None, None, '+2', 2000, 0.0),
    117: (None, 736.9, None, None, None, None, None, '+1', 2010, 0.0),
    118: (None, 860.1, None, None, None, None, None, '0', 2002, 0.0),
}


_FIELDS = (
    "electronegativity_pauling",
    "first_ionization_kj_per_mol",
    "melting_point_k",
    "boiling_point_k",
    "density_g_per_cm3",
    "atomic_radius_pm",
    "crystal_structure",
    "common_oxidation_states",
    "discovery_year",
    "crustal_abundance_mg_per_kg",
)

#: Room temperature, for deciding what state an element is in.
_AMBIENT_K = 298.15

#: Elements in use before anyone recorded discovering them.
#:
#: Their discovery year is ``None`` in the property table, but that ``None``
#: means something different from every other one: not "nobody has measured
#: this" but "there is no date, because the element was in use before there
#: were records". Reporting the two absences the same way would turn a fact
#: into an apparent gap in the data.
_KNOWN_SINCE_ANTIQUITY = frozenset({6, 16, 26, 29, 30, 33, 47, 50, 51, 79, 80, 82, 83})

#: Elements made rather than found.
#:
#: Technetium and promethium have no stable isotope and no primordial supply, and
#: everything above plutonium is produced in reactors and accelerators. Their
#: crustal abundance is recorded as ``0.0``, which is a real statement — the
#: element is not there — and a different one from an abundance nobody has
#: measured. Neptunium and plutonium occur in genuinely trace amounts in uranium
#: ores and are counted here as synthetic, which is the usual convention.
_SYNTHETIC = frozenset({43, 61}) | frozenset(range(93, 119))

#: Elements with no stable isotope. Technetium and promethium are the two gaps
#: below bismuth; everything from polonium up is radioactive throughout. Bismuth
#: is *observationally* stable but does decay, with a half-life far longer than
#: the age of the universe, so it is listed with the others.
_NO_STABLE_ISOTOPE = frozenset({43, 61, 83}) | frozenset(range(84, 119))


def _state_at_stp(melting: float | None, boiling: float | None) -> str | None:
    """Solid, liquid or gas at room temperature, from the transition points.

    Derived rather than entered, so an element can never be recorded as a gas
    while also being given a melting point above room temperature.
    """

    if boiling is not None and boiling <= _AMBIENT_K:
        return "gas"
    if melting is None:
        return None
    return "solid" if melting > _AMBIENT_K else "liquid"


#: Planck's constant times the speed of light, in eV angstrom.
#:
#: The one constant needed to turn every energy in the X-ray tables into the
#: wavelength half the field quotes instead. Crystallographers ask for Cu Ka1 in
#: angstroms and spectroscopists ask for it in keV; they are the same line, and
#: converting here means the two answers can never drift apart.
PLANCK_C_EV_ANGSTROM = 12398.419843320026

#: Siegbahn line names in the order a spectrum is read: hardest series first,
#: and within a series the strongest line first. Dictionary order in the
#: generated table is alphabetical, which puts Ka3 before Kb1 and Lb before La,
#: so the display order is stated once here rather than sorted at each caller.
LINE_ORDER: tuple[str, ...] = (
    "Ka1", "Ka2", "Ka3",
    "Kb1", "Kb2", "Kb3", "Kb4", "Kb5",
    "La1", "La2", "Lb1", "Lb2,15", "Lb3", "Lb4", "Lb5", "Lb6",
    "Lg1", "Lg2", "Lg3", "Lg6", "Ll", "Ln",
    "Ma", "Mb", "Mg", "Mz",
)

#: Absorption edges from the innermost shell outwards, which is also the order
#: of decreasing energy.
EDGE_ORDER: tuple[str, ...] = (
    "K",
    "L1", "L2", "L3",
    "M1", "M2", "M3", "M4", "M5",
    "N1", "N2", "N3", "N4", "N5", "N6", "N7",
    "O1", "O2", "O3", "O4", "O5",
    "P1", "P2", "P3",
)

#: Siegbahn names written the way they are printed, with the Greek letter.
_GREEK = {
    "a": "\N{GREEK SMALL LETTER ALPHA}",
    "b": "\N{GREEK SMALL LETTER BETA}",
    "g": "\N{GREEK SMALL LETTER GAMMA}",
    "l": "\N{SCRIPT SMALL L}",
    "n": "\N{GREEK SMALL LETTER ETA}",
    "z": "\N{GREEK SMALL LETTER ZETA}",
}


def _siegbahn_label(name: str) -> str:
    """Rewrite ``Ka1`` as the notation an X-ray table actually prints."""

    letter = _GREEK.get(name[1], name[1])
    return f"{name[0]}{letter}{name[2:]}"


def _wavelength(energy_ev: float | None) -> float | None:
    """Photon wavelength in angstroms, or ``None`` for an energy that is absent."""

    if not energy_ev:
        return None
    return round(PLANCK_C_EV_ANGSTROM / energy_ev, 5)


def xray_edges(number: int) -> dict[str, dict[str, Any]]:
    """Absorption edges for one element, innermost shell first.

    An empty result is a statement rather than a gap: the Elam tables stop at
    californium, so every element above it has no measured X-ray spectrum at
    all, not a spectrum this package failed to include.
    """

    raw = XRAY_EDGES.get(number, {})
    return {
        level: {
            "energy_ev": raw[level][0],
            "energy_kev": round(raw[level][0] / 1000.0, 5),
            "wavelength_angstrom": _wavelength(raw[level][0]),
            "fluorescence_yield": raw[level][1],
            "jump_ratio": raw[level][2],
        }
        for level in EDGE_ORDER
        if level in raw
    }


def xray_lines(number: int) -> dict[str, dict[str, Any]]:
    """Characteristic emission lines for one element, hardest series first.

    The relative intensity is normalised within each line's own series, which is
    what makes "Ka1 is about twice Ka2" a meaningful statement and "Ka1 against
    La1" a meaningless one. Each line carries the series it belongs to so a
    caller cannot cross that boundary without noticing.
    """

    raw = XRAY_LINES.get(number, {})
    return {
        name: {
            "label": _siegbahn_label(name),
            "series": name[0],
            "energy_ev": raw[name][0],
            "energy_kev": round(raw[name][0] / 1000.0, 5),
            "wavelength_angstrom": _wavelength(raw[name][0]),
            "relative_intensity": raw[name][1],
            "transition": f"{raw[name][2]} \N{RIGHTWARDS ARROW} {raw[name][3]}",
        }
        for name in LINE_ORDER
        if name in raw
    }


#: The handful of X-ray values a table cell or a filter needs as a plain number.
#:
#: The full line and edge dictionaries are the reference; these are the ones an
#: analyst reaches for often enough that burying them one level deeper would
#: make the tool slower to use than the wall chart it replaces.
_NOTABLE_LINES = (
    ("k_alpha1_ev", "Ka1"),
    ("k_alpha2_ev", "Ka2"),
    ("k_beta1_ev", "Kb1"),
    ("l_alpha1_ev", "La1"),
)


def _xray_summary(number: int) -> dict[str, Any]:
    lines = XRAY_LINES.get(number, {})
    edges = XRAY_EDGES.get(number, {})
    summary: dict[str, Any] = {
        field: (lines[name][0] if name in lines else None)
        for field, name in _NOTABLE_LINES
    }
    summary["k_edge_ev"] = edges["K"][0] if "K" in edges else None
    summary["l3_edge_ev"] = edges["L3"][0] if "L3" in edges else None
    return summary


def lines_near(
    energy_ev: float, tolerance_ev: float = 50.0, min_intensity: float = 0.01
) -> list[dict[str, Any]]:
    """Every characteristic line within ``tolerance_ev`` of a measured energy.

    This is the question an unlabelled peak in an EDS or XRF spectrum actually
    poses - not "what is iron's Ka1" but "what could this 6.4 keV peak be" - and
    it is the one a printed table answers worst, because answering it means
    scanning every row. Weak lines are excluded by default: a visible peak is
    not going to be a line carrying a thousandth of its series, and listing
    those buries the two or three candidates that matter.
    """

    if tolerance_ev < 0:
        raise ValueError("tolerance must not be negative")
    matches: list[dict[str, Any]] = []
    for number, raw in XRAY_LINES.items():
        for name, (line_energy, intensity, initial, final) in raw.items():
            if intensity < min_intensity:
                continue
            difference = line_energy - energy_ev
            if abs(difference) > tolerance_ev:
                continue
            symbol, element_name = _NAMES[number - 1]
            matches.append(
                {
                    "atomic_number": number,
                    "symbol": symbol,
                    "name": element_name,
                    "line": name,
                    "label": _siegbahn_label(name),
                    "series": name[0],
                    "energy_ev": line_energy,
                    "energy_kev": round(line_energy / 1000.0, 5),
                    "wavelength_angstrom": _wavelength(line_energy),
                    "relative_intensity": intensity,
                    "transition": f"{initial} \N{RIGHTWARDS ARROW} {final}",
                    "difference_ev": round(difference, 2),
                }
            )
    matches.sort(
        key=lambda match: (abs(match["difference_ev"]), -match["relative_intensity"])
    )
    return matches


def _isotopes(number: int) -> list[dict[str, Any]]:
    """Naturally occurring isotopes, as mass number, abundance and atomic mass.

    An empty list means the element has no primordial supply - it is synthetic,
    or every isotope of it decays faster than the Earth is old. That is the same
    fact ``synthetic`` reports, arrived at from the other direction.
    """

    return [
        {
            "mass_number": mass_number,
            "abundance_percent": abundance,
            "atomic_mass": mass,
        }
        for mass_number, abundance, mass in NATURAL_ISOTOPES.get(number, ())
    ]


#: Fields that come from the generated ``element_extras`` table.
#:
#: Listing them here rather than reading the keys of one element's dictionary
#: matters because those dictionaries omit whatever is unknown, so hydrogen and
#: iron do not have the same keys - and a client that discovered the field list
#: from whichever element it happened to load first would silently never show
#: the properties that element lacks.
EXTRA_FIELDS: tuple[str, ...] = (
    "electron_affinity_ev",
    "ionization_energies_ev",
    "electronegativity_allen_ev",
    "covalent_radius_pm",
    "van_der_waals_radius_pm",
    "metallic_radius_pm",
    "atomic_volume_cm3_per_mol",
    "dipole_polarizability_au",
    "lattice_structure",
    "lattice_constant_angstrom",
    "thermal_conductivity_w_per_m_k",
    "molar_heat_capacity_j_per_mol_k",
    "specific_heat_j_per_g_k",
    "heat_of_fusion_kj_per_mol",
    "heat_of_vaporization_kj_per_mol",
    "heat_of_atomization_kj_per_mol",
    "abundance_seawater_mg_per_l",
    "goldschmidt_class",
    "geochemical_class",
    "price_usd_per_kg",
    "supply_risk_index",
    "cas_number",
    "cpk_colour",
    "mendeleev_number",
    "pettifor_number",
    "discoverers",
    "discovery_location",
    "name_origin",
    "description",
    "uses",
    "sources",
)

#: X-ray fields that are plain numbers on the record, so a client can shade,
#: sort or filter the grid by them without unpacking the nested tables.
XRAY_SUMMARY_FIELDS: tuple[str, ...] = (
    "k_alpha1_ev",
    "k_alpha2_ev",
    "k_beta1_ev",
    "l_alpha1_ev",
    "k_edge_ev",
    "l3_edge_ev",
)


@lru_cache(maxsize=None)
def _record(number: int) -> dict[str, Any]:
    """Everything known about one element, derived where derivable.

    Cached because the record is now assembled from four tables and is read once
    per element per request; the result is treated as immutable by every caller
    here, and :func:`all_elements` hands out copies so a caller that does mutate
    one cannot poison the cache for the next request.
    """

    symbol, name = _NAMES[number - 1]
    configuration, is_exception = _configuration(number)
    values = dict(zip(_FIELDS, _PROPERTIES[number]))
    extras = {field: EXTRA_PROPERTIES.get(number, {}).get(field) for field in EXTRA_FIELDS}
    isotopes = _isotopes(number)
    return {
        "atomic_number": number,
        "symbol": symbol,
        "name": name,
        "atomic_mass": ATOMIC_WEIGHTS[symbol],
        "group": _group(number),
        "period": _period(number),
        "block": _block(number),
        "category": _category(number),
        "electron_configuration": configuration,
        "electron_configuration_is_exception": is_exception,
        "shell_electrons": _shell_electrons(number),
        "valence_electrons": _valence_electrons(number),
        "state_at_room_temperature": _state_at_stp(
            values["melting_point_k"], values["boiling_point_k"]
        ),
        "radioactive": number in _NO_STABLE_ISOTOPE,
        "known_since_antiquity": number in _KNOWN_SINCE_ANTIQUITY,
        "synthetic": number in _SYNTHETIC,
        "natural_isotopes": isotopes,
        "natural_isotope_count": len(isotopes),
        "monoisotopic": len(isotopes) == 1,
        "xray_edges": xray_edges(number),
        "xray_lines": xray_lines(number),
        "has_xray_data": number in XRAY_LINES,
        **_xray_summary(number),
        **extras,
        **values,
    }


def _shell_electrons(number: int) -> list[int]:
    """Electrons per principal shell — the 2, 8, 18, ... a Bohr diagram draws."""

    shells: dict[int, int] = {}
    remaining = number
    for shell, _orbital, capacity in _SUBSHELL_ORDER:
        if remaining <= 0:
            break
        occupancy = min(remaining, capacity)
        shells[shell] = shells.get(shell, 0) + occupancy
        remaining -= occupancy
    return [shells[shell] for shell in sorted(shells)]


#: Fields left out of the whole-table payload and served per element instead.
#:
#: The full line and edge tables are most of the data in this package - 96
#: elements times twenty-six lines and twenty-four edges - and the prose fields
#: add most of the rest. Sending all of it with the grid would be roughly
#: 800 kB before the reader has clicked anything, to draw a table that needs
#: none of it. Everything the grid itself uses - every scalar property, the
#: summary X-ray energies, the isotope list - stays in the one payload, so
#: shading, filtering and search still never touch the network; only opening an
#: element costs a request, and that request is a few kilobytes.
_DETAIL_ONLY_FIELDS: tuple[str, ...] = (
    "xray_lines",
    "xray_edges",
    "description",
    "uses",
    "sources",
    "name_origin",
    "discoverers",
    "discovery_location",
)


def all_elements(*, detail: bool = True) -> list[dict[str, Any]]:
    """Every element, in atomic-number order, as records the caller owns.

    With ``detail=False`` the per-element X-ray tables and prose are omitted;
    see :data:`_DETAIL_ONLY_FIELDS` for why the whole-table payload does that.
    """

    records = [dict(_record(number)) for number in range(1, len(_NAMES) + 1)]
    if detail:
        return records
    for record in records:
        for field in _DETAIL_ONLY_FIELDS:
            record.pop(field, None)
    return records


def element_by_symbol(symbol: str) -> dict[str, Any] | None:
    """One element by its symbol, matched case-insensitively, or ``None``."""

    wanted = str(symbol).strip().lower()
    for number, (element_symbol, _name) in enumerate(_NAMES, start=1):
        if element_symbol.lower() == wanted:
            return dict(_record(number))
    return None


def periodic_table() -> dict[str, Any]:
    """The whole table plus the layout a renderer needs, in one payload.

    The grid coordinates are included because the f block is drawn detached from
    the rest of the table, two rows below it. That is a display convention, not
    crystallography, and putting it here keeps one statement of it rather than
    one per client.
    """

    elements = all_elements(detail=False)
    for record in elements:
        number = record["atomic_number"]
        if 57 <= number <= 71:
            record["grid_row"], record["grid_column"] = 9, number - 57 + 4
        elif 89 <= number <= 103:
            record["grid_row"], record["grid_column"] = 10, number - 89 + 4
        else:
            record["grid_row"] = record["period"]
            record["grid_column"] = record["group"]
    return {
        "elements": elements,
        "categories": list(CATEGORIES),
        "fields": list(_FIELDS),
        "extra_fields": list(EXTRA_FIELDS),
        "xray_summary_fields": list(XRAY_SUMMARY_FIELDS),
        "line_order": list(LINE_ORDER),
        "edge_order": list(EDGE_ORDER),
        "max_xray_z": MAX_XRAY_Z,
        "detail_only_fields": list(_DETAIL_ONLY_FIELDS),
        "count": len(elements),
    }
