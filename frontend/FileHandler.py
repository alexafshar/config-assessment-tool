import logging
import os
import subprocess
import sys

if sys.version_info >= (3, 0):
    from http.server import BaseHTTPRequestHandler, HTTPServer
    from urllib import parse
else:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
    from urlparse import urlparse, parse_qsl


def getPlatform():
    platform = sys.platform
    if sys.platform == "linux":
        proc_version = open("/proc/version").read()
        if "microsoft" in proc_version:
            platform = "wsl"
    return platform


def openFile(filename):
    logging.info(f"Opening file: {filename}")
    platform = getPlatform()

    if platform == "darwin":
        subprocess.call(("open", filename))
    elif platform in ["win64", "win32"]:
        os.startfile(filename.replace("/", "\\"))
    elif platform == "wsl":
        subprocess.call(["wslview", filename])
    else:  # linux variants
        subprocess.call(("xdg-open", filename))


def openFolder(path):
    logging.info(f"Opening folder: {path}")
    platform = getPlatform()

    if platform == "darwin":
        subprocess.call(["open", "--", path])
    elif platform in ["win64", "win32"]:
        subprocess.call(["start", path])
    elif platform == "wsl":
        command = f"explorer.exe `wslpath -w {path}`"
        subprocess.run(["bash", "-c", command])
    else:  # linux variants
        subprocess.call(["xdg-open", "--", path])


class MyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

        if sys.version_info >= (3, 0):
            query_components = dict(parse.parse_qsl(parse.urlsplit(self.path).query))
        else:
            query_components = dict(parse_qsl(urlparse(self.path).query))

        if query_components["type"] == "file":
            openFile(query_components["path"])
        if query_components["type"] == "folder":
            openFolder(query_components["path"])

    def log_message(self, format, *args):
        logging.info("%s - - [%s] %s" % (self.address_string(), self.log_date_time_string(), format % args))


if __name__ == "__main__":
    if not os.path.exists("logs"):
        os.makedirs("logs")
    if not os.path.exists("output"):
        os.makedirs("output")

    # noinspection PyArgumentList
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[
            logging.FileHandler("logs/config-assessment-tool-frontend.log"),
        ],
    )

    hostName = "localhost"
    serverPort = 1337

    logging.info(f"Starting FileHandler on {hostName}:{serverPort}")
    webServer = HTTPServer((hostName, serverPort), MyServer)
    webServer.serve_forever()
