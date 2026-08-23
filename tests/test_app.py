import ast

from app import app, evaluate, plot_expression, VariableSpec, ExpressionError, _canonical, _evaluate


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
    assert response.get_json()["version"] == "0.3.0"


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
