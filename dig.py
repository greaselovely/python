import subprocess

"""
ok, so you wanna do a quick dig on domains and only retrieve the first IP.  Cool.
Linux / Mac only unless you have dig on Windows
"""

domains = ["google.com",
"microsoft.com",
"facebook.com",
"apple.com",
"instagram.com",
"linkedin.com",
"pickle.com"]

for domain in domains:
    command = f'dig +noall +short {domain}'.split()
    ip = subprocess.Popen(command, stdout=subprocess.PIPE)
    ip, _ = ip.communicate()
    ip = ip.decode().split()
    print(f'{domain} -> {ip[0] if len(ip) > 1 else ip[-1]}')

