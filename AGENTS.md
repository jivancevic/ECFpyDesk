# ECFpyDesk

A desktop GUI for symbolic regression: a Python app (customtkinter, MVC) that drives SRM, a C++ program built on ECF. The spec for finishing it is issue #1. Vocabulary is in `GLOSSARY.md`, decisions in `docs/adr/`.

## Layout

- `main.py`, `models/`, `views/`, `controllers/`, `utils/`: the Python app
- `native/ecf/`: vendored ECF 1.6.1, `native/SRM/`: SRM source (ADR 0001)
- `packaging/`: the PyInstaller spec, and the scripts that build a package and smoke-test it. A `v*` tag runs them in `.github/workflows/release.yml`.
- `srm/`: parameter file templates and sample data, and the SRM binary once built (gitignored, see `native/README.md`)

## How work ships

This repo follows `~/.agents/STANDARDS.md` (the loop, the gates, the never-list, `/ship`). Below are only this repo's facts.

- **Merge mode: direct.** The repo is private on GitHub Free, which has no branch protection. This ends when the repo goes public (ADR 0001); branch protection replaces it then.
- **A merge to `main` deploys nothing.** Users get the app only through a tagged release.
- **Post-merge check**: `ci` on `main` is green.
- **Rollback**: a revert PR. A bad release is deleted from GitHub Releases and the previous one stays the latest.
- **Required checks**: `ci`. A PR runs on Linux, and on all three systems only when it touches `native/`, `packaging/`, `srm/`, `requirements*` or `.github/`; a docs-only PR builds nothing. `main` always runs all three, so a Windows or macOS break can first show up in the post-merge check.

## Hard rules

- Do not make this repo public and do not put a licence on SRM until the mentor has confirmed it (ADR 0001).
- `srm/mc.txt` stays out of the repo: its origin is unknown.
