#!/usr/bin/env python
"""
SAMM Web Editor Launcher

Launch the web-based SAMM model editor.
"""

import sys
from samm_editor.web.app import run_app

if __name__ == '__main__':
    print("Starting SAMM Web Editor...")
    print("Open your browser and navigate to: http://127.0.0.1:5000")
    print("Press Ctrl+C to stop the server")
    print()

    run_app(host='127.0.0.1', port=5000, debug=True)
