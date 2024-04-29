import paramiko
import logging
import io


filename = "devices.txt"

logger = logging.getLogger("paramiko.transport")
logger.setLevel(logging.DEBUG)  # Set to DEBUG to capture all outputs
fh = logging.FileHandler('ssh_session.log')
fh.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)

def parse_log_data(log_content):
    details = {
        "Key Exchange Algorithms": "",
        "Server Key Types": "",
        "Encryption Algorithms": "",
        "MAC Algorithms": "",
        "Server Signature Algorithms": ""
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
        elif "Got EXT_INFO:" in line:
            sig_algs = line.split("{'server-sig-algs': b'")[1].split("'}")[0]
            details["Server Signature Algorithms"] = sig_algs.split(',')
            
    return details

def fetch_ssh_details(hostname, port=22):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    logger.addHandler(handler)

    try:
        client.connect(hostname, port, username='admin', password='password.', look_for_keys=False, allow_agent=False)
        return ['Connected successfully (unexpected)']
    except paramiko.ssh_exception.SSHException as e:
        return parse_log_data(log_stream.getvalue())
    finally:
        client.close()
        logger.removeHandler(handler)

def read_ips(filename):
    with open(filename, 'r') as file:
        return [line.strip() for line in file if line.strip()]

def main(ip_filename):
    ips = read_ips(ip_filename)
    results = []

    for ip in ips:
        print(ip)
        details = fetch_ssh_details(ip)
        results.append((ip, details))

    for result in results:
        print(f"IP Address: {result[0]}")
        for key, values in result[1].items():
            print(f"{key}:")
            if isinstance(values, list):
                for value in values:
                    print(f"  - {value}")
            else:
                print(f"  - {values}")
        print("\n")


if __name__ == "__main__":
    main(filename)
