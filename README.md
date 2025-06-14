# Conversion Tools

Safely manage public and private versions of your codebase using template substitution.

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

## 📁 Configuration
Create `.workflow-config.yaml`:
```yaml
owner: "yourusername"
repo: "your-repo"
profile: "scripts/config_profiles/company_profile.yaml"
temp_dir: ".workflow-temp"
template: "template"
```

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

