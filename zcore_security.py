"""
ZCoreSecurity v1.5 Z-CORE | ZeroTrust Native
1 fichier, 0 dépendance externe, 100% stdlib
Règle: VALIDER > LOGGER > BLOQUER > NE JAMAIS EXÉCUTER
"""
import re, socket, ipaddress, datetime, json, os, threading, hashlib

class ZCoreSecurity:
    """Framework ZeroTrust pour Android Chaquopy / Termux / Linux"""
    _DANGEROUS_CMD_CHARS = [";", "|", "&&", "`", "$(", "\n", "\r", ">", "<"]
    _BLOCKED_NETWORKS = [
        ipaddress.ip_network("127.0.0.0/8"), ipaddress.ip_network("10.0.0.0/8"),
        ipaddress.ip_network("172.16.0.0/12"), ipaddress.ip_network("192.168.0.0/16"),
        ipaddress.ip_network("169.254.0.0/16"), ipaddress.ip_network("::1/128"),
        ipaddress.ip_network("fc00::/7"),
    ]
    def __init__(self, log_path="zcore_audit.log"):
        self.log_path = log_path
        self._lock = threading.Lock()
        self._rate = {}
    def check_h202(self, cmd: str) -> dict:
        """H202: Anti Command Injection - Blacklist + Length"""
        if not isinstance(cmd, str) or len(cmd) > 2048: return self._fail("H202", cmd, "Input invalide")
        if any(p in cmd for p in self._DANGEROUS_CMD_CHARS): return self._fail("H202", cmd, "Injection détectée")
        return self._ok("H202", cmd, "OK")
    def check_h203(self, url: str) -> dict:
        """H203: Anti-SSRF - DNS Resolution + IP Check"""
        if not re.match(r"^https?://", url, re.I): return self._fail("H203", url, "Schema invalide")
        try:
            host = url.split("://",1)[1].split("/")[0].split("@")[-1].split(":")[0]
            ips = {info[4][0] for info in socket.getaddrinfo(host, None)}
        except: return self._fail("H203", url, "DNS Error")
        for ip_str in ips:
            ip = ipaddress.ip_address(ip_str)
            if any(ip in net for net in self._BLOCKED_NETWORKS): return self._fail("H203", url, f"SSRF Block: {ip_str}")
        return self._ok("H203", url, f"OK - Resolved: {ips}")
    def scan_h204(self, target: str) -> dict:
        """H204: IP Validation Only - No network call"""
        try: ip = ipaddress.ip_address(target)
        except: return self._fail("H204", target, "IP invalide")
        if any(ip in net for net in self._BLOCKED_NETWORKS): return self._fail("H204", target, f"Plage interdite")
        return self._ok("H204", target, "IP Publique")
    def log_h205(self, event: dict) -> None:
        """H205: Audit Log JSONL + SHA256 integrity hash"""
        entry = {"ts": datetime.datetime.now(datetime.timezone.utc).isoformat(), "event": event}
        entry["sig"] = hashlib.sha256(json.dumps(entry["event"], sort_keys=True).encode()).hexdigest()[:12]
        try:
            with self._lock:
                with open(self.log_path, "a", encoding="utf-8") as f: f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except OSError: pass
    def _ok(self, c, i, r): res={"valid":True,"reason":r}; self.log_h205({"check":c,"in":str(i)[:256],"res":res}); return res
    def _fail(self, c, i, r): res={"valid":False,"reason":r}; self.log_h205({"check":c,"in":str(i)[:256],"res":res}); return res
    def read_audit_log(self, n=50) -> list:
        """Lecture des n derniers logs"""
        if not os.path.exists(self.log_path): return []
        with open(self.log_path,"r",encoding="utf-8") as f: return [json.loads(l) for l in f.readlines()[-n:] if l.strip()]

if __name__ == "__main__":
    zc = ZCoreSecurity()
    print("Z-CORE v1.5 ONLINE")
    print(zc.check_h202("ping 8.8.8.8; rm -rf /"))
    print(zc.check_h203("http://169.254.169.254/latest/meta-data/"))
    print(zc.scan_h204("192.168.1.1"))
    print("Logs:", zc.read_audit_log(2))
