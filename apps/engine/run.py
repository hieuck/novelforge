import os
import sys
import uvicorn

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

HOST = os.environ.get("NOVELFORGE_HOST", "127.0.0.1")
PORT = int(os.environ.get("NOVELFORGE_PORT", "9000"))

if __name__ == "__main__":
    uvicorn.run("app:app", host=HOST, port=PORT, log_level="info")
