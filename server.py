
from http.server import BaseHTTPRequestHandler, HTTPServer, HTTPStatus
import time
import json
import urllib
import mimetypes
import os
import os.path

hostName = "0.0.0.0"
hostPort = 9000

# Get the directory of this .py file
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def guess_type(path):
    filetype, _ = mimetypes.guess_type(path)
    return filetype


class MyHandler(BaseHTTPRequestHandler):
    def serve_file(self):
        path = self.path
        if path == '/':
            path = 'index.html'

        # Remove the leading forward slash
        if path[0] == '/':
            path = path[1:]

        # Security, remove the ..
        path = path.replace('..', '')

        # Determine the fullpath
        path = os.path.join(BASE_DIR, path)

        try:
            data = open(path, 'rb').read()
            filetype = guess_type(path)
            self.send_response(200)
            self.send_header("Content-Type", filetype)
            self.end_headers()
            self.wfile.write(data)
        except:
            self.send_error(404)

    def do_POST(self):
        urlparts = urllib.parse.urlsplit(self.path)

        if self.path == "/cmd":
            data_string = str(self.rfile.read(int(self.headers['Content-Length'])), encoding="UTF-8")
            print("Command:", data_string)
            self.server.cmd_queue.put(json.loads(data_string))
            self.send_response(HTTPStatus.OK)
            self.send_header('Content-type', 'text/html')
            encoded = bytes('{"status":"In-Progress"}', "UTF-8")
            self.send_header('Content-Length', len(encoded))
            self.end_headers()
            self.wfile.write(encoded)
        else:
            self.send_error(404)

    def do_GET(self):
        urlparts = urllib.parse.urlsplit(self.path)
        q = urllib.parse.parse_qs(urlparts.query)

        if self.path == "/favicon.ico":
            self.send_error(404)
        elif self.path.startswith("/meas?"): # return specified meas fields
            q = urllib.parse.parse_qs(self.path.split("?",2)[1])
            fields = q.get("field") or () # list of meas fields to return or empty tuple if no fields specified
            meas_data = self.server.meas_func()
            m = { key: meas_data[key] for key in fields if key in meas_data }
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "application/json")
            encoded = bytes(json.dumps(m), "utf-8")
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        elif self.path == "/meas": # return all measurements
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-type", "application/json")
            encoded = bytes(json.dumps(self.server.meas_func()), "utf-8")
            self.send_header('Content-Length', str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)
        else:
            self.serve_file()
            #self.send_response(200)
            #self.send_header("Content-type", "text/html")
            #self.end_headers()
            #self.wfile.write(bytes("<html><head><title>Invalid request</title></head>", "utf-8"))
            #self.wfile.write(bytes("<p>You accessed path: '%s'</p>" % (self.path), "utf-8"))
            #self.wfile.write(bytes("</body></html>", "utf-8"))

# TODO:
# To serve multiple clients consider using socketserver.ThreadingMixIn
# or the new asyncio server: https://github.com/KeepSafe/aiohttp

class WebServer:
    def __init__(self, meas_func, cmd_queue):
        self.myServer = HTTPServer((hostName, hostPort), MyHandler)
        self.myServer.meas_func = meas_func
        self.myServer.cmd_queue = cmd_queue
        print(time.asctime(), "Server Starts - %s:%s" % (self.myServer.server_address))

    def serve(self):
        self.myServer.serve_forever()
        print(time.asctime(), "Server Stops - %s:%s" % (self.myServer.server_address))

    def stop(self):
        '''Must be called from another thread'''
        self.myServer.shutdown()
        self.myServer.server_close()


if __name__ == "__main__":
    def test_meas():
        return { 'meas1': 123, 'meas2': [1, 2, 3] }
    s = WebServer(test_meas)
    import threading
    t = threading.Thread(target = s.serve)
    t.start()
    time.sleep(10) # test serve for 10 s
    s.stop()
