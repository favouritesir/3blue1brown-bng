"""Range-capable static server for the 3B1B Bengali platform.
Use INSTEAD OF `python -m http.server` so HTML5 video seeking (bookmarks) works.

  python serve_range.py            # port 8085
  python serve_range.py 9000       # custom port
"""
import http.server, socketserver, os, re, sys, mimetypes

ROOT = os.path.dirname(os.path.abspath(__file__))

class RangeHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **kw):
        super().__init__(*a, directory=ROOT, **kw)

    def send_head(self):
        path = self.translate_path(self.path)
        if os.path.isdir(path):
            return super().send_head()
        rng = self.headers.get('Range')
        if not rng:
            return super().send_head()
        m = re.match(r'bytes=(\d*)-(\d*)', rng.strip())
        if not m:
            return super().send_head()
        try:
            f = open(path, 'rb')
        except OSError:
            self.send_error(404); return None
        size = os.fstat(f.fileno()).st_size
        start = int(m.group(1)) if m.group(1) else 0
        end = int(m.group(2)) if m.group(2) else size - 1
        if start >= size:
            f.close(); self.send_error(416); return None
        end = min(end, size - 1)
        length = end - start + 1
        ctype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
        self.send_response(206)
        self.send_header('Content-Type', ctype)
        self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}')
        self.send_header('Content-Length', str(length))
        self.send_header('Last-Modified', self.date_time_string(os.fstat(f.fileno()).st_mtime))
        self.end_headers()
        f.seek(start)
        self._range_file = f
        self._range_remaining = length
        return self._range_iter()

    def _range_iter(self):
        f = self._range_file
        remaining = self._range_remaining
        while remaining > 0:
            chunk = f.read(min(64 * 1024, remaining))
            if not chunk: break
            remaining -= len(chunk)
            yield chunk
        f.close()

    def copyfile(self, source, outputfile):
        if hasattr(source, '__iter__') and not hasattr(source, 'read'):
            for chunk in source:
                outputfile.write(chunk)
        else:
            super().copyfile(source, outputfile)

    def end_headers(self):
        # advertise Range support on all responses
        if 'Accept-Ranges' not in self._headers_buffer_names():
            self.send_header('Accept-Ranges', 'bytes')
        super().end_headers()

    def _headers_buffer_names(self):
        return [h.decode('latin1').split(':')[0] for h in self._headers_buffer]

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8085
    print(f'Serving {ROOT} on http://127.0.0.1:{port} (Range enabled)')
    with socketserver.TCPServer(('127.0.0.1', port), RangeHandler) as httpd:
        httpd.serve_forever()
