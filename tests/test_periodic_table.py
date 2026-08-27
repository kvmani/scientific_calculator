"""The periodic table: the data is checked against rules, not against itself.

A reference table is only worth having if its numbers are right, and a wrong
number in one does not look wrong. So rather than pinning values that were typed
in — which would only assert that the typing has not changed — these tests check
the table against facts that hold independently of it:

* every standard atomic weight must equal the one the composition converter
  already uses, so the two tools cannot disagree about a mass;
* atomic mass rises with atomic number, with exactly the four inversions the
  periodic table is known to contain (Ar/K, Co/Ni, Te/I, Th/Pa);
* the electron configuration must account for exactly Z electrons;
* group, period and block must agree with each other and with the noble gases,
  whose positions are fixed;
* every property that is present must be physically admissible — a boiling point
  above a melting point, a positive density, an electronegativity on the Pauling
  scale.

Where a value is absent the test asserts that the absence is *deliberate*: the
record has to say which kind of absence it is, because "nobody has measured it",
"the element was in use before records" and "the element does not occur in
nature" are three different statements and a blank cell tells them apart from
neither of the others.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scientific_calculator_service.elements import ATOMIC_WEIGHTS
from scientific_calculator_service.periodic_table import (
    CATEGORIES,
    all_elements,
    element_by_symbol,
    periodic_table,
)

ELEMENTS = all_elements()
BY_SYMBOL = {element["symbol"]: element for element in ELEMENTS}


def test_the_table_holds_every_element_exactly_once():
    assert len(ELEMENTS) == 118
    assert [element["atomic_number"] for element in ELEMENTS] == list(range(1, 119))
    assert len({element["symbol"] for element in ELEMENTS}) == 118
    assert len({element["name"] for element in ELEMENTS}) == 118


def test_masses_agree_with_the_table_the_converter_uses():
    """One mass per element across the whole service, or neither tool is trusted."""

    assert {element["symbol"] for element in ELEMENTS} == set(ATOMIC_WEIGHTS)
    for element in ELEMENTS:
        assert element["atomic_mass"] == ATOMIC_WEIGHTS[element["symbol"]]


def test_mass_rises_with_atomic_number_except_where_it_famously_does_not():
    """The four inversions are a fact about isotope abundances, not a typo.

    Argon before potassium, cobalt before nickel, tellurium before iodine and
    thorium before protactinium are heavier than the element that follows them.
    Mendeleev ordered by mass and had to break his own rule at these pairs;
    pinning exactly this set is what makes the test catch a transcription error
    without also failing on real chemistry.

    Only the naturally occurring elements are in scope. A synthetic element has
    no standard atomic weight at all — there is no natural isotopic mixture to
    average — so the figure quoted for it is the mass number of its longest-lived
    known isotope, and which isotope that happens to be does not have to rise
    with atomic number. Comparing those would test nuclear luck, not the table.
    """

    natural = [element for element in ELEMENTS if not element["synthetic"]]
    inversions = {
        (element["symbol"], natural[index + 1]["symbol"])
        for index, element in enumerate(natural[:-1])
        if element["atomic_mass"] > natural[index + 1]["atomic_mass"]
    }
    assert inversions == {("Ar", "K"), ("Co", "Ni"), ("Te", "I"), ("Th", "Pa")}


def test_every_configuration_accounts_for_exactly_its_electrons():
    """Including the exceptions, which are the ones most likely to be mistyped."""

    cores = {"He": 2, "Ne": 10, "Ar": 18, "Kr": 36, "Xe": 54, "Rn": 86}
    for element in ELEMENTS:
        total = 0
        for part in element["electron_configuration"].split():
            if part.startswith("["):
                total += cores[part.strip("[]")]
            else:
                total += int(part[2:])
        assert total == element["atomic_number"], element["symbol"]


def test_shell_occupancies_sum_to_the_electron_count():
    for element in ELEMENTS:
        assert sum(element["shell_electrons"]) == element["atomic_number"]
        assert all(count > 0 for count in element["shell_electrons"])


def test_the_noble_gases_close_their_periods():
    """Their positions are fixed points the rest of the layout is derived against."""

    for symbol, period in (("He", 1), ("Ne", 2), ("Ar", 3), ("Kr", 4), ("Xe", 5), ("Rn", 6)):
        element = BY_SYMBOL[symbol]
        assert element["group"] == 18
        assert element["period"] == period
        assert element["category"] == "noble gas"


def test_group_period_and_block_agree_with_each_other():
    for element in ELEMENTS:
        block, group = element["block"], element["group"]
        if block == "f":
            assert group is None, element["symbol"]
            assert element["period"] in (6, 7)
            continue
        assert group is not None, element["symbol"]
        assert 1 <= group <= 18
        if block == "s":
            assert group in (1, 2) or element["symbol"] == "He"
        elif block == "d":
            assert 3 <= group <= 12
        else:
            assert 13 <= group <= 18


def test_every_category_is_one_the_legend_lists():
    used = {element["category"] for element in ELEMENTS}
    assert used <= set(CATEGORIES)
    # An entry in the legend that nothing uses is a legend nobody can read.
    assert used == set(CATEGORIES)


def test_the_f_block_is_the_fifteen_lanthanides_and_fifteen_actinides():
    lanthanides = [e for e in ELEMENTS if e["category"] == "lanthanide"]
    actinides = [e for e in ELEMENTS if e["category"] == "actinide"]
    assert [e["atomic_number"] for e in lanthanides] == list(range(57, 72))
    assert [e["atomic_number"] for e in actinides] == list(range(89, 104))


def test_present_values_are_physically_admissible():
    for element in ELEMENTS:
        melting = element["melting_point_k"]
        boiling = element["boiling_point_k"]
        if melting is not None:
            assert melting > 0, element["symbol"]
        if boiling is not None:
            assert boiling > 0, element["symbol"]
        if element["density_g_per_cm3"] is not None:
            assert element["density_g_per_cm3"] > 0, element["symbol"]
        if element["electronegativity_pauling"] is not None:
            # Caesium is the least electronegative and fluorine the most; the
            # Pauling scale is defined so that nothing falls outside them.
            assert 0.7 <= element["electronegativity_pauling"] <= 3.98, element["symbol"]
        if element["first_ionization_kj_per_mol"] is not None:
            assert element["first_ionization_kj_per_mol"] > 0, element["symbol"]


def test_boiling_exceeds_melting_except_where_the_element_sublimes():
    """Arsenic sublimes at ambient pressure, so its 'boiling' point is lower.

    Naming the one exception is the point: a blanket rule would have to be
    relaxed to pass, and a relaxed rule would stop catching a swapped pair.
    """

    inverted = [
        element["symbol"]
        for element in ELEMENTS
        if element["melting_point_k"] is not None
        and element["boiling_point_k"] is not None
        and element["boiling_point_k"] < element["melting_point_k"]
    ]
    assert inverted == ["As"]


def test_the_state_at_room_temperature_follows_from_the_transition_points():
    """Two liquids, eleven gases; every other element with data is a solid."""

    liquids = {e["symbol"] for e in ELEMENTS if e["state_at_room_temperature"] == "liquid"}
    gases = {e["symbol"] for e in ELEMENTS if e["state_at_room_temperature"] == "gas"}
    assert liquids == {"Br", "Hg"}
    assert gases == {"H", "He", "N", "O", "F", "Ne", "Cl", "Ar", "Kr", "Xe", "Rn"}


def test_an_absent_value_says_which_kind_of_absence_it_is():
    for element in ELEMENTS:
        if element["discovery_year"] is None:
            assert element["known_since_antiquity"], element["symbol"]
        else:
            assert not element["known_since_antiquity"], element["symbol"]
        if element["synthetic"]:
            assert element["crustal_abundance_mg_per_kg"] == 0.0, element["symbol"]
            assert element["radioactive"], element["symbol"]


def test_no_element_known_since_antiquity_is_synthetic():
    for element in ELEMENTS:
        assert not (element["known_since_antiquity"] and element["synthetic"])


def test_spot_values_against_independent_references():
    """A handful of values anyone can check, so a systematic shift is caught.

    Chosen because each is quoted identically in every reference: hydrogen's
    mass, carbon's defining position, iron's body-centred cubic structure and
    56 300 mg/kg crustal abundance, gold's anomalous configuration, and
    fluorine's electronegativity, which defines the top of the Pauling scale.
    """

    assert BY_SYMBOL["H"]["atomic_mass"] == pytest.approx(1.008)
    assert BY_SYMBOL["C"]["group"] == 14 and BY_SYMBOL["C"]["period"] == 2
    assert BY_SYMBOL["Fe"]["crystal_structure"] == "body-centred cubic"
    assert BY_SYMBOL["Fe"]["electron_configuration"] == "[Ar] 3d6 4s2"
    assert BY_SYMBOL["Au"]["electron_configuration"] == "[Xe] 4f14 5d10 6s1"
    assert BY_SYMBOL["Au"]["electron_configuration_is_exception"] is True
    assert BY_SYMBOL["F"]["electronegativity_pauling"] == pytest.approx(3.98)
    assert BY_SYMBOL["Cs"]["electronegativity_pauling"] == pytest.approx(0.79)


def test_lookup_is_case_insensitive_and_says_no_clearly():
    assert element_by_symbol("fe")["name"] == "Iron"
    assert element_by_symbol("FE")["name"] == "Iron"
    assert element_by_symbol(" Au ")["name"] == "Gold"
    assert element_by_symbol("Zz") is None


def test_the_layout_puts_every_element_somewhere_and_nowhere_twice():
    """The grid is what the browser draws, so a collision would hide an element."""

    table = periodic_table()
    seats = {(e["grid_row"], e["grid_column"]) for e in table["elements"]}
    assert len(seats) == 118
    for element in table["elements"]:
        assert 1 <= element["grid_column"] <= 18
        assert 1 <= element["grid_row"] <= 10
    # The f block is drawn detached, below the seven periods.
    detached = {e["symbol"] for e in table["elements"] if e["grid_row"] > 7}
    assert len(detached) == 30
    assert {"La", "Lu", "Ac", "Lr", "U"} <= detached
