from app import app, evaluate, plot_expression, VariableSpec


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
    with app.test_client() as client:
        response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json()["tool_id"] == "scientific-calculator"


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
