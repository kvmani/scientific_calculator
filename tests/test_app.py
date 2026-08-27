import ast

from app import app, convert_composition, evaluate, plot_expression, VariableSpec, ExpressionError, _canonical, _evaluate


def test_evaluate_scientific_expression():
    assert evaluate("sqrt(3**2 + 4**2)") == 5


def test_rejects_arbitrary_code():
    try:
        evaluate("__import__('os').getcwd()")
    except ValueError:
        pass
    else:
        raise AssertionError("unsafe expression was accepted")


def test_health_contract():
    """The served version must be the packaged one, not a third copy of a string.

    Transcribing the version here made the test assert only that nobody had
    edited this line, which is how the packaged version and the served version
    came to disagree without anything failing. Reading both is what catches it.
    """

    import re
    from pathlib import Path

    from app import VERSION

    with app.test_client() as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["tool_id"] == "scientific-calculator"
    assert response.get_json()["version"] == VERSION

    pyproject = Path(__file__).resolve().parents[1] / "pyproject.toml"
    packaged = re.search(r'^version = "([^"]+)"', pyproject.read_text(encoding="utf-8"), re.M)
    assert packaged and packaged.group(1) == VERSION


def test_scientific_help_and_security_headers():
    with app.test_client() as client:
        response = client.get("/help")
    assert response.status_code == 200
    assert b"SCIENTIFIC GUIDE" in response.data
    assert b"calculator-workflow.svg" in response.data
    assert response.headers["X-Content-Type-Options"] == "nosniff"


def test_evaluate_contract():
    with app.test_client() as client:
        response = client.post("/api/evaluate", json={"expression": "pi"})
    assert response.status_code == 200
    assert response.get_json()["ok"] is True


def test_named_variables_and_power_notation():
    assert evaluate("a^2 + 5*b + 23", {"a": 23, "b": -18}) == 462


def test_plot_contracts_for_one_and_two_variables():
    one_d = plot_expression("x^2", [VariableSpec("x", -1, 1, 1)])
    assert one_d["mode"] == "1d"
    assert one_d["points"] == 3
    two_d = plot_expression("x^2 + y", [VariableSpec("x", 0, 1, 1), VariableSpec("y", 0, 1, 1)])
    assert two_d["mode"] == "2d"
    assert len(two_d["grid"]["z"]) == 2


def test_expression_validation_and_degree_mode():
    assert evaluate("sin(90)", angle_unit="degree") == 1
    for expression in ("", "1" * 1025, "1 +", "__import__('os')", "unknown"):
        try:
            evaluate(expression)
        except ValueError:
            pass
        else:
            raise AssertionError(expression)
    for variables in ({"bad-name": 1}, {"x": "nope"}):
        try:
            evaluate("x", variables)
        except ValueError:
            pass
        else:
            raise AssertionError(variables)
    for bad_unit in ("gradians",):
        try:
            evaluate("1", angle_unit=bad_unit)
        except ExpressionError:
            pass
        else:
            raise AssertionError(bad_unit)


def test_plot_rejects_invalid_ranges_and_payloads():
    for specs in ([VariableSpec("x", 1, 0, 1)], [VariableSpec("x", 0, 1, 0)], [], [VariableSpec("x", 0, 10000, 1)]):
        try:
            plot_expression("x", specs)
        except ValueError:
            pass
        else:
            raise AssertionError(specs)
    with app.test_client() as client:
        assert client.post("/api/evaluate", json={"expression": "1/0"}).status_code == 400
        assert client.post("/api/plot", json={"expression": "x^2", "variables": [{"name": "x", "start": 0, "stop": 1, "step": 1}]}).get_json()["ok"] is True
        assert client.post("/api/scientific_calculator/plot", json={"expression": "x", "variables": [{"name": "x"}]}).status_code == 400
    assert evaluate("-1") == -1
    for callback in (lambda: _canonical(ast.Load()), lambda: _evaluate(ast.Load(), {}, {})):
        try:
            callback()
        except ValueError:
            pass
        else:
            raise AssertionError("unsupported AST was accepted")


def test_atom_to_mass_fraction_matches_known_stainless_steel():
    result = convert_composition("atom_to_mass", {"Fe": 70, "Cr": 19, "Ni": 11})
    assert result["mode"] == "atom_to_mass"
    assert abs(sum(result["mass_fraction"].values()) - 1.0) < 1e-9
    # Cr (lightest, 52.0) should lose mass share; Ni (heaviest, 58.69) should gain it.
    assert result["mass_fraction"]["Cr"] < result["atom_fraction"]["Cr"]
    assert result["mass_fraction"]["Ni"] > result["atom_fraction"]["Ni"]
    assert result["elements"] == ["Fe", "Cr", "Ni"]


def test_mass_to_atom_fraction_round_trips_atom_to_mass():
    forward = convert_composition("atom_to_mass", {"Fe": 70, "Cr": 19, "Ni": 11})
    back = convert_composition("mass_to_atom", forward["percent"]["mass_fraction"])
    for element in ("Fe", "Cr", "Ni"):
        assert abs(back["atom_fraction"][element] - forward["atom_fraction"][element]) < 1e-6


def test_composition_conversion_rejects_bad_input():
    for mode, composition in (
        ("atom_to_mass", {}),
        ("atom_to_mass", {"Zz": 1}),
        ("atom_to_mass", {"Fe": -1}),
        ("atom_to_mass", {"Fe": "nope"}),
        ("bad_mode", {"Fe": 1}),
    ):
        try:
            convert_composition(mode, composition)
        except ValueError:
            pass
        else:
            raise AssertionError((mode, composition))


def test_composition_api_contract():
    with app.test_client() as client:
        response = client.post(
            "/api/composition/convert",
            json={"mode": "atom_to_mass", "composition": {"Fe": 70, "Cr": 19, "Ni": 11}},
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ok"] is True
        assert set(data["elements"]) == {"Fe", "Cr", "Ni"}
        assert client.get("/api/elements").get_json()["elements"]["Fe"] == 55.845
        assert client.post("/api/composition/convert", json={"composition": {}}).status_code == 400
