# Troubleshooting

- If the public directory contains private data, ensure you reverted using the same profile used when injecting.
- If `workflow.py` reports missing directories, copy the example configuration files again to recreate them.
- When in doubt, delete the `.workflow-temp` directory and start again.

## Invalid Python Identifiers

If you see syntax errors like `class ACME CorpClient:` after conversion:

1. **Problem**: Placeholders used in class/function names contain spaces or special characters
2. **Solution**: The tool now automatically sanitizes these values:
   - `"ACME Corp"` → `"ACME_Corp"` in identifiers
   - `"123-test"` → `"test"` (removes leading digits)
   - Special characters are replaced with underscores

3. **Best Practice**: Define separate keys for identifiers in your profile:
   ```yaml
   COMPANY_NAME: "ACME Corp"  # For display
   COMPANY_CLASS: "ACMECorp"  # For class names
   ```

Validation: The workflow now warns about problematic values during validation


## Testing Instructions

After implementing all fixes:

1. Run the unit tests:
   ```bash
   pytest tests/unit/test_identifier_edge_cases.py -v
   ```

2. Test the full workflow:
   ```bash
   python workflow.py private
   # Check that class names are valid Python
   python -m py_compile .workflow-temp/private/*.py

   python workflow.py public
   # Verify placeholders are restored correctly

   # Run validation
   python workflow.py validate
   ```

### Expected Outcomes

- Class names with spaces are automatically fixed: `class ACME_CorpClient:`
- Validation warns about problematic placeholder usage
- Reversion correctly identifies and replaces sanitized identifiers
- No Python syntax errors in generated code
- Full backward compatibility with existing templates
