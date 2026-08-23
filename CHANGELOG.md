# Changelog

## 0.4.0 — 2026-08-23

- Added an Atom % ⇄ Mass % composition conversion tab, backed by a 118-element IUPAC standard
  atomic weight table (`elements.py`), `/api/composition/convert`, and `/api/elements`.

## 0.3.0 — 2026-08-23

- Added a scientific help page covering expression evaluation, sampling, equations, critical
  bounds, and an SVG workflow.
- Added versioned health metadata, security headers, and a Waitress production entry point.
- Repackaged the service so wheels contain the application, templates, JavaScript, and SVG assets.

## 0.2.0

- Added the safe expression evaluator and bounded one- and two-variable plotting APIs.
