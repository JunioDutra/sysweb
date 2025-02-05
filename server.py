#!/usr/bin/env python3
import subprocess
import json
import os
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse

class SyswebHandler(BaseHTTPRequestHandler):
    def _set_headers(self, content_type='application/json'):
        self.send_response(200)
        self.send_header('Content-type', content_type)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == "/":
            self._serve_index()
        elif parsed_path.path == '/services':
            self._list_services()
        elif parsed_path.path == '/logs':
            self._get_logs()
        else:
            self.send_error(404, "Endpoint not found")

    def do_POST(self):
        parsed_path = urlparse(self.path)
        if parsed_path.path == '/service':
            self._service_action()
        else:
            self.send_error(404, "Endpoint not found")

    def _list_services(self):
        try:
            output = subprocess.check_output(
                ['systemctl', 'list-units', '--type=service', '--no-pager'],
                universal_newlines=True
            )
            self._set_headers()
            output = self._format_output(output)
            self.wfile.write(json.dumps({'services': output}).encode())
        except Exception as e:
            self.send_error(500, str(e))

    def _format_output(self, output: str) -> list:
        lines = output.splitlines()
        services = []
        header_found = False
        for line in lines:
            if not header_found:
                if "UNIT" in line and "LOAD" in line:
                    header_found = True
                continue
            if line.strip() == "" or "loaded units listed" in line:
                continue
            if ".service" not in line:
                continue
            unit = line[0:56].strip()
            load = line[56:63].strip()
            active = line[63:70].strip()
            sub = line[70:78].strip()
            description = line[78:].strip()
            services.append({
                "unit": unit,
                "load": load,
                "active": active,
                "sub": sub,
                "description": description
            })
        return services

    def _service_action(self):
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        try:
            data = json.loads(post_data)
            service = data.get('service')
            action = data.get('action')
            if not service or not action or action not in ['restart', 'stop', 'status', 'start']:
                self.send_error(400, "Invalid parameters: require 'service' and a valid 'action'")
                return
            if action in ['restart', 'start', 'stop']:
                cmd = ['sudo', 'systemctl', action, service]
            else:
                cmd = ['systemctl', action, service]
            output = subprocess.check_output(
                cmd,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            self._set_headers()
            if action == 'status':
                structured = self._format_status(output)
                self.wfile.write(json.dumps({'result': structured}).encode())
            else:
                self.wfile.write(json.dumps({'result': output}).encode())
        except subprocess.CalledProcessError as cpe:
            self.send_error(500, cpe.output)
        except Exception as e:
            self.send_error(500, str(e))

    def _format_status(self, output: str) -> dict:
        result = {}
        lines = [line.strip() for line in output.splitlines() if line.strip()]
        months = {"Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"}
        for line in lines:
            if line[:3] in months:
                continue
            if line.startswith("●"):
                line = line.lstrip("●").strip()
                if " - " in line:
                    unit, desc = line.split(" - ", 1)
                    result["unit"] = unit.strip()
                    result["description"] = desc.strip()
                else:
                    result["unit"] = line
            elif ":" in line:
                key, val = line.split(":", 1)
                norm_key = key.strip().lower().replace(" ", "_")
                result[norm_key] = val.strip()
        return result

    def _get_logs(self):
        try:
            from urllib.parse import parse_qs
            parsed_url = urlparse(self.path)
            query_params = parse_qs(parsed_url.query)
            service_filter = query_params.get('service', [None])[0]
            cmd = ['journalctl', '--no-pager', '-n', '100']
            if service_filter:
                cmd.extend(['-u', service_filter])
            output = subprocess.check_output(
                cmd,
                universal_newlines=True
            )
            lines = [line.strip() for line in output.splitlines() if line.strip()]
            self._set_headers(content_type='application/json')
            self.wfile.write(json.dumps({'logs': lines}).encode())
        except Exception as e:
            self.send_error(500, str(e))

    def _serve_index(self):
        try:
            path = os.path.join(os.path.dirname(__file__), "index.html")
            with open(path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.send_header("Content-Length", str(len(content)))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error(500, str(e))

def run(server_class=HTTPServer, handler_class=SyswebHandler, port=8000):
    server_address = ('0.0.0.0', port)
    httpd = server_class(server_address, handler_class)
    print(f"Sysweb server running on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    port = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PORT")
    port = int(port) if port is not None else 8000
    run(port=port)
