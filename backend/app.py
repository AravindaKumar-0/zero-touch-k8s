from http.server import BaseHTTPRequestHandler, HTTPServer
import json


class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        if self.path == "/health":
            response = {
                "status": "healthy",
                "service": "backend"
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            self.wfile.write(json.dumps(response).encode())

        elif self.path == "/api":
            response = {
                "message": "Backend API is working",
                "service": "zero-touch-k8s"
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()

            self.wfile.write(json.dumps(response).encode())

        else:
            self.send_response(404)
            self.end_headers()


server = HTTPServer(("0.0.0.0", 8080), Handler)

print("Backend running on port 8080")

server.serve_forever()