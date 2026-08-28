"""X-ray lines, edges and the extra properties: checked against physics.

The X-ray tables are generated from a published compilation, so a test that
pinned their values would only assert that the generator ran. What is worth
asserting is that the numbers obey the rules that make them X-ray data at all,
and that the generated file is the one the rest of the package thinks it is:

* an emission line cannot be more energetic than the edge whose vacancy it
  fills, since the photon comes from an electron falling into that vacancy;
* Ka1 must exceed Ka2, because L3 lies above L2;
* every line and edge energy must rise with atomic number - this is Moseley's
  law, and it is the single strongest check available on a table of X-ray
  energies, because a transposed digit anywhere breaks it;
* the wavelength must be the energy converted, to the precision quoted;
* the tables must stop exactly at californium, and the elements past it must
  report *no data* rather than an empty table that reads like a measurement of
  zero.

Three values are pinned, and only three: Cu Ka1, Mo Ka1 and Fe Ka1 are the
anchors every X-ray laboratory knows by heart, and a package that got those
wrong would be wrong in a way no structural test can catch.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from scientific_calculator_service.app import app
from scientific_calculator_service.periodic_table import (
    EXTRA_FIELDS,
    MAX_XRAY_Z,
    PLANCK_C_EV_ANGSTROM,
    all_elements,
    element_by_symbol,
    lines_near,
    xray_edges,
    xray_lines,
)
from scientific_calculator_service.sources import sources
from scientific_calculator_service.xray_data import XRAY_EDGES, XRAY_LINES


@pytest.fixture(scope="module")
def elements():
    return all_elements()


# --------------------------------------------------------------- anchors ---
#: The three lines a diffractionist or a spectroscopist would notice were wrong
#: immediately, with the value each is known by and the tolerance the Elam
#: compilation is quoted to.
ANCHORS = (
    ("Cu", "Ka1", 8047.8, 3.0),
    ("Mo", "Ka1", 17479.0, 6.0),
    ("Fe", "Ka1", 6403.8, 3.0),
)


@pytest.mark.parametrize("symbol, line, energy_ev, tolerance", ANCHORS)
def test_known_lines_have_their_known_energies(symbol, line, energy_ev, tolerance):
    element = element_by_symbol(symbol)
    assert element["xray_lines"][line]["energy_ev"] == pytest.approx(
        energy_ev, abs=tolerance
    )


def test_copper_k_alpha_wavelength_is_the_one_diffraction_uses():
    """1.5406 A is the number on every powder-diffraction pattern ever indexed."""

    line = element_by_symbol("Cu")["xray_lines"]["Ka1"]
    assert line["wavelength_angstrom"] == pytest.approx(1.5406, abs=0.001)


# ------------------------------------------------------------- structure ---
def test_tables_stop_at_californium():
    assert max(XRAY_LINES) == MAX_XRAY_Z == 98
    assert max(XRAY_EDGES) == MAX_XRAY_Z


def test_elements_past_californium_report_no_data_rather_than_empty_measurements():
    """The distinction the whole module is built on, applied to X-rays."""

    for symbol in ("Es", "Fm", "Og"):
        element = element_by_symbol(symbol)
        assert element["has_xray_data"] is False
        assert element["xray_lines"] == {}
        assert element["xray_edges"] == {}
        # Not zero, and not absent-by-accident: every summary field is None.
        assert element["k_alpha1_ev"] is None
        assert element["k_edge_ev"] is None


def test_every_element_up_to_californium_has_a_k_edge():
    for number in range(1, MAX_XRAY_Z + 1):
        assert "K" in xray_edges(number), number


#: What the Elam tables are quoted to, in eV.
#:
#: For the light elements the L2-L3 spin-orbit splitting is smaller than this,
#: so two levels that differ physically can round to the same figure or even to
#: the wrong side of each other - sodium's L2 and L3 edges are printed as 30.4
#: and 30.5 eV. That is a property of the published table, not an error in it,
#: and the ordering tests allow exactly one quoted digit of slack rather than
#: pretending the data is finer than it is.
QUOTED_PRECISION_EV = 0.1


def test_k_alpha_1_is_above_k_alpha_2():
    """L3 lies above L2, so the photon from L3 carries more energy."""

    for number in range(1, MAX_XRAY_Z + 1):
        lines = xray_lines(number)
        if "Ka1" in lines and "Ka2" in lines:
            # Sodium's two Ka lines are printed as 1040.3 and 1040.4: their
            # true separation is below the figure the table is quoted to.
            gap = lines["Ka1"]["energy_ev"] - lines["Ka2"]["energy_ev"]
            assert gap > -QUOTED_PRECISION_EV - 1e-6, number


def test_no_emission_line_exceeds_the_edge_it_fills():
    """A line is an electron falling into a vacancy; it cannot beat the drop.

    The tolerance is one part in a thousand: the edge and the line come from
    different measurements in the same compilation, and the K edge is the
    ionization threshold rather than the exact binding energy of the level.
    """

    for number in range(1, MAX_XRAY_Z + 1):
        edges = xray_edges(number)
        for name, line in xray_lines(number).items():
            edge = edges.get(line["transition"].split()[0])
            if edge is None or not edge["energy_ev"]:
                continue
            assert line["energy_ev"] <= edge["energy_ev"] * 1.001, (number, name)


def test_moseley_energies_rise_with_atomic_number():
    """The check a transposed digit cannot survive.

    Moseley's law is why the periodic table is ordered by atomic number at all:
    the square root of a characteristic line's frequency is linear in Z. The
    weaker statement tested here - that it rises at all - is enough to catch any
    single wrong digit in a table of four-figure energies.
    """

    for name in ("Ka1", "Kb1", "La1"):
        previous = 0.0
        for number in range(1, MAX_XRAY_Z + 1):
            line = xray_lines(number).get(name)
            if line is None:
                continue
            assert line["energy_ev"] > previous, (name, number)
            previous = line["energy_ev"]


def test_absorption_edges_rise_with_atomic_number():
    for level in ("K", "L1", "L3", "M5"):
        previous = 0.0
        for number in range(1, MAX_XRAY_Z + 1):
            edge = xray_edges(number).get(level)
            if edge is None or not edge["energy_ev"]:
                continue
            assert edge["energy_ev"] >= previous, (level, number)
            previous = edge["energy_ev"]


def test_the_k_edge_is_the_highest_of_them_all():
    """No vacancy costs more to make than one in the innermost shell."""

    for number in range(1, MAX_XRAY_Z + 1):
        edges = xray_edges(number)
        highest = max(edge["energy_ev"] for edge in edges.values())
        assert edges["K"]["energy_ev"] == highest, number


def test_k_l_and_m_edges_are_ordered_by_shell():
    """An inner vacancy costs more than an outer one - through the M shell.

    The slack is one eV rather than the quoted 0.1, because the M levels of the
    first transition series sit at a few tens of eV where the compilation's
    figures are least certain: Elam prints cobalt's M2 and M3 as 58.9 and
    59.9 eV, inverted by a shade more than their own precision.
    """

    for number in range(1, MAX_XRAY_Z + 1):
        ordered = [
            edge["energy_ev"]
            for level, edge in xray_edges(number).items()
            if level[0] in "KLM"
        ]
        for higher, lower in zip(ordered, ordered[1:]):
            assert higher >= lower - 1.0, number


def test_the_f_levels_of_the_lanthanides_lie_below_the_shell_outside_them():
    """The one place where "deeper shell, higher energy" is simply false.

    In the lanthanides the 4f electrons (N6, N7) are barely bound - a few eV -
    while the 6s level (O1) below them in shell number sits at thirty to a
    hundred and fifty. This is not a defect in the table; it is why the
    lanthanides behave as they do, and it is asserted here so that nobody
    "fixes" the ordering test by extending it through the outer shells.
    """

    for number in range(58, 84):
        edges = xray_edges(number)
        if "N7" not in edges or "O1" not in edges:
            continue
        assert edges["N7"]["energy_ev"] < edges["O1"]["energy_ev"], number


def test_wavelength_is_the_energy_converted():
    for number in (6, 26, 29, 42, 74, 92):
        for line in xray_lines(number).values():
            # Wavelengths are stored to five decimal places, which is finer
            # than any measurement here and coarser than a relative tolerance
            # would be at 0.2 A, so the check is against the rounding step.
            assert line["wavelength_angstrom"] == pytest.approx(
                PLANCK_C_EV_ANGSTROM / line["energy_ev"], abs=1e-5
            )
        assert line["energy_kev"] == pytest.approx(line["energy_ev"] / 1000.0)


def test_fluorescence_yields_are_probabilities():
    for number in range(1, MAX_XRAY_Z + 1):
        for level, edge in xray_edges(number).items():
            assert 0.0 <= edge["fluorescence_yield"] <= 1.0, (number, level)
            assert edge["jump_ratio"] >= 1.0, (number, level)


def test_relative_intensities_are_fractions_of_their_series():
    for number in range(1, MAX_XRAY_Z + 1):
        for name, line in xray_lines(number).items():
            assert 0.0 <= line["relative_intensity"] <= 1.0, (number, name)


def test_siegbahn_labels_are_printed_with_greek_letters():
    lines = xray_lines(26)
    assert lines["Ka1"]["label"] == "Kα1"
    assert lines["Lb1"]["label"] == "Lβ1"
    assert lines["Ln"]["label"] == "Lη"


# -------------------------------------------------------------- identify ---
def test_lines_near_finds_the_line_it_is_given():
    matches = lines_near(8047.8, tolerance_ev=20.0)
    assert matches[0]["symbol"] == "Cu"
    assert matches[0]["line"] == "Ka1"


def test_lines_near_is_ordered_by_distance():
    matches = lines_near(6400.0, tolerance_ev=200.0)
    distances = [abs(match["difference_ev"]) for match in matches]
    assert distances == sorted(distances)


def test_lines_near_excludes_lines_too_weak_to_appear_in_a_spectrum():
    """The default cut is what makes the answer a shortlist rather than a dump."""

    wide = lines_near(6400.0, tolerance_ev=200.0, min_intensity=0.0)
    usual = lines_near(6400.0, tolerance_ev=200.0)
    assert len(usual) < len(wide)
    assert all(match["relative_intensity"] >= 0.01 for match in usual)


def test_lines_near_rejects_a_negative_tolerance():
    with pytest.raises(ValueError):
        lines_near(8000.0, tolerance_ev=-1.0)


# ---------------------------------------------------------------- extras ---
def test_every_element_carries_every_extra_field():
    """Present as a key even when unknown, so a client can render an absence.

    The generated table omits what it has no value for, which means hydrogen and
    iron do not have the same keys there. If that reached the record, a client
    would silently never draw a row for a property the first element it looked
    at happened to lack.
    """

    for element in all_elements():
        for field in EXTRA_FIELDS:
            assert field in element, (element["symbol"], field)


def test_natural_isotope_abundances_sum_to_a_hundred_percent():
    for element in all_elements():
        isotopes = element["natural_isotopes"]
        if not isotopes:
            continue
        total = sum(isotope["abundance_percent"] for isotope in isotopes)
        assert total == pytest.approx(100.0, abs=0.5), element["symbol"]


def test_isotope_masses_bracket_the_standard_atomic_weight():
    """A weighted mean must lie between the lightest and heaviest contributor."""

    for element in all_elements():
        isotopes = element["natural_isotopes"]
        if len(isotopes) < 2:
            continue
        masses = [isotope["atomic_mass"] for isotope in isotopes]
        assert min(masses) - 0.5 <= element["atomic_mass"] <= max(masses) + 0.5


def test_synthetic_elements_have_no_natural_isotopes():
    for element in all_elements():
        if element["synthetic"]:
            assert element["natural_isotopes"] == [], element["symbol"]


def test_monoisotopic_agrees_with_the_isotope_list():
    for element in all_elements():
        assert element["monoisotopic"] == (len(element["natural_isotopes"]) == 1)


def test_ionization_energies_rise_with_each_electron_removed():
    """Pulling an electron off a more positive ion always costs more."""

    for element in all_elements():
        energies = element["ionization_energies_ev"]
        if not energies:
            continue
        assert None not in energies, element["symbol"]
        assert energies == sorted(energies), element["symbol"]


#: Elements whose two ionization-energy sources genuinely disagree.
#:
#: The eV list comes from the NIST spectroscopic determinations and the kJ/mol
#: scalar from the CRC Handbook. For 109 elements they agree to well under one
#: percent. For these nine - the 5d metals and the early actinides, where the
#: measurement is hard and the compilations have not converged - they differ by
#: up to four percent. Naming them keeps the disagreement visible and still
#: catches a regression anywhere else; widening the tolerance to fit them would
#: have hidden a real fact about the literature behind a loose number.
IONIZATION_SOURCES_DISAGREE = frozenset(
    {"Tc", "Ta", "W", "Os", "Ir", "Ac", "Th", "Lr", "Db"}
)


def test_first_ionization_energy_agrees_between_its_two_units():
    for element in all_elements():
        energies = element["ionization_energies_ev"]
        scalar = element["first_ionization_kj_per_mol"]
        if not energies or scalar is None:
            continue
        tolerance = 0.05 if element["symbol"] in IONIZATION_SOURCES_DISAGREE else 0.01
        assert energies[0] * 96.485 == pytest.approx(
            scalar, rel=tolerance
        ), element["symbol"]


def test_the_disagreeing_elements_really_do_disagree():
    """Otherwise the exception list would quietly outlive the reason for it."""

    for element in all_elements():
        if element["symbol"] not in IONIZATION_SOURCES_DISAGREE:
            continue
        ratio = element["ionization_energies_ev"][0] * 96.485 / element[
            "first_ionization_kj_per_mol"
        ]
        assert abs(ratio - 1) > 0.01, element["symbol"]


def test_radii_are_ordered_the_way_bonding_requires():
    """A covalent radius is a bonded distance; a van der Waals radius is not."""

    for element in all_elements():
        covalent = element["covalent_radius_pm"]
        van_der_waals = element["van_der_waals_radius_pm"]
        if covalent is None or van_der_waals is None:
            continue
        assert covalent < van_der_waals, element["symbol"]


def test_cpk_colours_are_hex_triples():
    for element in all_elements():
        colour = element["cpk_colour"]
        if colour is None:
            continue
        assert colour.startswith("#") and len(colour) == 7, element["symbol"]
        int(colour[1:], 16)


# --------------------------------------------------------------- sources ---
def test_every_reported_field_is_claimed_by_a_source():
    """A property with no citation is a number the reader cannot check.

    This is the test that makes the provenance list maintainable: adding a
    property without saying where it came from fails here rather than shipping
    an uncitable number.
    """

    claimed = {field for entry in sources()["sources"] for field in entry["fields"]}
    # Fields derived here rather than taken from a source, and the layout keys.
    derived = {
        "atomic_number",
        "symbol",
        "name",
        "group",
        "period",
        "block",
        "category",
        "valence_electrons",
        "radioactive",
        "known_since_antiquity",
        "synthetic",
        "has_xray_data",
        "grid_row",
        "grid_column",
    }
    reported = set(all_elements()[25])
    unclaimed = reported - claimed - derived
    assert not unclaimed, sorted(unclaimed)


def test_every_source_has_a_url_a_reader_can_open():
    for entry in sources()["sources"]:
        assert entry["url"].startswith("https://"), entry["id"]
        assert entry["publisher"] and entry["detail"]
    for entry in sources()["tooling"]:
        assert entry["url"].startswith("https://")


# ------------------------------------------------------------------- API ---
def test_the_grid_payload_leaves_the_heavy_tables_out():
    """Otherwise the first page load ships 800 kB to draw a table needing none."""

    with app.test_client() as client:
        payload = client.get("/api/periodic_table").get_json()
    element = next(item for item in payload["elements"] if item["symbol"] == "Fe")
    assert "xray_lines" not in element
    assert "description" not in element
    # But everything the grid shades, filters or searches by is still there.
    assert element["k_alpha1_ev"] and element["thermal_conductivity_w_per_m_k"]
    assert element["natural_isotope_count"] == 4


def test_the_element_endpoint_carries_what_the_grid_left_out():
    with app.test_client() as client:
        element = client.get("/api/periodic_table/Fe").get_json()["element"]
    assert element["xray_lines"]["Ka1"]["energy_ev"] > 6000
    assert element["description"]


def test_xray_endpoint_returns_lines_and_edges():
    with app.test_client() as client:
        payload = client.get("/api/xray/Cu").get_json()
    assert payload["ok"] and payload["atomic_number"] == 29
    assert payload["lines"]["Ka1"]["wavelength_angstrom"] == pytest.approx(1.5406, abs=0.001)


def test_identify_accepts_either_unit_and_says_which_it_used():
    with app.test_client() as client:
        in_kev = client.get("/api/xray/identify?energy_kev=8.0478").get_json()
        in_ev = client.get("/api/xray/identify?energy_ev=8047.8").get_json()
    assert in_kev["unit_supplied"] == "keV"
    assert in_ev["unit_supplied"] == "eV"
    assert in_kev["matches"][0]["symbol"] == in_ev["matches"][0]["symbol"] == "Cu"


@pytest.mark.parametrize(
    "query",
    (
        "",
        "energy_kev=0",
        "energy_kev=-3",
        "energy_kev=abc",
        "energy_kev=8&tolerance_ev=-1",
        "energy_kev=8&min_intensity=2",
    ),
)
def test_identify_rejects_a_request_it_cannot_answer(query):
    with app.test_client() as client:
        response = client.get("/api/xray/identify?" + query)
    assert response.status_code == 400
    assert response.get_json()["ok"] is False


def test_identify_is_capped_but_says_so():
    """A one-eV question over a wide window can match hundreds of lines."""

    with app.test_client() as client:
        payload = client.get(
            "/api/xray/identify?energy_kev=8&tolerance_ev=5000&min_intensity=0"
        ).get_json()
    assert payload["truncated"] is True
    assert len(payload["matches"]) < payload["match_count"]


def test_unknown_symbols_are_a_404_on_every_element_endpoint():
    with app.test_client() as client:
        for path in ("/api/periodic_table/Xx", "/api/xray/Xx"):
            assert client.get(path).status_code == 404


def test_sources_endpoint_is_served():
    with app.test_client() as client:
        payload = client.get("/api/sources").get_json()
    assert payload["ok"] and payload["sources"] and payload["tooling"]
