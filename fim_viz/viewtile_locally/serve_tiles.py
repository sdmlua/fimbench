#!/usr/bin/env python3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
import mimetypes
import pathlib

ROOT = str(pathlib.Path(__file__).resolve().parents[1])

class GzipPbfHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Serve from this folder (fim_viz)
        full = os.path.join(ROOT, path.lstrip("/"))
        return full

    def end_headers(self):
        # Allow local fetches / CORS for safety
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def guess_type(self, path):
        # Add .pbf mime
        if path.endswith(".pbf"):
            return "application/x-protobuf"
        return super().guess_type(path)

    def do_GET(self):
        # Let the parent build headers, then add gzip for .pbf
        supercls = super(GzipPbfHandler, self)
        path = self.translate_path(self.path)
        if path.endswith(".pbf") and os.path.exists(path):
            # Make sure browser treats it as gzip (mb-util exports gzipped PBFs)
            self.send_response(200)
            self.send_header("Content-Type", "application/x-protobuf")
            self.send_header("Content-Encoding", "gzip")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            with open(path, "rb") as f:
                self.wfile.write(f.read())
        else:
            super().do_GET()

def main():
    os.chdir(ROOT)
    port = 8000
    with ThreadingHTTPServer(("0.0.0.0", port), GzipPbfHandler) as httpd:
        print(f"Serving on http://localhost:{port}")
        httpd.serve_forever()

if __name__ == "__main__":
    main()
