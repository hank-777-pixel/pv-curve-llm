#!/usr/bin/env python3
import sys

if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "cli"

    try:
        if mode == "server":
            from server import app
            port = int(sys.argv[2]) if len(sys.argv) > 2 else 5000
            print(f"Starting PV Curve API Server on port {port}")
            print(f"Access the web interface at: http://127.0.0.1:{port}")
            app.run(host="127.0.0.1", port=port, debug=True)
        else:
            from cli import run_cli
            run_cli()
    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nUsage:")
        print("  python main.py          # Run CLI (default)")
        print("  python main.py server   # Run web server")
        print("  python main.py server 8080  # Run web server on custom port")
