import re, json, sys, http.server, socketserver
from urllib.parse import urlparse

class ZeroTrustEngine:
    def __init__(self):
        self.blocked_hosts = ['169.254.169.254', 'localhost', '127.0.0.1']
        self.blocked_patterns = [
            r'exec\s*\(', r'os\.system', r'subprocess', 
            r'cat\s+', r'rm\s+', r'mv\s+', r'wget\s+', r'curl\s+',
            r'nc\s+', r'bash\s+', r'sh\s+', r'\.\./'
        ]

    def scan(self, request):
        for host in self.blocked_hosts:
            if host in request: 
                return {"status": "BLOCKED", "reason": f"HOST_BLOCKED: {host}"}
        for pattern in self.blocked_patterns:
            if re.search(pattern, request, re.IGNORECASE):
                return {"status": "BLOCKED", "reason": f"COMMAND_BLOCKED: {pattern}"}
        return {"status": "SUCCESS", "risk": "low"}

class ZCoreOrchestrator:
    def __init__(self):
        self.zt = ZeroTrustEngine()
        self.id = "c9309187"
    
    def route(self, request):
        zt_result = self.zt.scan(request)
        if zt_result["status"] == "BLOCKED":
            zt_result["id"] = self.id
            return zt_result
        return {
            "status": "SUCCESS", 
            "id": self.id,
            "recon": {"task": "recon", "keywords": request.split()},
            "prediction": {"task": "predict", "risk": "low"},
            "result": f"[EXECUTED] Action réalisée pour: {request}"
        }

class ZCoreHandler(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        zcore = ZCoreOrchestrator()
        length = int(self.headers['Content-Length'])
        body = self.rfile.read(length).decode('utf-8')
        data = json.loads(body)
        result = zcore.route(data.get("request",""))
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(result).encode())

if __name__ == "__main__":
    if "--server" in sys.argv:
        PORT = 8080
        with socketserver.TCPServer(("", PORT), ZCoreHandler) as httpd:
            print(f"[Z-CORE-API] Serving at port {PORT}")
            httpd.serve_forever()
    else:
        zcore = ZCoreOrchestrator()
        req = " ".join(sys.argv[1:])
        print(json.dumps(zcore.route(req)))
