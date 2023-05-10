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
    command = f'dig +noall +short {domain}'.split()     # I hate writing list of the commands and it's prone to error, so I just split it.
    ip = subprocess.Popen(command, stdout=subprocess.PIPE)
    ip, _ = ip.communicate()    # capture from stdout above
    ip = ip.decode().split()    # convert from bytes
    ip = ip[0] if len(ip) > 1 else ip[-1]   # I want the first ip in a list, otherwise the 'last' (for some reason it didn't like index 0 and so who cares)
    print(f'{domain} -> {ip}')  # print that sh*t

