import ssl
import socket
import datetime
import requests
import pathlib
import os
import random
import argparse
from sys import argv
from colorama import Fore
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from cryptography import x509
from cryptography.hazmat.backends import default_backend

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

domain_file = 'domains.txt'
opendns_file = 'opendns.txt'
lpath = pathlib.Path(__file__).parent
domains = os.path.join(lpath, domain_file)
opendns = os.path.join(lpath, opendns_file)
domain_list = []

def clear():
    """
    Clears the screen.
    """
    os.system("cls" if os.name == "nt" else "clear")

def argue_with_me():
    """
    This is called if there are arguments passed to the script via cli,
    and assigns and stores boolean if you want us to run in demo mode. 
    Otherwise, populate domains.txt
    """
    parser = argparse.ArgumentParser(description='Domain SSL Certificate Checking, showing CA and expiration')
    parser.add_argument('-d', '--demo', action='store_true', help='Generates a list of random domain names to show you results of those', required=False)
    parser.add_argument('-c', '--count', type=int, help='Specify number of demo domains to generate, maximum of 10', required=True)
    parser.add_argument('-v', '--verbose', action='store_true', help='Provides detail output of the entire certificate', required=False)
    args = parser.parse_args()
    verbose = args.verbose
    demo = args.demo
    count = args.count
    return verbose, demo, count

def tcp_port_responding(domain: str, port: int = 443, timeout: int = 3) -> bool:
    """
    Checks if the specified TCP port is responding.
    """
    try:
        with socket.create_connection((domain, port), timeout):
            return True
    except (socket.timeout, socket.error):
        return False

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

    for domain in domain_list:
        domain = domain.strip() # CYA cleanup
        if tcp_port_responding(domain):
            try:
                expiration_date, ca = get_certificate_info(domain, verbose)
                if expiration_date and ca:
                    days_remaining = (expiration_date - datetime.datetime.now()).days
                    print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\nExpiration Date: {expiration_date}\nDays Remaining: {days_remaining}\nCertificate Authority: {Fore.RED}{ca}{Fore.RESET}\n")
                else:
                    print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\n{Fore.RED}Failed to retrieve certificate information.{Fore.RESET}\n")
            except ssl.CertificateError as e:
                print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\nError: {Fore.RED}{e}{Fore.RESET}\n")
            except ssl.SSLError as e:
                print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\nError: {Fore.RED}{e}{Fore.RESET}\n")
            except socket.timeout as e:
                print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\nError: {Fore.RED}{e}{Fore.RESET}\n")
            except socket.error as e:
                print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\nError: {Fore.RED}{e}{Fore.RESET}\n")
        else:
            print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\n{Fore.RED}The website is not responding on port 443. Please check the server or network settings.{Fore.RESET}\n")

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
        domains_from_opendns = requests.get(url, verify='/Users/ssivley/Downloads/cert_trust-decrypt.crt').text
        with open(opendns, 'w') as f:
            f.write(domains_from_opendns)
    
    domains_from_opendns = domains_from_opendns.split()
    
    domain_list = random.sample(domains_from_opendns, count)
    
    with open(domains, 'w') as d:
        for domain in domain_list:
            d.write(domain + '\n')

def main():
    # clear()
    
    if len(argv) == 1:
        verbose, demo, count = False, False, 5
        check_ssl_certificates(verbose, demo, count)
    else:
        verbose, demo, count = argue_with_me()
        if demo: open(domains, 'w').close() # overwrite / clear the file
        check_ssl_certificates(verbose, demo, count)

if __name__ == '__main__':
    main()
