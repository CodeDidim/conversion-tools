# Private Overlay

The **private overlay** directory lets you add or override files that should
exist only in the private version of your project. The overlay contents are
copied on top of the template before tokens are replaced.

## Usage Aim
- Keep private-only scripts or configuration outside of the public template.
- Quickly patch sensitive files without modifying the main template directory.

## How To Use
1. Create a directory named `private-overlay` at the root of your repository.
   Mirror the layout of the files you want to override or add.
2. In `.workflow-config.yaml` set the `company_only_files` field if you use a custom
   path. The default is `private-overlay`.
3. Run `python workflow.py private` to build the private working directory.
   The overlay files will be copied into the workspace before token substitution.

Overlay files are ignored when generating the public directory so they never appear in
public repositories.
