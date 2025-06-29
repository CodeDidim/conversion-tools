# Conversion Tools

This repository contains a set of small scripts used to move between a
public version of a project and a private one.  The tools can inject
private configuration data, export a cleaned copy for publishing and
validate that no sensitive information remains.

## Scripts

### `apply_template_context.py`

Copies a generic project to a new location and replaces `{{ KEY }}`
placeholders using values from a YAML profile. Tokens can include optional
whitespace, so both `{{KEY}}` and `{{ KEY }}` forms are replaced. An optional overlay
folder can be provided to apply company‑specific files on top of the
base project.  Every run writes a timestamped log file to the `log/`
directory and an optional `--verbose` flag prints those log lines to the
screen.

```
python scripts/apply_template_context.py <src> <dst> <profile> [--overlay <dir>] [--verbose]
```

### `revert_template_context.py`

Copies a private project to a new location and replaces private values with
their original `{{ KEY }}` placeholders using the same YAML profile.  The
replacement now uses regular expressions with word boundaries to avoid
matching partial words.  Logging behaviour mirrors that of
`apply_template_context.py`, writing to `log/` and supporting `--verbose`.

```
python scripts/revert_template_context.py <src> <dst> <profile> [--verbose]
```

### `export_to_public.py`

Walks a directory tree and copies files to a target location while
removing lines that contain private keywords such as company names or
internal e‑mail addresses.  Non‑text files are copied verbatim.  Each
run writes a log to the `log/` directory and accepts a `--verbose` flag
to echo log lines to the console.

```
python scripts/export_to_public.py <src> <dst> [--verbose]
```

### `validate_public_repo.py`

Scans the exported directory and reports occurrences of company
references, e‑mails, IP addresses or tokens.  The script exits with a
non‑zero status if any issues are found.

```
python scripts/validate_public_repo.py
```

### `github_visibility.py`

Manually toggles your GitHub repository between public and private states.
It reads the repository owner and name from `.workflow-config.yaml` and uses
the `GITHUB_TOKEN` environment variable for authentication.

```
python scripts/github_visibility.py hide   # make private
python scripts/github_visibility.py unhide # make public
```

### `manage_logs.py`

Removes old `.log` files from the `log/` directory. Specify the age in days.

```
python scripts/manage_logs.py --cleanup --days 30
```

## Configuration Profiles

Example YAML profiles can be found under `scripts/config_profiles/`.
They map placeholder names to actual values used by
`apply_template_context.py`.

## Running Tests

The repository includes unit tests for the scripts.  Run them with:

```
pytest -q
```

