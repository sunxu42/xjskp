import atexit
import subprocess
import time
import webbrowser


def main() -> None:
    proc = subprocess.Popen(
        [
            "python",
            "-m",
            "uvicorn",
            "src.service.app:app",
            "--host",
            "127.0.0.1",
            "--port",
            "18765",
        ]
    )

    def _cleanup() -> None:
        if proc.poll() is None:
            proc.terminate()
            proc.wait(timeout=5)

    atexit.register(_cleanup)
    time.sleep(1)
    webbrowser.open("http://127.0.0.1:18765")
    proc.wait()


if __name__ == "__main__":
    main()
