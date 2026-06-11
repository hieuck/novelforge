import os
import sys
import subprocess
import time
import socket

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENGINE = os.path.join(REPO, "apps", "engine", "run.py")
DESKTOP = os.path.join(REPO, "apps", "desktop")


def get_free_port(start=5173, end=5200):
    for port in range(start, end):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            s.bind(("127.0.0.1", port))
            s.close()
            return port
        except OSError:
            continue
    return 5173


def main():
    port = get_free_port()
    print(f"[novelforge] Port {port}")
    engine = subprocess.Popen(
        [sys.executable, ENGINE],
        env={**os.environ, "NOVELFORGE_PORT": str(port), "PYTHONUNBUFFERED": "1"},
        cwd=os.path.dirname(ENGINE),
    )
    print(f"[novelforge] Engine pid={engine.pid}")

    time.sleep(0.9)
    desktop = subprocess.Popen(
        [sys.executable, "run-dev.py"],
        cwd=DESKTOP,
        env={**os.environ, "PORT": str(port)},
    )
    print(f"[novelforge] Desktop pid={desktop.pid}")
    engine.wait()
    sys.exit(engine.returncode or 0)


if __name__ == "__main__":
    main()
