"""一键添加 SSH 公钥到服务器"""
import paramiko, os

PUBKEY = open(os.path.expanduser("~/.ssh/id_ed25519.pub")).read().strip()
HOST, USER, PASS = "150.158.130.73", "ubuntu", "Czh20031029"

c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
c.connect(HOST, username=USER, password=PASS, timeout=15)

c.exec_command("mkdir -p ~/.ssh && chmod 700 ~/.ssh")
_, stdout, _ = c.exec_command(f"echo '{PUBKEY}' >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys")
print(stdout.read().decode())
print("SSH key added. Testing...")
c.close()

# Verify key works
import subprocess
r = subprocess.run(["ssh", "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
                    "-i", os.path.expanduser("~/.ssh/id_ed25519"), f"{USER}@{HOST}",
                    "echo KEY_OK"], capture_output=True, text=True, timeout=15)
print(r.stdout.strip() or r.stderr[:200])
print("Done! Public key deployed.")
