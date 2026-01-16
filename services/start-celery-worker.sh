#!/bin/bash
# Start Celery worker with a simple HTTP health check server

# Start a simple HTTP server for health checks in the background
python -c "
import http.server
import socketserver
import threading

class HealthCheckHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'OK')

    def log_message(self, format, *args):
        pass  # Suppress logs

PORT = 8080
Handler = HealthCheckHandler
httpd = socketserver.TCPServer(('', PORT), Handler)
print(f'Health check server started on port {PORT}')
httpd.serve_forever()
" &

# Wait a moment for the health server to start
sleep 2

# Start Celery worker (this blocks)
exec celery -A config worker -l INFO -Q default,translation,rag,assistance,maintenance -c 4
