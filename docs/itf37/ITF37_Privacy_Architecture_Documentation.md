# ITF-37 Privacy Architecture Documentation

## Executive Summary

The templated dual work environment system protects company privacy by ensuring no sensitive information ever resides in source control. Developers seamlessly switch between sanitized home setups and fully featured company environments without risking leaks. This approach aligns with corporate security policy, enables compliance audits, and mitigates exposure risk.

## Table of Contents
1. [Objective](#objective)
2. [Risk Mitigation](#risk-mitigation)
3. [Compliance Alignment](#compliance-alignment)
4. [Technical Architecture Overview](#technical-architecture-overview)
5. [Privacy Controls Detail](#privacy-controls-detail)
6. [Home Development Security](#home-development-security)
7. [Company Environment Security](#company-environment-security)
8. [Developer Workflow Documentation](#developer-workflow-documentation)
9. [Compliance and Audit](#compliance-and-audit)
10. [Security Considerations](#security-considerations)
11. [Integration with Company Policies](#integration-with-company-policies)

<a name="objective"></a>

## Objective

This document explains how the ITF templated workflow allows developers to work both from home and in the office using the same codebase while preventing accidental exposure of confidential data. By leveraging placeholders for all secrets and environment-specific values, the framework enforces security across the development lifecycle.

<a name="risk-mitigation"></a>

## Risk Mitigation

* **No secrets in version control.** Template files only contain placeholders like `{{ API_KEY }}` preventing hard-coded credentials.
* **Automatic conversion workflow.** `workflow.py private` inserts real values when needed and `workflow.py public` cleans them before commits.
* **Dual profile enforcement.** Separate profiles keep private infrastructure inaccessible outside the office.

<a name="compliance-alignment"></a>

## Compliance Alignment

The system aligns with security standards such as GDPR and SOX by keeping sensitive data in isolated profiles, logging access to real configurations, and ensuring sanitized code is always stored in Git.

<a name="technical-architecture-overview"></a>

## Technical Architecture Overview

```mermaid
flowchart TD
    A[Developer] --> B{Environment?}
    B -->|Company| C[Load company_profile.yaml]
    B -->|Home| D[Load generic_profile.yaml]
    C --> E[Real IP: {{ COMPANY_JAMA_IP }}]
    D --> F[Mock IP: {{ GENERIC_JAMA_IP }}]
    E --> G[Access Real Jama/Hardware]
    F --> H[Access Mock Services]
    G --> I[workflow.py public before commit]
    H --> J[Safe to commit templates]
```

Developers run the same tests in either environment because the framework injects the appropriate configuration at runtime.

<a name="privacy-controls-detail"></a>

## Privacy Controls Detail

### Template Placeholder System

All configuration files reference variables using the `{{ VARIABLE }}` syntax. For example:

```yaml
jama_config:
  base_url: "{{ JAMA_BASE_URL }}"
  api_key: "{{ JAMA_API_KEY }}"
  project_id: "{{ JAMA_PROJECT_ID }}"

device_config:
  moxa_device: "{{ MOXA_IP_ADDRESS }}"
  test_ports: "{{ TEST_PORT_RANGE }}"
```

### Conversion Tool Security

The `workflow.py` tool tracks every file that is converted from template to private form. It prevents accidental commits of private data by requiring `workflow.py public` to be run before pushing.

### File System Isolation

Generated private files reside in `.workflow-temp/` and are excluded from version control, keeping sensitive data out of the repo.

### Git Hook Protection

Optional pre-commit hooks scan for tokens or IP patterns to ensure no private information remains.

<a name="home-development-security"></a>

## Home Development Security

* **Generic Profile Usage.** Developers at home load `generic_profile.yaml` which contains mock services and public resources only.
* **Mock Service Integration.** Generic services simulate company hardware so tests remain valid.
* **Network Isolation.** The home environment has no direct access to internal company infrastructure.
* **Code Portability.** Because the same placeholders are used, code runs the same tests in either environment.

<a name="company-environment-security"></a>

## Company Environment Security

* **Temporary File Management.** Real configs are generated only inside `.workflow-temp/` and deleted by `workflow.py public`.
* **Access Control.** Only authorized users possess the `company_profile.yaml` file.
* **Audit Trail.** Usage of real data is logged for review.
* **Cleanup Verification.** Before commits, the tool confirms that all private files have been removed from the working tree.

<a name="developer-workflow-documentation"></a>

## Developer Workflow Documentation

Daily development cycle:

```bash
# 1. Get latest templates
git pull
# 2. Generate private configs
workflow.py private --profile company_profile.yaml
# ... run tests against real hardware ...
# 3. Clean workspace for commit
workflow.py public
# 4. Commit only sanitized files
git add .
git commit -m "Update tests"
# 5. Push safely
git push
```

<a name="compliance-and-audit"></a>

## Compliance and Audit

* **Security Review Process.** Changes to the privacy system are reviewed by security leads.
* **Audit Logging.** Access to `company_profile.yaml` and runs of `workflow.py private` are logged.
* **Incident Response.** If real data is exposed, triggers notify the security team and instructions for rotating credentials are followed.
* **Regular Reviews.** Quarterly audits verify adherence to privacy procedures.

<a name="security-considerations"></a>

## Security Considerations

### Threat Model

The system protects against the following threats:
* Accidental commits of credentials.
* Unauthorized access to company infrastructure from home.
* Data exfiltration via public repositories.

### Attack Scenarios

An attacker with access only to the public repository cannot obtain company secrets because the profiles and temporary files are ignored by Git. Even if a developer mistakenly commits the `.workflow-temp/` directory, pre-commit hooks flag the presence of IP addresses or API keys.

### Defense in Depth

1. Template substitution ensures no hardcoded secrets.
2. Dual profiles segregate production and home environments.
3. Git hooks and code review catch remaining issues.

### Failure Modes

If a developer forgets to run `workflow.py public`, the commit will include files containing placeholders or real data. The pre-commit checks halt the process and instruct the developer to clean their workspace.

<a name="integration-with-company-policies"></a>

## Integration with Company Policies

* **Data Classification.** Templates are classified as public while profiles containing real data are restricted.
* **Remote Work Policy.** The home environment uses sanitized values and prevents access to internal networks, conforming to remote work guidelines.
* **Third-Party Access.** Contractors can clone the repository and work with generic profiles without seeing company data.
* **Regulatory Compliance.** Keeping sensitive data in isolated profiles supports GDPR and SOX requirements for data minimization and auditability.

---

This document illustrates how the templated dual work environment enables flexible development while upholding strict privacy guarantees. The following guides and checklist further detail the day-to-day process and verification steps.
