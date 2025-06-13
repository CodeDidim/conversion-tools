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
**At home (with GitHub access)**
```bash
python workflow.py init
export GITHUB_TOKEN='ghp_your_token_here'
```

**At company (without GitHub access)**
```bash
python workflow_company.py init
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

**At Company**
```bash
# Make repo public on your phone first!

git pull origin main
python workflow_company.py private
# Work with real values...
python workflow_company.py public
git push origin main
# Make repo private again on your phone
```

## 📁 Configuration
Create `.workflow-config.yaml`:
```yaml
github:
  owner: "yourusername"
  repo: "your-repo"
  token_env: "GITHUB_TOKEN"

profile: "scripts/config_profiles/company_profile.yaml"
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

![Workflow Diagram](docs/diagrams/manual-workflow.mermaid)

## 📖 Full Documentation
- [Architecture Overview](docs/ARCHITECTURE.md)
- [Manual Workflow Guide](docs/MANUAL_WORKFLOW.md)
- [Security Model](docs/SECURITY.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Development Guide](docs/DEVELOPMENT.md)

