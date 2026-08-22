"""Local scientific calculator with safe evaluation and plot-data APIs."""

from __future__ import annotations

import ast
import math
import operator
from dataclasses import dataclass
from typing import Callable, Mapping

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)
MAX_EXPRESSION_LENGTH = 1024
MAX_POINTS = 5000


class ExpressionError(ValueError):
    """Raised when an expression or plot request is invalid."""


@dataclass(frozen=True)
class VariableSpec:
    name: str
    start: float
    stop: float
    step: float


def _normalize(expression: str) -> str:
    if not isinstance(expression, str) or not expression.strip():
        raise ExpressionError("Expression is required")
    if len(expression) > MAX_EXPRESSION_LENGTH:
        raise ExpressionError("Expression is too long")
    return expression.strip().replace("^", "**")


def _trig(fn: Callable[[float], float], degrees: bool) -> Callable[[float], float]:
    return lambda value: fn(math.radians(value) if degrees else value)


def _inverse_trig(fn: Callable[[float], float], degrees: bool) -> Callable[[float], float]:
    return lambda value: math.degrees(fn(value)) if degrees else fn(value)


def _functions(angle_unit: str) -> dict[str, Callable[..., float]]:
    if angle_unit not in {"radian", "degree"}:
        raise ExpressionError("angle_unit must be 'radian' or 'degree'")
    degrees = angle_unit == "degree"
    return {
        "sin": _trig(math.sin, degrees), "cos": _trig(math.cos, degrees),
        "tan": _trig(math.tan, degrees), "asin": _inverse_trig(math.asin, degrees),
        "acos": _inverse_trig(math.acos, degrees), "atan": _inverse_trig(math.atan, degrees),
        "sinh": math.sinh, "cosh": math.cosh, "tanh": math.tanh,
        "sqrt": math.sqrt, "log": lambda x, base=math.e: math.log(x, base),
        "ln": math.log, "log10": math.log10, "exp": math.exp, "abs": abs,
        "floor": math.floor, "ceil": math.ceil,
        "min": min, "max": max,
    }


def _validate(node: ast.AST) -> None:
    if isinstance(node, ast.Expression):
        _validate(node.body); return
    if isinstance(node, ast.BinOp) and isinstance(node.op, (ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow)):
        _validate(node.left); _validate(node.right); return
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        _validate(node.operand); return
    if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and not node.keywords:
        for arg in node.args: _validate(arg)
        return
    if isinstance(node, ast.Name): return
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool): return
    raise ExpressionError("Only numeric operations, named variables, and approved math functions are allowed")


def _canonical(node: ast.AST) -> str:
    if isinstance(node, ast.Constant): return f"{node.value:g}"
    if isinstance(node, ast.Name): return node.id
    if isinstance(node, ast.UnaryOp): return f"({'+' if isinstance(node.op, ast.UAdd) else '-'}{_canonical(node.operand)})"
    if isinstance(node, ast.BinOp):
        symbols = {ast.Add: "+", ast.Sub: "-", ast.Mult: "*", ast.Div: "/", ast.Mod: "%", ast.Pow: "^"}
        return f"({_canonical(node.left)} {symbols[type(node.op)]} {_canonical(node.right)})"
    if isinstance(node, ast.Call): return f"{node.func.id}({', '.join(_canonical(arg) for arg in node.args)})"
    raise ExpressionError("Unsupported expression")


def _evaluate(node: ast.AST, context: Mapping[str, float], functions: Mapping[str, Callable[..., float]]) -> float:
    if isinstance(node, ast.Constant): value = float(node.value)
    elif isinstance(node, ast.Name):
        if node.id not in context: raise ExpressionError(f"Unknown variable '{node.id}'")
        value = context[node.id]
    elif isinstance(node, ast.UnaryOp): value = _evaluate(node.operand, context, functions) * (-1 if isinstance(node.op, ast.USub) else 1)
    elif isinstance(node, ast.BinOp):
        left = _evaluate(node.left, context, functions)
        right = _evaluate(node.right, context, functions)
        operation = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv, ast.Mod: operator.mod, ast.Pow: operator.pow}[type(node.op)]
        value = operation(left, right)
    elif isinstance(node, ast.Call):
        if node.func.id not in functions: raise ExpressionError(f"Function '{node.func.id}' is not allowed")
        value = functions[node.func.id](*[_evaluate(arg, context, functions) for arg in node.args])
    else: raise ExpressionError("Unsupported expression")
    if isinstance(value, complex) or not math.isfinite(float(value)): raise ExpressionError("Result is not finite")
    return float(value)


def _parse_expression(expression: str) -> tuple[ast.AST, str]:
    try: tree = ast.parse(_normalize(expression), mode="eval")
    except SyntaxError as error: raise ExpressionError(f"Could not parse expression: {error.msg}") from error
    _validate(tree)
    return tree.body, _canonical(tree.body)


def _context(variables: Mapping[str, object] | None) -> dict[str, float]:
    context = {"pi": math.pi, "e": math.e, "tau": math.tau}
    for name, value in (variables or {}).items():
        if not isinstance(name, str) or not name.isidentifier() or name.startswith("__"):
            raise ExpressionError(f"Invalid variable name '{name}'")
        try: context[name] = float(value)
        except (TypeError, ValueError) as error: raise ExpressionError(f"Variable '{name}' must be numeric") from error
    return context


def evaluate_expression(expression: str, variables: Mapping[str, object] | None = None, angle_unit: str = "radian") -> dict[str, object]:
    body, canonical = _parse_expression(expression)
    functions = _functions(angle_unit)
    context = _context(variables)
    value = _evaluate(body, context, functions)
    names = sorted({node.id for node in ast.walk(body) if isinstance(node, ast.Name) and node.id not in functions and node.id not in {"pi", "e", "tau"}})
    return {"value": value, "result": value, "canonical": canonical, "angle_unit": angle_unit, "used_variables": names}


def evaluate(expression: str, variables: Mapping[str, object] | None = None, angle_unit: str = "radian") -> float:
    """Backward-compatible scalar API used by earlier local clients."""
    return float(evaluate_expression(expression, variables, angle_unit)["value"])


def _range(spec: VariableSpec) -> list[float]:
    if spec.step <= 0 or spec.stop < spec.start: raise ExpressionError("Ranges require stop >= start and step > 0")
    count = int(math.floor((spec.stop - spec.start) / spec.step + 1e-9)) + 1
    if count > MAX_POINTS: raise ExpressionError("Range produces too many points")
    return [spec.start + index * spec.step for index in range(count)]


def plot_expression(expression: str, variables: list[VariableSpec], constants: Mapping[str, object] | None = None, angle_unit: str = "radian") -> dict[str, object]:
    if len(variables) not in {1, 2}: raise ExpressionError("Only one or two variables are supported")
    body, canonical = _parse_expression(expression)
    functions = _functions(angle_unit)
    context = _context(constants)
    ranges = [_range(spec) for spec in variables]
    points = math.prod(len(values) for values in ranges)
    if points > MAX_POINTS: raise ExpressionError("Requested grid exceeds 5000 points")
    if len(variables) == 1:
        series = []
        for value in ranges[0]:
            local = dict(context); local[variables[0].name] = value
            series.append({"x": value, "y": _evaluate(body, local, functions)})
        return {"mode": "1d", "expression": canonical, "points": len(series), "variables": [variables[0].__dict__], "series": series}
    surface = []
    for y in ranges[1]:
        row = []
        for x in ranges[0]:
            local = dict(context); local[variables[0].name] = x; local[variables[1].name] = y
            row.append(_evaluate(body, local, functions))
        surface.append(row)
    return {"mode": "2d", "expression": canonical, "points": points, "variables": [spec.__dict__ for spec in variables], "grid": {"x": ranges[0], "y": ranges[1], "z": surface}}


def _payload(): return request.get_json(silent=True) or {}


@app.get("/")
def home(): return render_template("index.html")


@app.get("/api/health")
def health(): return jsonify({"status": "ok", "tool_id": "scientific-calculator", "version": "0.2.0"})


@app.post("/api/evaluate")
@app.post("/api/scientific_calculator/evaluate")
def api_evaluate():
    payload = _payload()
    try: return jsonify({"ok": True, **evaluate_expression(payload.get("expression", ""), payload.get("variables"), payload.get("angle_unit", "radian"))})
    except (ExpressionError, TypeError, ValueError, ZeroDivisionError, OverflowError) as error: return jsonify({"ok": False, "error": str(error)}), 400


@app.post("/api/plot")
@app.post("/api/scientific_calculator/plot")
def api_plot():
    payload = _payload()
    try:
        variables = [VariableSpec(str(item["name"]), float(item["start"]), float(item["stop"]), float(item["step"])) for item in payload.get("variables", [])]
        return jsonify({"ok": True, **plot_expression(payload.get("expression", ""), variables, payload.get("constants"), payload.get("angle_unit", "radian"))})
    except (KeyError, ExpressionError, TypeError, ValueError, ZeroDivisionError, OverflowError) as error: return jsonify({"ok": False, "error": str(error)}), 400


if __name__ == "__main__": app.run(host="127.0.0.1", port=5055, debug=False)
