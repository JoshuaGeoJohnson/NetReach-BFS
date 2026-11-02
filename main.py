"""
main.py
-------
Entry point for NetReach – Emergency Communication Network Reachability Analyzer.

Run with:
    python main.py
"""

import sys
import os

# Ensure the project directory is on the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from gui import NetReachApp


def main():
    app = NetReachApp()
    app.mainloop()


if __name__ == "__main__":
    main()
