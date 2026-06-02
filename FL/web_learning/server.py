#!/usr/bin/env python3
"""
Simple HTTP Server for Heap Sort Visualizer
Run this to serve the application locally
"""

import http.server
import socketserver
import webbrowser
import os
import sys

PORT = 8000

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Cache-Control', 'no-cache, no-store, must-revalidate')
        self.send_header('Pragma', 'no-cache')
        self.send_header('Expires', '0')
        super().end_headers()

def start_server():
    """Start the HTTP server and open browser"""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
        url = f"http://localhost:{PORT}"
        print("=" * 70)
        print("🌳 Heap Sort Visualizer Server")
        print("=" * 70)
        print(f"\nServer running at: {url}")
        print("\nOpening browser...")
        print("\nPress Ctrl+C to stop the server")
        print("=" * 70)
        
        # Open browser
        try:
            webbrowser.open(url)
        except:
            print(f"\nCould not open browser automatically.")
            print(f"Please open: {url}")
        
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n\nServer stopped.")
            sys.exit(0)

if __name__ == "__main__":
    start_server()

