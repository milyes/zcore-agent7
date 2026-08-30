#!/usr/bin/env python3
# Z-CORE AZURE_CLI v1.0
# NON DÉPENDANCE. ZERO TRUST NATIF.
# Ce script ne fait que déployer et auditer. L'IA reste 100% locale.

import subprocess
import json
import hashlib
from datetime import datetime
import os

AZURE_GROUP = "zcore-edge-rg"
AZURE_VM = "zcore-node-01"
AUDIT_FILE = "~/zcore-agent7/zcore_audit.log"

def sha256(data):
    return hashlib.sha256(data.encode()).hexdigest()[:12]

def log_audit(event_type, target, result):
    ts = datetime.now().isoformat()
    log_entry = {
        "ts": ts,
        "event": {"check": "AZURE_CLI", "type": event_type, "target": target, "res": result},
        "sig": sha256(ts + event_type + target)
    }
    with open(os.path.expanduser(AUDIT_FILE), "a") as f:
        f.write(json.dumps(log_entry) + "\n")
    print(f"[AUDIT] {event_type} -> {result['valid']}")

def az_deploy():
    """Déploie Z-CORE sur VM Azure. Z-CORE reste local sur la VM"""
    print("[Z-CORE] Déploiement en cours...")
    cmd = f"az vm run-command invoke -g {AZURE_GROUP} -n {AZURE_VM} --command-id RunShellScript --scripts 'git clone https://github.com/milyes/zcore-agent7.git 2>/dev/null || cd ~/zcore-agent7 && git pull && python zcore_orchestrator.py --daemon'"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    valid = res.returncode == 0
    log_audit("DEPLOY", AZURE_VM, {"valid": valid, "reason": "OK" if valid else res.stderr})
    return valid

def az_get_logs(lines=20):
    """Récupère zcore_audit.log depuis la VM. Aucune donnée IA ne transite"""
    print(f"[Z-CORE] Récupération des {lines} dernières lignes d'audit...")
    cmd = f"az vm run-command invoke -g {AZURE_GROUP} -n {AZURE_VM} --command-id RunShellScript --scripts 'tail -n {lines} ~/zcore-agent7/zcore_audit.log'"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    valid = res.returncode == 0
    log_audit("GET_LOGS", AZURE_VM, {"valid": valid, "reason": "OK" if valid else "Erreur"})
    return res.stdout if valid else "Erreur de récupération"

def az_status():
    """Check status VM sans toucher à Z-CORE"""
    cmd = f"az vm get-instance-view -g {AZURE_GROUP} -n {AZURE_VM} --query 'instanceView.statuses[1].displayStatus' -o tsv"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    status = res.stdout.strip()
    print(f"[Z-CORE] Status VM: {status}")
    return status

def az_block_ip(ip):
    """Bloque une IP sur la VM via iptables. Zero Trust"""
    print(f"[Z-CORE] Blocage IP {ip}...")
    cmd = f"az vm run-command invoke -g {AZURE_GROUP} -n {AZURE_VM} --command-id RunShellScript --scripts 'sudo iptables -A INPUT -s {ip} -j DROP'"
    res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    valid = res.returncode == 0
    log_audit("BLOCK_IP", ip, {"valid": valid, "reason": "IP bloquée" if valid else res.stderr})
    return valid

if __name__ == "__main__":
    print("="*40)
    print("Z-CORE AZURE_CLI v1.0 ONLINE")
    print("NON DÉPENDANCE. ZERO TRUST NATIF.")
    print("="*40)
    az_status()
