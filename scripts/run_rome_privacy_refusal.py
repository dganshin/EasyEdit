import sys
from pathlib import Path


SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from run_privacy_refusal_edit import main as _generic_main


if __name__ == "__main__":
    if "--method" not in sys.argv[1:]:
        sys.argv = [sys.argv[0], "--method", "ROME", *sys.argv[1:]]
    raise SystemExit(_generic_main())
