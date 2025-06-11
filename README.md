# Conversion Tools

This repository contains a set of small scripts used to move between a
public version of a project and a private one.  The tools can inject
private configuration data, export a cleaned copy for publishing and
validate that no sensitive information remains.

## Scripts

### `inject_private_context.py`

Copies a generic project to a new location and replaces `{{ KEY }}`
placeholders using values from a YAML profile.  An optional overlay
folder can be provided to apply company‑specific files on top of the
base project.

```
python scripts/inject_private_context.py <src> <dst> <profile> [--overlay <dir>]
```

### `revert_private_context.py`

Copies a private project to a new location and replaces private values with
their original `{{ KEY }}` placeholders using the same YAML profile.

```
python scripts/revert_private_context.py <src> <dst> <profile>
```

### `export_to_public.py`

Walks a directory tree and copies files to a target location while
removing lines that contain private keywords such as company names or
internal e‑mail addresses.  Non‑text files are copied verbatim.

```
python scripts/export_to_public.py <src> <dst>
```

### `validate_public_repo.py`

Scans the exported directory and reports occurrences of company
references, e‑mails, IP addresses or tokens.  The script exits with a
non‑zero status if any issues are found.

```
python scripts/validate_public_repo.py
```

## Configuration Profiles

Example YAML profiles can be found under `scripts/config_profiles/`.
They map placeholder names to actual values used by
`inject_private_context.py`.

## Running Tests

The repository includes unit tests for the scripts.  Run them with:

```
pytest -q
```

