### Now Playing Monitor 2.0

This script handles reading Now Playing data from a file created by Foobar2000 and submitting it to NodeCG for use in GDQ layouts. This relies on Foobar being set up with the "Now Playing Simple" legacy component.

The script can be run directly if `uv` is installed. Without `uv`, use a Python dependency manager to install the requirements from `pyproject.toml` and then run `python3 np2.py`.

This project requires Python 3.13. Configuration is stored in `config.toml`.
