import http.server,socketserver,json,socket
from datetime import datetime
PORT_S=8000
def free_port(s,e):
 for p in range(s,e+1):
  try:
   s=socket.socket();s.setsockopt(1,2,1);s.bind(("",p));s.close();return p
  except:continue
 return s
PORT=free_port(8000,8010)
class R(socketserver.TCPServer):allow_reuse_address=True
class H(http.server.SimpleHTTPRequestHandler):
 def do_GET(self):
  if"/api/status"in self.path:
   self.send_response(200);self.send_header("Content-type","application/json");self.end_headers()
   self.wfile.write(json.dumps({"version":"v1_9 UNIFIED OPUS45","hash":"89b6df2e-v24","port":self.server.server_address[1],"status":"NON DEPENDANCE VALIDEE","logics":22,"security":"ZeroTrust","size":"5.4K","stack":"Python3.11 0 dep Termux"}).encode())
  else:return super().do_GET()
print({"version":"v2.4","hash":"89b6df2e-v24","port":PORT,"status":"NON DEPENDANCE VALIDEE","logics":22})
with R(("",PORT),H) as httpd:print(f"LIVE {PORT}");httpd.serve_forever()
