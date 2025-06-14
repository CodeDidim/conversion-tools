# Manual Workflow

Follow these steps when working with the private and public repositories.
Always make edits in the `template` directory. Convert to private when you need
to test with real values and convert back to public before committing. Avoid
editing `.workflow-temp/private` directly because the next run of the workflow
will overwrite those files.

1. Clone the repository and create or update `.workflow-config.yaml`.
2. Run `workflow.py private` to inject private context.
3. Develop and commit changes to your **private** repository.
4. Before pushing publicly, run `workflow.py public` to revert private data.
5. Verify no private data remains in the diff.
6. (Optional) Check whether the repository is currently public or private:
   ```bash
   python workflow.py status
   ```
   The command prints the full path to the config file in use before showing the
   visibility state. It exits with an error if the config file cannot be found.
7. Push the cleaned changes to GitHub.

See `diagrams/manual-workflow.mermaid` for a visual overview of the process.
