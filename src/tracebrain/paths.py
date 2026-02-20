import json
import os
import shutil
from pathlib import Path
import platformdirs

# Default settings shipped with the package
API_ROOT = Path(__file__).parent
_DEFAULT_SETTINGS  = API_ROOT / "configs" / "settings.json"

# Resolve settings path from environment variable or default to user config directory 
SETTINGS_FILE = Path(os.getenv("SETTINGS_PATH", str(Path(platformdirs.user_config_dir("tracebrain")) / "settings.json")))

# Copy defaults to user config directory on first run
if not SETTINGS_FILE.exists():
    SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(_DEFAULT_SETTINGS, SETTINGS_FILE)
else:
    # Merge any new keys into existing user settings
    defaults = json.loads(_DEFAULT_SETTINGS.read_text())
    user = json.loads(SETTINGS_FILE.read_text())
    new_settings = {**defaults, **user}
    if new_settings != user:
        SETTINGS_FILE.write_text(json.dumps(new_settings, indent=2))