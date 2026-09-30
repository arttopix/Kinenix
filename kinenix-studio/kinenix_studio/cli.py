import argparse
import sys
import threading
import time
import webbrowser
import uvicorn

from . import __version__


def _launch_browser(url: str):
    # Wait briefly for uvicorn server to bind and start accepting connections
    time.sleep(0.8)
    try:
        webbrowser.open(url)
    except Exception:
        pass


def main():
    parser = argparse.ArgumentParser(
        prog="kinenix-studio",
        description="kinenix-studio: Developer Studio, Step Inspector, and Live Debugger for kinenix"
    )
    parser.add_argument(
        "--version", "-v",
        action="version",
        version=f"kinenix-studio {__version__}"
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host address to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port to listen on (default: 8080)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload on code changes (development mode)"
    )
    parser.add_argument(
        "--no-browser",
        action="store_true",
        help="Do not automatically launch the web browser"
    )

    args = parser.parse_args()

    from pathlib import Path
    frontend_dist = Path(__file__).resolve().parent.parent / "frontend" / "dist"
    has_frontend = frontend_dist.is_dir() and (frontend_dist / "index.html").is_file()

    server_url = f"http://{args.host}:{args.port}/" if has_frontend else f"http://{args.host}:{args.port}/docs"

    print("==================================================")
    print(f"Kinenix Studio v{__version__}")
    print(f"Web Interface: http://{args.host}:{args.port}/")
    print(f"Swagger API Docs: http://{args.host}:{args.port}/docs")
    if not args.no_browser:
        print("Launching Studio interface in browser...")
    print("==================================================")

    if not args.no_browser:
        threading.Thread(target=_launch_browser, args=(server_url,), daemon=True).start()

    uvicorn.run(
        "kinenix_studio.server:app",
        host=args.host,
        port=args.port,
        reload=args.reload
    )


if __name__ == "__main__":
    main()
