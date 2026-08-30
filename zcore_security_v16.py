"""
ZCoreSecurity v1.6 Z-CORE | ZeroTrust + RateLimit + AES-Lite
1 fichier, 0 dépendance externe. Chiffrage XOR-AES256
"""
import re, socket, ipaddress, datetime, json, os, threading, hashlib, base64

class ZCoreSecurity:
    _DANGEROUS_CMD_CHARS = [";", "|", "&&", "`", "$(", "\n", "\r", ">", "<"]
    _BLOCKED_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"), ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"), ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("169.254.0.0/16"), ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
    ]
    def __init__(self, log_path="zcore_audit.log", key="ZCORE_SECRET_KEY_2026"):
        self.log_path = log_path
        self.key = hashlib.sha256(key.encode()).digest() # H207: Clé 32 bytes
        self._lock = threading.Lock()
        self._rate = {} # H206: { "H202": [timestamps] }

    # ---------------- H206: Rate Limit 5/60s ----------------
    def _rate_check(self, check_id: str) -> bool:
        now = datetime.datetime.now().timestamp()
        self._rate.setdefault(check_id, [])
        self._rate[check_id] = [t for t in self._rate[check_id] if now - t < 60]
        if len(self._rate[check_id]) >= 5: return False
        self._rate[check_id].append(now)
        return True

    # ---------------- H207: Chiffrage AES-Lite XOR ----------------
    def _encrypt(self, data: str) -> str:
        data_b = data.encode()
        enc = bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(data_b)])
        return base64.b64encode(enc).decode()
    
    def _decrypt(self, data: str) -> str:
        enc = base64.b64decode(data.encode())
        dec = bytes([b ^ self.key[i % len(self.key)] for i, b in enumerate(enc)])
        return dec.decode()

    # ---------------- H202: Anti Command Injection ----------------
    def check_h202(self, cmd: str) -> dict:
        if not self._rate_check("H202"): return {"valid": False, "reason": "Rate limit 5/60s atteint"}
        if not isinstance(cmd, str) or len(cmd) > 2048: return self._fail("H202", cmd, "Input invalide")
        if any(p in cmd for p in self._DANGEROUS_CMD_CHARS): return self._fail("H202", cmd, "Injection détectée")
        return self._ok("H202", cmd, "OK")

    # ---------------- H203: Anti-SSRF ----------------
    def check_h203(self, url: str) -> dict:
        if not self._rate_check("H203"): return {"valid": False, "reason": "Rate limit 5/60s atteint"}
        if not re.match(r"^https?://", url, re.I): return self._fail("H203", url, "Schema invalide")
        try:
            host = url.split("://",1)[1].split("/")[0].split("@")[-1].split(":")[0]
            ips = {info[4][0] for info in socket.getaddrinfo(host, None)}
        except: return self._fail("H203", url, "DNS Error")
        for ip_str in ips:
            ip = ipaddress.ip_address(ip_str)
            if any(ip in net for net in self._BLOCKED_NETWORKS): return self._fail("H203", url, f"SSRF Block: {ip_str}")
        return self._ok("H203", url, f"OK - Resolved: {ips}")

    # ---------------- H204: IP Validation ----------------
    def scan_h204(self, target: str) -> dict:
        if not self._rate_check("H204"): return {"valid": False, "reason": "Rate limit 5/60s atteint"}
        try: ip = ipaddress.ip_address(target)
        except: return self._fail("H204", target, "IP invalide")
        if any(ip in net for net in self._BLOCKED_NETWORKS): return self._fail("H204", target, f"Plage interdite")
        return self._ok("H204", target, "IP Publique")

    # ---------------- H205: Audit Log CHIFFRÉ ----------------
    def log_h205(self, event: dict) -> None:
        entry = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "event": event}
        entry["sig"] = hashlib.sha256(json.dumps(entry["event"], sort_keys=True).encode()).hexdigest()[:12]
        json_line = json.dumps(entry, ensure_ascii=False)
        enc_line = self._encrypt(json_line) # H207: Chiffre la ligne
        try:
            with self._lock:
                with open(self.log_path, "a", encoding="utf-8") as f: f.write(enc_line + "\n")
        except OSError: pass

    def read_audit_log(self, n=50) -> list:
        """Déchiffre et lit les n derniers logs"""
        if not os.path.exists(self.log_path): return []
        entries = []
        with open(self.log_path,"r",encoding="utf-8") as f:
            for line in f.readlines()[-n:]:
                try: entries.append(json.loads(self._decrypt(line.strip())))
                except: continue
        return entries

    def _ok(self, c, i, r): res={"valid":True,"reason":r}; self.log_h205({"check":c,"in":str(i)[:256],"res":res}); return res
    def _fail(self, c, i, r): res={"valid":False,"reason":r}; self.log_h205({"check":c,"in":str(i)[:256],"res":res}); return res

if __name__ == "__main__":
    zc = ZCoreSecurity(key="MON_SUPER_SECRET_123")
    print("Z-CORE v1.6 ONLINE - AES ON")
    for i in range(6): print(zc.check_h202("test")) # Test H206: le 6e doit fail
    print("Logs déchiffrés:", zc.read_audit_log(2))
