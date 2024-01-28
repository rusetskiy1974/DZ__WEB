
import json
import logging
from threading import Thread
import socket
import urllib.parse
from pathlib import Path
import mimetypes
from datetime import datetime, timedelta
from http.server import HTTPServer, BaseHTTPRequestHandler


BASE_DIR = Path()
BUFFER_SIZE = 1024
HTTP_PORT = 3000
HTTP_HOST = '0.0.0.0'
SOCKER_HOST = '127.0.0.1'
SOCKER_PORT = 5000

MESSAGES = {}
STORAGE_PATH = Path('storage')
DELTA_TIME_ZONE = 0


class GoItFramework(BaseHTTPRequestHandler):

    def do_GET(self):
        route = urllib.parse.urlparse(self.path)
        match route.path:
            case '/':
                self.send_html('index.html')
            case '/message':
                self.send_html('message.html')
            case _:
                file = BASE_DIR.joinpath(route.path[1:])
                if file.exists():
                    self.send_static(file)
                else:
                    self.send_html('error.html', 404)

    def do_POST(self):
        size = self.headers.get('Content-Length')
        data = self.rfile.read(int(size))

        client_socker = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        client_socker.sendto(data, (SOCKER_HOST, SOCKER_PORT))
        client_socker.close()

        self.send_response(302)
        self.send_header('Location', '/message')
        self.end_headers()

    def send_html(self, filename, status_code=200):
        self.send_response(status_code)
        self.send_header('Content-Type', 'text/html')
        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())

    def send_static(self, filename, status_code=200):
        self.send_response(status_code)
        mime_type, *_ = mimetypes.guess_type(filename)
        if mime_type:
            self.send_header('Content-Type', mime_type)
        else:
            self.send_header('Content-Type', 'text/plain')

        self.end_headers()
        with open(filename, 'rb') as file:
            self.wfile.write(file.read())


def save_data_from_form(data):
    parse_data = urllib.parse.unquote_plus(data.decode())
    try:
        parse_dict = {key: value for key, value in [el.split('=') for el in parse_data.split('&')]}
        with open('storage/data.json', 'w', encoding='utf-8') as file:
            MESSAGES.update({str(datetime.now()+timedelta(hours=DELTA_TIME_ZONE)): parse_dict})
            json.dump(MESSAGES, file, ensure_ascii=False, indent=4)
            file.write('\n')
    except ValueError as error:
        logging.error(error)
    except OSError as error:
        logging.error(error)


def run_socket_server(host, port):
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((host, port))
    logging.info("Starting socket server")
    try:
        while True:
            msg, address = server_socket.recvfrom(BUFFER_SIZE)
            logging.info(f"Socket receiver {address}: {msg}")
            save_data_from_form(msg)
    except KeyboardInterrupt:
        pass
    finally:
        server_socket.close()


def run_http_server(host, port):
    address = (host, port)
    http_server = HTTPServer(address, GoItFramework)
    logging.info("Starting http server")
    try:
        http_server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        http_server.server_close()


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG, format="%(threadName)s %(message)s")
    try:
        with open(STORAGE_PATH / 'data.json', 'r') as file:
            MESSAGES = json.load(file)
    except OSError as err:
        # logging.info(err)
        STORAGE_PATH.mkdir(exist_ok=True, parents=True)

    server = Thread(target=run_http_server, args=(HTTP_HOST, HTTP_PORT))
    server.start()

    server_socket = Thread(target=run_socket_server, args=(SOCKER_HOST, SOCKER_PORT))
    server_socket.start()
