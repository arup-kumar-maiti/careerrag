"""Start the CareerRAG server."""

import argparse

import uvicorn

from careerrag.server.app import create_app

DEFAULT_HOST = "127.0.0.1"
DEFAULT_NAME = "John Doe"
DEFAULT_PORT = 8000


def main() -> None:
    """Parse arguments and start the server."""
    parser = argparse.ArgumentParser(description="Start the CareerRAG server.")
    parser.add_argument("--host", default=DEFAULT_HOST, help="Set the bind address.")
    parser.add_argument("--name", default=DEFAULT_NAME, help="Set the display name.")
    parser.add_argument(
        "--port", default=DEFAULT_PORT, help="Set the port number.", type=int
    )
    args = parser.parse_args()
    app = create_app(args.name)
    uvicorn.run(app, host=args.host, port=args.port)


main()
