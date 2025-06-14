# Development Guide

Contributions are welcome. Please open a pull request with unit tests.

## Template-First Workflow

Always edit the files in the `template` directory rather than the generated
private output. The recommended cycle is:

```bash
# 1. Edit template files
vim template/src/config.py  # Has {{ API_KEY }}

# 2. Test your changes
python workflow.py private   # Injects real values
python .workflow-temp/private/main.py  # Run/test

# 3. Make more edits to the template
vim template/src/config.py

# 4. Test again
python workflow.py private

# 5. Ready to commit
python workflow.py public    # Clean for Git
git add template/
git commit -m "Added new feature"
```

### Why work on templates?

- **Version Control** – Git tracks the generic template, not your private values.
- **Consistency** – The same source code works everywhere with different values.
- **Safety** – Private values can't be committed accidentally.
- **Portability** – The code runs both at home and at work.

Editing files under `.workflow-temp/private/` is discouraged because changes are
lost when you re-run the workflow, they can't easily be converted back to the
template, and there is a higher risk of committing private data. Treat the
template as your source code and the private version as a build output.
