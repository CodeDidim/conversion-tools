# Conversion Tools

Safely manage public and private versions of your codebase using template substitution.

Requires **Python 3.11** or newer. The project is tested against Python 3.11, 3.12, and 3.13.

## 🚀 Quick Start

### 1. Installation
```bash
git clone https://github.com/yourusername/conversion-tools.git
cd conversion-tools
pip install -r requirements.txt
```

### 2. Initial Setup
Copy the example configuration and set your GitHub token:
```bash
cp examples/.workflow-config.yaml.example .workflow-config.yaml
export GITHUB_TOKEN='ghp_your_token_here'
```

### 3. Basic Usage
**At Home**
```bash
# Convert to private mode for development
python workflow.py private
# Work with real values...
# Convert back to public before pushing
python workflow.py public
git push origin main
```

### Template Workflow
Edit the files under `template/` that contain `{{ PLACEHOLDERS }}`. Run
`python workflow.py private` whenever you need to test with real values and
`python workflow.py public` before committing. Avoid editing
`.workflow-temp/private` directly, as those files are regenerated.

## 📁 Configuration
Create `.workflow-config.yaml`:
```yaml
owner: "yourusername"
repo: "your-repo"
placeholder_values: "scripts/config_profiles/company_profile.yaml"
working_directory: ".workflow-temp"
template_source_dir: "template"
company_only_files: "private-overlay"  # optional private files
```
The `company_only_files` directory contains files that are only used in private mode.
These files are automatically removed when creating the public version.
See [docs/PRIVATE_OVERLAY.md](docs/PRIVATE_OVERLAY.md) for details.

## 🔒 Security Best Practices
- Never commit private values
- Keep `.workflow-config.yaml` in `.gitignore`
- Regularly run validation:
```bash
python scripts/validate_public_repo.py
```
- Use rollback if something goes wrong:
```bash
python workflow.py rollback
```
- Remove old log files:
```bash
python workflow.py clean-logs
```
- Check repository visibility:
```bash
python workflow.py status
```
This command now reports the full path to the configuration file before displaying
the repository visibility. It also exits with an error if the specified config file
does not exist.

![Workflow Diagram](docs/diagrams/manual-workflow.mermaid)

## 📖 Full Documentation
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Manual Workflow Guide](docs/MANUAL_WORKFLOW.md)
- [Security Model](docs/SECURITY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Development Guide](docs/DEVELOPMENT.md)
- [Private Overlay](docs/PRIVATE_OVERLAY.md)

