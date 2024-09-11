import ssl
import socket
import datetime
import warnings
import requests
import pathlib
import os
import random
import argparse
import xmltodict
import json
from getpass import getpass
from sys import argv
from colorama import Fore, init
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from cryptography import x509
from cryptography.hazmat.backends import default_backend
from cryptography.utils import CryptographyDeprecationWarning

# Initialize colorama
init(autoreset=True)

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
warnings.filterwarnings("ignore", category=CryptographyDeprecationWarning)

domain_file = 'domains.txt'
opendns_file = 'opendns.txt'
inventory_file = 'inventory.json'
lpath = pathlib.Path(__file__).parent
domains = os.path.join(lpath, domain_file)
opendns = os.path.join(lpath, opendns_file)
domain_list = []
firewall_info = None

def clear():
    """
    Clears the screen.
    """
    os.system("cls" if os.name == "nt" else "clear")

def argue_with_me():
    """
    This is called if there are arguments passed to the script via cli.
    """
    parser = argparse.ArgumentParser(description='Domain SSL Certificate Checking, showing CA and expiration')
    parser.add_argument('-d', '--demo', action='store_true', help='Generates a list of random domain names to show you results of those', required=False)
    parser.add_argument('-c', '--count', type=int, help='Specify number of demo domains to generate, maximum of 10', required=False, default=5)
    parser.add_argument('-v', '--verbose', action='store_true', help='Provides detail output of the entire certificate', required=False)
    parser.add_argument('-s', '--setup', action='store_true', help='Setup or update firewall information to query URLs', required=False)
    args = parser.parse_args()
    return args

def setup_firewall():
    """
    Setup or update firewall information.
    """
    hostname = input("Enter firewall hostname: ")
    hostname = hostname.upper()
    ip_address = input("Enter firewall IP address: ")
    username = input("Enter username: ")
    password = getpass("Enter password: ")

    # Get API key
    api_url = f"https://{ip_address}/api/?type=keygen&user={username}&password={password}"
    try:
        response = requests.get(api_url, verify=False, timeout=10)
        response.raise_for_status()
        xml_dict = xmltodict.parse(response.text)
        api_key = xml_dict['response']['result']['key']
    except Exception as e:
        print(f"Failed to get API key: {e}")
        return

    # Test the API key
    if not test_api_key(ip_address, api_key):
        print("Failed to validate the API key. Firewall information not saved.")
        return

    # Prepare new firewall data
    new_firewall_data = {
        "hostname": hostname,
        "ip_address": ip_address,
        "api_key": api_key
    }

    # Load existing inventory or create new if doesn't exist
    if os.path.exists(inventory_file):
        with open(inventory_file, 'r') as f:
            inventory = json.load(f)
    else:
        inventory = {}

    # Update existing entry or add new one
    inventory[hostname] = new_firewall_data

    # Use json.dumps() to save the updated inventory
    with open(inventory_file, 'w') as f:
        json_string = json.dumps(inventory, indent=2)
        f.write(json_string)

    clear()

def test_api_key(ip_address, api_key):
    """
    Test if the API key is valid by making a simple API call.
    """
    test_url = f"https://{ip_address}/api/?type=op&cmd=<show><system><info></info></system></show>&key={api_key}"
    try:
        response = requests.get(test_url, verify=False, timeout=10)
        response.raise_for_status()
        xml_dict = xmltodict.parse(response.text)
        if xml_dict['response']['@status'] == 'success':
            return True
    except Exception:
        pass
    return False

def load_firewall_info():
    """
    Load firewall information from inventory.json and test API keys.
    Prioritizes the most recently added firewall.
    """
    global firewall_info
    if os.path.exists(inventory_file):
        with open(inventory_file, 'r') as f:
            inventory = json.load(f)
        
        if not inventory:
            return False

        # Get the most recently added firewall (last item in the dictionary)
        latest_hostname = list(inventory.keys())[-1]
        latest_fw = inventory[latest_hostname]

        if test_api_key(latest_fw['ip_address'], latest_fw['api_key']):
            firewall_info = latest_fw
            return True

        # If the latest firewall fails, try others
        for hostname, fw_data in inventory.items():
            if hostname != latest_hostname:  # Skip the one we already tried
                if test_api_key(fw_data['ip_address'], fw_data['api_key']):
                    firewall_info = fw_data
                    return True
    
    return False

def tcp_port_responding(domain: str, port: int = 443, timeout: int = 3) -> bool:
    """
    Checks if the specified TCP port is responding.
    """
    try:
        with socket.create_connection((domain, port), timeout):
            return True
    except (socket.timeout, socket.error):
        return False

def get_url_category(url):
    """
    Queries the connected firewall for URL category and risk.
    """
    if firewall_info:
        try:
            api_url = f"https://{firewall_info['ip_address']}/api/?type=op&cmd=<test><url>{url}</url></test>&key={firewall_info['api_key']}"
            response = requests.get(api_url, verify=False, timeout=10)
            response.raise_for_status()
            
            # Parse XML response using xmltodict
            xml_dict = xmltodict.parse(response.text)
            
            # Extract result from the parsed dictionary
            result = xml_dict.get('response', {}).get('result')
            
            if result:
                # Split the result string
                parts = result.split()
                
                # Find the index of the domain name
                domain_index = parts.index(url.split('://')[1]) if '://' in url else parts.index(url)
                
                # Extract category and risk
                category_risk = ' '.join(parts[domain_index + 1:])
                category_risk_parts = category_risk.split()
                
                # Initialize category and risk
                category = "Unknown"
                risk = "Unknown"
                
                # Extract category (which may contain hyphens)
                for i, part in enumerate(category_risk_parts):
                    if part.lower() in ['low-risk', 'medium-risk', 'high-risk', 'unknown']:
                        category = ' '.join(category_risk_parts[:i])
                        risk = part
                        break
                
                return category, risk
            else:
                print(f"No result found in the response for {url}")
        except requests.RequestException as e:
            print(f"Request error for {url}: {e}")
        except xmltodict.expat.ExpatError as e:
            print(f"XML parsing error for {url}: {e}")
        except Exception as e:
            print(f"Failed to get URL category for {url}: {e}")
    return None, None

def get_certificate_info(domain: str, verbose: bool) -> tuple:
    """
    This is used to make a connection out to the requested domain,
    captures the certificate info, expiration date and the CA.
    
    Returns a tuple.
    """
    context = ssl.create_default_context()
    context.options |= ssl.OP_LEGACY_SERVER_CONNECT  # Enable legacy renegotiation
    context.check_hostname = False
    context.verify_mode = ssl.CERT_NONE
    conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=domain)
    conn.settimeout(3.0)
    
    try:
        conn.connect((domain, 443))
        der_cert = conn.getpeercert(True)
        pem_cert = ssl.DER_cert_to_PEM_cert(der_cert)
        
        # Load the certificate using cryptography
        cert = x509.load_pem_x509_certificate(pem_cert.encode(), default_backend())
        
        expiration_date = cert.not_valid_after
        issuer = cert.issuer.rfc4514_string()

        if verbose:
            print("Certificate:", cert)
            print("Expiration date:", expiration_date)
            print("Issuer:", issuer)
        
    except (ssl.SSLError, ssl.CertificateError, ssl.SSLCertVerificationError) as ssl_error:
        print(f"SSL error occurred: {ssl_error}")
        return None, None
    except socket.error as socket_error:
        print(f"Socket error occurred: {socket_error}")
        return None, None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None, None
    finally:
        conn.close()
    
    return expiration_date, issuer

def domain_gen(count: int) -> None:
    """
    Used to create a domain list for demonstration purposes.

    Checks to see if the random domain list exists, if not
    downloads it.

    Then takes n number of domains and puts them in the list and 
    also writes them to the domains.txt file for use a second time
    (don't use demo mode if you want to retain the file)
    """
    global domain_list

    if os.path.isfile(opendns):
        with open(opendns, 'r') as od:
            domains_from_opendns = od.read()
    else:
        url = "https://raw.githubusercontent.com/opendns/public-domain-lists/master/opendns-top-domains.txt"
        domains_from_opendns = requests.get(url, verify=False).text
        with open(opendns, 'w') as f:
            f.write(domains_from_opendns)
    
    domains_from_opendns = domains_from_opendns.split()
    
    domain_list = random.sample(domains_from_opendns, count)
    
    with open(domains, 'w') as d:
        for domain in domain_list:
            d.write(domain + '\n')

def check_ssl_certificates(verbose: bool, demo: bool, count: int) -> None:
    """
    This function checks SSL certificates of domains.
    """
    global domain_list
    if not os.path.isfile(domains):
        domain_gen(count)
    elif os.path.getsize(domains) > 0:
        with open(domains, 'r') as f:
            domain_list = f.read().splitlines()
    else:
        if len(domain_list) == 0:
            print(f"\n\n[i]\tDomain list is empty, creating...\n\n")
            demo = True

    if demo: domain_gen(count)

    firewall_connected = load_firewall_info()

    for domain in domain_list:
        domain = domain.strip() # CYA cleanup
        if tcp_port_responding(domain):
            try:
                expiration_date, ca = get_certificate_info(domain, verbose)
                if expiration_date and ca:
                    days_remaining = (expiration_date - datetime.datetime.now()).days
                    print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}")
                    print(f"Expiration Date: {expiration_date}")
                    print(f"Days Remaining: {days_remaining}")
                    print(f"Certificate Authority: {Fore.RED}{ca}{Fore.RESET}")
                    
                    if firewall_connected:
                        category, risk = get_url_category(domain)
                        if category and risk:
                            print(f"Category: {Fore.YELLOW}{category}{Fore.RESET}")
                            print(f"Risk: {Fore.YELLOW}{risk}{Fore.RESET}")
                    
                    print()
                else:
                    print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}")
                    print(f"{Fore.RED}Failed to retrieve certificate information.{Fore.RESET}\n")
            except ssl.CertificateError as e:
                print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}")
                print(f"Error: {Fore.RED}{e}{Fore.RESET}\n")
            except ssl.SSLError as e:
                print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}")
                print(f"Error: {Fore.RED}{e}{Fore.RESET}\n")
            except socket.timeout as e:
                print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}")
                print(f"Error: {Fore.RED}{e}{Fore.RESET}\n")
            except socket.error as e:
                print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}")
                print(f"Error: {Fore.RED}{e}{Fore.RESET}\n")
        else:
            print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}")
            print(f"{Fore.RED}The website is not responding on TCP/443.{Fore.RESET}\n")

def main():
    clear()
    args = argue_with_me()
    
    if args.setup:
        setup_firewall()
    
    if load_firewall_info():
        check_ssl_certificates(args.verbose, args.demo, args.count)


if __name__ == '__main__':
    main()