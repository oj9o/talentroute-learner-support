"""Remove generated artifacts only; retain raw downloads, source and documentation."""
from pathlib import Path
import shutil
root = Path(__file__).resolve().parents[1]
for relative in ['outputs', 'data/processed', 'review']:
    path = root / relative
    if path.exists():
        shutil.rmtree(path)
