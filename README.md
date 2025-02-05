# Sysweb

A minimalist Python project without external dependencies to control systemctl services and collect logs.

## API Endpoints Documentation

### GET /services
- Description: Lists systemd services.
- Response: JSON with a "services" key containing an array of service objects.
- Example:
  GET http://<server>:8000/services

**Curl Example:**
```bash
curl http://localhost:8000/services
```

### GET /logs
- Description: Retrieves system logs.
- Query Parameters:
  - service (optional): Filter logs by the service unit name.
- Response: JSON with a "logs" key containing an array of log lines.
- Example:
  GET http://<server>:8000/logs?service=nginx.service

**Curl Example:**
```bash
curl "http://localhost:8000/logs?service=nginx.service"
```

### POST /service
- Description: Performs an action on a specified service.
- Request Body (JSON):
  - service (string): The service unit name (e.g., "nginx.service").
  - action (string): One of "start", "stop", "restart", or "status". 
    - Note: 'start', 'stop', and 'restart' require elevated privileges (sudo).
- Response:
  - For "status": Returns a structured JSON object with keys like "unit", "description", and additional status properties.
  - For other actions: Returns the raw output as a string.
- Example:
  POST http://<server>:8000/service  
  Body:
  {
    "service": "nginx.service",
    "action": "restart"
  }

**Curl Example:**
```bash
curl -X POST http://localhost:8000/service \
     -H "Content-Type: application/json" \
     -d '{"service": "nginx.service", "action": "restart"}'
```


## Running the Server

Ensure the script has executable permissions and run:
```
./server.py
```
Alternatively, run with:
```
python3 server.py
```
By default, the server listens on port 8000. To specify a different port, pass the port as a command-line argument:
```
python3 server.py 8080
```
or set the PORT environment variable:
```
export PORT=8080
python3 server.py
```

## Running the Server as a Service

# Copy service file to systemd directory
```
sudo cp sysweb.service /etc/systemd/system/
```
# Reload systemd daemon
```
sudo systemctl daemon-reload
```

# Enable service to start on boot
```
sudo systemctl enable sysweb.service
```

# Start the service
```
sudo systemctl start sysweb.service
```
