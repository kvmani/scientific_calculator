# Scientific Calculator

Standalone local service for safe, reproducible engineering and scientific expressions. It is intentionally separate from the portal and from PyTex's crystallographic calculator.

The browser UI supports named variables, `^` power notation, approved math functions, degree/radian modes, one-variable plots, and two-variable surface heatmaps. The API also keeps the legacy-compatible `/api/scientific_calculator/evaluate` and `/api/scientific_calculator/plot` routes.

## Run

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5055`.

## Deployment modes

The calculator is a complete standalone web app and can be developed, tested, and deployed on its
own. The Office Scientific Tools portal may link to its service URL, but `ml_server` and the other
tools are not required dependencies.
