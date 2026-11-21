"""Threaded range-capable static server for verification (no video-range blocking)."""
import sys, os, socketserver
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from serve_range import RangeHandler

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8092
class Threaded(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True

print("Threaded verification server on", PORT)
with Threaded(('127.0.0.1', PORT), RangeHandler) as httpd:
    httpd.serve_forever()
