"""Shared paths. Set MOON_MAPS to the folder that holds the maps and index.csv
(the 'Moon Visibility Maps (moonsighting.com)' folder made by tools/Download-MoonMaps.ps1
or scripts/fetch_maps.py). Defaults to ./maps in the repo."""
import os, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / 'data'
MAPS = str(pathlib.Path(os.environ.get('MOON_MAPS', ROOT / 'maps'))) + os.sep
