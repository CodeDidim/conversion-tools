# Architecture

The project consists only of local scripts. There is no server component.
Files are converted by applying a placeholder values and optional overlay before generating the public build.

## Private Overlay
See [PRIVATE_OVERLAY.md](PRIVATE_OVERLAY.md) for full details. In short, any
files placed in the `private-overlay` directory are copied into the working
area when running `workflow.py private`. This lets you maintain private-only
files without modifying the main template. The overlay files are removed again
when running `workflow.py public` so nothing leaks into the public build.
