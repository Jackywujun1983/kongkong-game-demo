"""Command line entrypoint for the 空空如也GameHub backend."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.config import DATABASE_PATH, DEFAULT_HOST, DEFAULT_PORT
from app.server import run_server


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Run the 空空如也GameHub API server.")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", default=DEFAULT_PORT, type=int)
    parser.add_argument("--database", default=str(DATABASE_PATH))
    return parser.parse_args()


def main() -> None:
    """Start the backend API server."""
    args = parse_args()
    run_server(
        host=args.host,
        port=args.port,
        database_path=Path(args.database),
    )


if __name__ == "__main__":
    main()
