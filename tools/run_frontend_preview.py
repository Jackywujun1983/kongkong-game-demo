"""Serve the zero-dependency 空空如也GameHub frontend preview."""

from __future__ import annotations

from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
HOST = "127.0.0.1"
PORT = 5173


class PreviewRequestHandler(SimpleHTTPRequestHandler):
    """Serve preview.html as the frontend root page."""

    def do_GET(self) -> None:
        """Map the root path to the preview page."""
        if self.path in {"/", "/index.html"}:
            self.path = "/preview.html"
        super().do_GET()

    def log_message(self, format: str, *args: object) -> None:
        """Keep the preview server console quiet."""
        return


def main() -> None:
    """Start the frontend preview server."""
    handler = partial(PreviewRequestHandler, directory=str(FRONTEND_DIR))
    server = ThreadingHTTPServer((HOST, PORT), handler)
    print(f"空空如也GameHub preview running at http://{HOST}:{PORT}/")
    server.serve_forever()


if __name__ == "__main__":
    main()
