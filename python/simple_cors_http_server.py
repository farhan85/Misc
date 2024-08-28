#!/usr/bin/env python3

import argparse
from http.server import HTTPServer, SimpleHTTPRequestHandler


class CORSRequestHandler(SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Cache-Control', 'no-store, no-cache')
        SimpleHTTPRequestHandler.end_headers(self)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Runs a debug server that allows access to local files')
    parser.add_argument('-p', '--port', type=int, default=0)
    args = parser.parse_args()

    httpd = HTTPServer(('', args.port), CORSRequestHandler)
    print(f'Listening on port {httpd.server_address[1]}')
    httpd.serve_forever()
