import paramiko
from tabulate import tabulate
import logging
import io

log_stream = io.StringIO()
logging.basicConfig(stream=log_stream, level=logging.DEBUG)

filename = "firewalls.txt"

def parse_log_data(log_content):
    details = {
        "Key Exchange Algorithms": "",
        "Server Key Types": "",
        "Encryption Algorithms": "",
        "MAC Algorithms": ""
    }
    
    lines = log_content.split('\n')
    for line in lines:
        if "kex algos:" in line:
            details["Key Exchange Algorithms"] = line.split(': ')[1].split(', ')
        elif "server key:" in line:
            details["Server Key Types"] = line.split(': ')[1].split(', ')
        elif "server encrypt:" in line:
            details["Encryption Algorithms"] = line.split(': ')[1].split(', ')
        elif "server mac:" in line:
            details["MAC Algorithms"] = line.split(': ')[1].split(', ')
            
    return details

def fetch_ssh_details(hostname, port=22):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        client.connect(hostname, port, username='fake_admin', password='fake_password.', look_for_keys=False, allow_agent=False)
        return ['Connected successfully (unexpected)']
    except paramiko.ssh_exception.SSHException as e:
        return parse_log_data(log_stream.getvalue())
    finally:
        client.close()
        log_stream.truncate(0)
        log_stream.seek(0)

def read_ips(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def main(ip_filename):
    ips = read_ips(ip_filename)
    results = []

    for ip in ips:
        details = fetch_ssh_details(ip)
        results.append((ip, details))

    for result in results:
        print(f"IP Address: {result[0]}")
        for key, values in result[1].items():
            print(f"{key}:")
            for value in values:
                print(f"  - {value}")
        print("\n")


if __name__ == "__main__":
    main(filename)
