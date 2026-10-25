"""python -m borer_api: one uvicorn process (the court's queue lives in it), bound to
BORER_HOST (default 0.0.0.0) : BORER_PORT. Phones use scripts/tunnel.sh, not the LAN."""
import os

import uvicorn

from borer_api.app import create_app

if __name__ == "__main__":  # guard: forkserver workers import this module too
    uvicorn.run(create_app(), host=os.environ.get("BORER_HOST", "0.0.0.0"),
                port=int(os.environ.get("BORER_PORT", "8000")))
