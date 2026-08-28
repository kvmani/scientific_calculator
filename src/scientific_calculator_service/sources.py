"""Where every number in the element tables came from, with links to check it.

Why this is a module and not a paragraph in the template
--------------------------------------------------------
A reference tool that cannot be checked is worth less than one that can, and
"the CRC Handbook" is not a citation a reader can act on - it is the name of a
book. So each group of properties names the compilation it came from, the
primary paper behind that compilation where there is one, and a URL that leads
to the actual numbers rather than to a homepage.

Keeping this next to the data rather than in the page means the API and the UI
quote the same provenance, and that adding a property without saying where it
came from is a visibly incomplete change rather than an invisible one.

Every URL here points at a public database or a published paper's DOI. None is
fetched at runtime: the service works with no outside connection, and these are
for the reader, not for the program.
"""

from __future__ import annotations

from typing import Any

__all__ = ["SOURCES", "sources"]

#: One entry per group of properties, in the order the detail view shows them.
#:
#: ``fields`` names the record keys the entry accounts for, so a reader looking
#: at one number can find which citation covers it, and so a property that no
#: entry claims is findable by a test rather than by noticing.
_SOURCES: tuple[dict[str, Any], ...] = (
    {
        "id": "atomic-weights",
        "title": "Standard atomic weights",
        "publisher": "IUPAC Commission on Isotopic Abundances and Atomic Weights (CIAAW)",
        "detail": (
            "The 2021 table of standard atomic weights. Values for elements with "
            "no stable isotope are the mass number of the longest-lived isotope, "
            "which is a convention rather than a measured weight."
        ),
        "url": "https://ciaaw.org/atomic-weights.htm",
        "fields": ("atomic_mass",),
    },
    {
        "id": "isotopes",
        "title": "Natural isotopic abundances and isotope masses",
        "publisher": "NIST Atomic Weights and Isotopic Compositions database",
        "detail": (
            "Abundances are the representative isotopic composition of normal "
            "terrestrial material; a sample from one source can differ from it, "
            "which is why the standard atomic weight of some elements is an "
            "interval rather than a number."
        ),
        "url": "https://physics.nist.gov/cgi-bin/Compositions/stand_alone.pl",
        "fields": ("natural_isotopes", "natural_isotope_count", "monoisotopic"),
    },
    {
        "id": "configurations",
        "title": "Ground-state electron configurations",
        "publisher": "NIST Atomic Spectra Database",
        "detail": (
            "Configurations are computed here from the Madelung ordering, with "
            "the twenty experimentally established exceptions to that ordering "
            "taken from NIST and listed explicitly in the source, so which "
            "elements break the rule is itself visible."
        ),
        "url": "https://www.nist.gov/pml/atomic-spectra-database",
        "fields": (
            "electron_configuration",
            "electron_configuration_is_exception",
            "shell_electrons",
        ),
    },
    {
        "id": "xray",
        "title": "X-ray emission lines and absorption edges",
        "publisher": "XrayDB, packaging the tables of Elam, Ravel and Sieber (2002)",
        "detail": (
            "W. T. Elam, B. D. Ravel and J. R. Sieber, 'A new atomic database "
            "for X-ray spectroscopic calculations', Radiation Physics and "
            "Chemistry 63 (2002) 121. Covers Z = 1 to 98. Fluorescence yields "
            "and jump ratios come from the same compilation."
        ),
        "url": "https://xraypy.github.io/XrayDB/",
        "doi": "https://doi.org/10.1016/S0969-806X(01)00227-4",
        "cross_check_url": "https://physics.nist.gov/PhysRefData/XrayTrans/Html/search.html",
        "cross_check_label": "Cross-check against the NIST X-ray Transition Energies database",
        "fields": (
            "xray_lines",
            "xray_edges",
            "k_alpha1_ev",
            "k_alpha2_ev",
            "k_beta1_ev",
            "l_alpha1_ev",
            "k_edge_ev",
            "l3_edge_ev",
        ),
    },
    {
        "id": "ionization",
        "title": "Ionization energies",
        "publisher": "NIST Atomic Spectra Database, ionization energies",
        "detail": (
            "Successive ionization energies in electronvolts. The first "
            "ionization energy is also carried in kJ/mol from the CRC Handbook. "
            "For 109 elements the two agree to well under a percent; for the 5d "
            "metals Tc, Ta, W, Os and Ir and the early actinides Ac, Th, Lr and "
            "Db the two compilations differ by up to four percent, which is a "
            "disagreement in the literature rather than in this tool."
        ),
        "url": "https://physics.nist.gov/PhysRefData/ASD/ionEnergy.html",
        "fields": ("ionization_energies_ev", "first_ionization_kj_per_mol"),
    },
    {
        "id": "electronegativity",
        "title": "Electronegativity scales",
        "publisher": "Pauling scale (CRC Handbook); Allen scale (Allen 1989)",
        "detail": (
            "L. C. Allen, 'Electronegativity is the average one-electron energy "
            "of the valence-shell electrons in ground-state free atoms', J. Am. "
            "Chem. Soc. 111 (1989) 9003. The Allen scale is in eV and is not on "
            "the same footing as the dimensionless Pauling scale."
        ),
        "url": "https://doi.org/10.1021/ja00207a003",
        "fields": ("electronegativity_pauling", "electronegativity_allen_ev"),
    },
    {
        "id": "radii",
        "title": "Atomic, covalent and van der Waals radii",
        "publisher": "Cordero et al. (2008); Alvarez (2013); CRC Handbook",
        "detail": (
            "Covalent radii are the self-consistent set of B. Cordero et al., "
            "Dalton Trans. (2008) 2832. Van der Waals radii are S. Alvarez, "
            "Dalton Trans. 42 (2013) 8617. A radius is a model-dependent "
            "quantity, so radii from different sets should not be mixed."
        ),
        "url": "https://doi.org/10.1039/b801115j",
        "doi": "https://doi.org/10.1039/c3dt50599e",
        "fields": (
            "atomic_radius_pm",
            "covalent_radius_pm",
            "van_der_waals_radius_pm",
            "metallic_radius_pm",
            "atomic_volume_cm3_per_mol",
        ),
    },
    {
        "id": "thermophysical",
        "title": "Thermal, physical and crystallographic properties",
        "publisher": "CRC Handbook of Chemistry and Physics, 97th ed. (2016)",
        "detail": (
            "Melting and boiling points, density, crystal structure, lattice "
            "constant, thermal conductivity, heat capacity and the heats of "
            "fusion, vaporization and atomization. Densities are for the solid "
            "at 20 degrees C except for the gases and the two liquids."
        ),
        "url": "https://hbcp.chemnetbase.com/",
        "fields": (
            "melting_point_k",
            "boiling_point_k",
            "density_g_per_cm3",
            "crystal_structure",
            "lattice_structure",
            "lattice_constant_angstrom",
            "thermal_conductivity_w_per_m_k",
            "molar_heat_capacity_j_per_mol_k",
            "specific_heat_j_per_g_k",
            "heat_of_fusion_kj_per_mol",
            "heat_of_vaporization_kj_per_mol",
            "heat_of_atomization_kj_per_mol",
            "electron_affinity_ev",
            "dipole_polarizability_au",
            "state_at_room_temperature",
            "common_oxidation_states",
        ),
    },
    {
        "id": "occurrence",
        "title": "Abundance, classification, price and supply risk",
        "publisher": "mendeleev, compiling CRC Handbook and Royal Society of Chemistry data",
        "detail": (
            "Crustal and seawater abundances, Goldschmidt and geochemical "
            "classes, CAS registry numbers, prices and relative supply risk. "
            "Prices are indicative only: they are a snapshot of a market, not a "
            "physical constant, and they move."
        ),
        "url": "https://mendeleev.readthedocs.io/en/stable/data.html",
        "cross_check_url": "https://www.rsc.org/periodic-table",
        "cross_check_label": "Royal Society of Chemistry periodic table",
        "fields": (
            "crustal_abundance_mg_per_kg",
            "abundance_seawater_mg_per_l",
            "goldschmidt_class",
            "geochemical_class",
            "cas_number",
            "price_usd_per_kg",
            "supply_risk_index",
            "mendeleev_number",
            "pettifor_number",
            "cpk_colour",
            "discoverers",
            "discovery_location",
            "discovery_year",
            "name_origin",
            "description",
            "uses",
            "sources",
        ),
    },
)

#: The two packages the generated tables are read out of, named so a reader can
#: reproduce the generation step rather than take the numbers on trust.
_TOOLING: tuple[dict[str, str], ...] = (
    {
        "name": "XrayDB",
        "detail": "M. Newville and contributors. MIT licence.",
        "url": "https://github.com/xraypy/XrayDB",
    },
    {
        "name": "mendeleev",
        "detail": "L. M. Mentel. MIT licence.",
        "url": "https://github.com/lmmentel/mendeleev",
    },
)


def sources() -> dict[str, Any]:
    """The provenance of every property, for the API and the page alike."""

    return {
        "sources": [dict(entry, fields=list(entry["fields"])) for entry in _SOURCES],
        "tooling": [dict(entry) for entry in _TOOLING],
        "note": (
            "No URL here is fetched by this service. The tables are vendored, "
            "the tool runs with no outside connection, and these links are for "
            "you to check the numbers against their source."
        ),
    }


#: The same payload as a constant, for callers that want it without a call.
SOURCES: dict[str, Any] = sources()
