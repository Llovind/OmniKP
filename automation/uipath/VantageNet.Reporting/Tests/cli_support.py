"""Resolve an existing CLI only. Never install tooling or configure tenant authentication."""
import os
from pathlib import Path
import shutil

configured = os.environ.get('UIPATH_CLI')
resolved = configured or shutil.which('uip.cmd') or shutil.which('uip')
if not resolved or not Path(resolved).is_file():
    raise RuntimeError('Set UIPATH_CLI to your existing uip executable/launcher or add it to PATH. No installer is run.')
CLI = str(Path(resolved).resolve())
