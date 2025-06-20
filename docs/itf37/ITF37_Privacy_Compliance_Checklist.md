# ITF-37 Privacy Compliance Checklist

Use this checklist before each commit to ensure no company data is exposed.

## Pre-Commit Verification

- [ ] Run `workflow.py public` to remove private files.
- [ ] Verify `.workflow-temp/` is absent or empty.
- [ ] Search the diff for tokens like `{{ COMPANY_` or real IP addresses.
- [ ] Ensure `company_profile.yaml` is not tracked by Git.
- [ ] Run unit tests to confirm template conversions succeed.

## Audit Trail Requirements

- Logs for each invocation of `workflow.py private` must be retained.
- Access to company profiles must be recorded in a secure log.
- Any detected privacy violation should trigger an incident report.

Follow this checklist to maintain compliance with corporate privacy policies.
