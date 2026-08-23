"""Guards for offline equation rendering on the help page."""

from pathlib import Path

from app import app


ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "src" / "scientific_calculator_service" / "static"
VENDOR = STATIC / "vendor" / "mathjax"


def test_mathjax_bundle_is_vendored_for_offline_use() -> None:
    """The office intranet has no CDN access, so the bundle must ship with the service."""
    bundle = VENDOR / "tex-chtml-full.js"
    assert bundle.is_file()
    assert bundle.stat().st_size > 500_000
    assert (VENDOR / "LICENSE").is_file()

    fonts = sorted((VENDOR / "output" / "chtml" / "fonts" / "woff-v2").glob("*.woff"))
    assert len(fonts) >= 15


def test_vendored_assets_are_tracked_by_git() -> None:
    """Files present only on a developer's disk would not reach a deployment."""
    import subprocess

    tracked = subprocess.run(
        ["git", "ls-files", "src/scientific_calculator_service/static/vendor/mathjax"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split()

    assert any(name.endswith("tex-chtml-full.js") for name in tracked)
    assert sum(1 for name in tracked if name.endswith(".woff")) >= 15


def test_wheel_would_ship_the_vendored_bundle() -> None:
    """A "static/*.js" glob does not reach static/vendor/**."""
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert 'scientific_calculator_service = ["templates/*.html", "static/**/*"]' in pyproject


def test_help_page_typesets_through_the_local_bundle() -> None:
    with app.test_client() as client:
        response = client.get("/help")
    assert response.status_code == 200
    body = response.data.decode("utf-8")

    assert "/static/vendor/mathjax/tex-chtml-full.js" in body
    assert "/static/mathjax-config.js" in body
    assert "cdn.jsdelivr.net" not in body
    assert r"\[" in body
    assert 'class="eq mathjax"' in body


def test_help_page_serves_the_bundle_and_its_fonts() -> None:
    with app.test_client() as client:
        assert client.get("/static/vendor/mathjax/tex-chtml-full.js").status_code == 200
        font = client.get(
            "/static/vendor/mathjax/output/chtml/fonts/woff-v2/MathJax_Math-Italic.woff"
        )
    assert font.status_code == 200
