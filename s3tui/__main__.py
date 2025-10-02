"""Main entry point for S3 TUI"""

import sys
from .app import S3TUI


def main():
    """Run the S3 TUI application"""
    try:
        app = S3TUI()
        app.run()
    except Exception as e:
        print(f"Error starting S3 TUI: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
