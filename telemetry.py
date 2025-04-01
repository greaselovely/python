import getpass
import requests
import xmltodict
from urllib3.exceptions import InsecureRequestWarning

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

def check_device_certificates(api_key, base_url):
    url = f"{base_url}/api/?type=op&cmd=<show><certificate><info></info></certificate></show>&key={api_key}"
    try:
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()
        data = xmltodict.parse(response.text)
        
        certificates = data.get('response', {}).get('result', {}).get('entry', [])
        if not isinstance(certificates, list):
            certificates = [certificates]
        
        all_valid = True
        for cert in certificates:
            name = cert.get('name', 'Unknown')
            valid_to = cert.get('valid-to', 'Unknown')
            print(f"Certificate: {name}, Valid until: {valid_to}")
            if "Not-valid" in valid_to:
                all_valid = False
        
        return all_valid
    except requests.exceptions.RequestException as e:
        print(f"Error checking certificates: {e}")
        return False

def check_telemetry_enabled(api_key, base_url):
    url = f"{base_url}/api/?type=op&cmd=<show><system><telemetry></telemetry></system></show>&key={api_key}"
    try:
        response = requests.get(url, verify=False, timeout=10)
        response.raise_for_status()
        
        data = xmltodict.parse(response.text)
        
        if data['response']['@status'] == 'error':
            error_msg = data['response']['msg']['line']
            print(f"\nError checking telemetry: {error_msg}")
            print("This could mean that the telemetry command is not supported on this firewall model or PAN-OS version.")
            return "Unknown"
        
        result = data.get('response', {}).get('result', {})
        
        if isinstance(result, str):
            print(f"\nUnexpected telemetry response: {result}")
            return "Unknown"
        
        telemetry_status = result.get('telemetry-status', 'Unknown')
        print(f"\nTelemetry status: {telemetry_status}")
        
        # Additional telemetry details
        print("\nAdditional telemetry details:")
        for key, value in result.items():
            if key != 'telemetry-status':
                print(f"{key}: {value}")
        
        return telemetry_status.lower() == 'on'
    except requests.exceptions.RequestException as e:
        print(f"Error checking telemetry: {e}")
        return "Unknown"

def check_firewall(firewall_ip, username, password):
    base_url = f"https://{firewall_ip}"
    
    # Get API key
    key_url = f"{base_url}/api/?type=keygen&user={username}&password={password}"
    try:
        response = requests.get(key_url, verify=False, timeout=10)
        response.raise_for_status()
        data = xmltodict.parse(response.text)
        api_key = data.get('response', {}).get('result', {}).get('key')
        if not api_key:
            print(f"Failed to obtain API key for {firewall_ip}")
            return
    except requests.exceptions.RequestException as e:
        print(f"Error connecting to {firewall_ip}: {e}")
        return
    
    print(f"\nChecking firewall: {firewall_ip}")
    
    # Check device certificates
    all_certs_valid = check_device_certificates(api_key, base_url)
    
    # Check telemetry status
    telemetry_status = check_telemetry_enabled(api_key, base_url)
    
    print(f"All certificates valid: {'Yes' if all_certs_valid else 'No'}")
    print(f"Telemetry status: {telemetry_status}")

def main():
    username = input("Enter your username: ")
    password = getpass.getpass("Enter your password: ")
    
    file_name = input("Enter the name of the file containing firewall IP addresses: ")
    
    try:
        with open(file_name, 'r') as file:
            firewall_ips = [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        print(f"Error: File '{file_name}' not found.")
        return
    except IOError:
        print(f"Error: Unable to read file '{file_name}'.")
        return
    
    if not firewall_ips:
        print("No valid IP addresses found in the file.")
        return
    
    for ip in firewall_ips:
        check_firewall(ip, username, password)

if __name__ == "__main__":
    main()