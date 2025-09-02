# Manual Test Instructions

Follow these steps to verify the workflow manually. They mirror the automated tests but can be run without `pytest`.

1. Ensure `.workflow-config.yaml` exists in the repository root.
2. Run `python workflow.py private` to create the private working copy.
3. Modify files in `.workflow-temp/private` and confirm values from your placeholder values file were injected.
4. Run `python workflow.py public` to revert the private data back to placeholders.
5. Inspect the diff to make sure no secrets remain in the `template` directory.
6. (Optional) Check the current visibility state:
   ```bash
   python workflow.py status
   ```

See `TEST_SCENARIOS.md` for example situations to try.
