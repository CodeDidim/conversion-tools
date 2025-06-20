# ITF-37 Developer Privacy Guide

This guide provides daily workflow steps for working safely with the templated dual environment.

## 1. Setup Profiles

Place the following YAML profiles outside version control:

```yaml
# company_profile.yaml
work_environments:
  company_environment:
    profile: "company_profile.yaml"
    location: "conversion-tools/.workflow-temp/"
    contains: "Real IPs, Jama tokens, internal resources"
    visibility: "Private, never committed"
  home_environment:
    profile: "generic_profile.yaml"
    location: "conversion-tools/.workflow-temp/"
    contains: "Generic IPs, mock services, public tools"
    visibility: "Safe for home networks"
```

## 2. Daily Workflow

1. **Pull latest templates**
   ```bash
   git pull
   ```
2. **Generate private files**
   ```bash
   workflow.py private --profile company_profile.yaml
   ```
3. **Run tests**
   Execute your normal integration tests or automation using the generated configs.
4. **Revert to public files**
   ```bash
   workflow.py public
   ```
5. **Commit changes**
   ```bash
   git add .
   git commit -m "Update tests"
   ```
6. **Push**
   ```bash
   git push
   ```

## 3. Common Pitfalls

- Forgetting to run `workflow.py public` before committing. Use a pre-commit hook if available.
- Storing `company_profile.yaml` in the repository. Keep it on your workstation only.
- Running tests against production hardware from home. Use the generic profile instead.

## 4. Troubleshooting

If `workflow.py private` fails, check that your profile file paths are correct and that the `.workflow-temp/` directory is writable. If pre-commit hooks block your commit, run `workflow.py public` again and ensure no private files remain.

Follow this guide to ensure all team members maintain privacy compliance during daily development.
