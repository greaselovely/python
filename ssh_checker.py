import paramiko
from tabulate import tabulate

def fetch_key_exchange_algorithms(hostname, port=22):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname, port, username='dummy', password='dummy', look_for_keys=False, allow_agent=False)
    except Exception as e:
        transport = client.get_transport()
        if transport:
            return transport.get_security_options().kex
        else:
            return ['No connection established']
    finally:
        client.close()

def read_ips(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def main(ip_filename):
    ips = read_ips(ip_filename)
    results = []

    for i, ip in enumerate(ips):
        print(f"{i}\t{ip}")
        algorithms = fetch_key_exchange_algorithms(ip)
        results.append((ip, algorithms))

    # Print the results in a table
    for result in results:
        print(f"IP Address: {result[0]}")
        print(tabulate([(alg,) for alg in result[1]], headers=['Supported Key Exchange Algorithms']))
        print("\n")

# Use the actual filename where your IP addresses are stored
main('ips.txt')
