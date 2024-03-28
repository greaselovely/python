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

def check_ssl_certificates(verbose: bool, demo: bool, count: int) -> None:
    """
    this is doing a few extra things aside from checking ssl certs, it probably 
    needs to be culled a little, but for now this checks to see if the domains.txt 
    file exists, if there is anything in it, or otherwise creates it under demo mode.
    Demo mode basically runs off to grab a large list of domains from github and 
    finds n number of domains, stores them in a list, and then writes them to the file also

    We make a call to get_certificate_info and display results of the cert, expiration date, 
    number of days until it expires, and the cert authority.

    This is very useful as a demonstration under ssl decryption to quickly show / validate 
    which cert is used to encrypt the session.

    Now, this point is important.  If ssl decryption is used, the cert in flight is modified to 
    to the ssl decryption trusted certificate, however, what isn't modified is the expiration, 
    so the expiration is the actual server certificate.
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
        try:
            expiration_date, ca = get_certificate_info(domain, verbose)
            days_remaining = expiration_date - datetime.datetime.now()
            print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\nExpiration Date: {expiration_date}\nDays Remaining: {days_remaining.days}\nCertificate Authority: {Fore.RED}{ca}{Fore.RESET}\n")
        except ssl.CertificateError as e:
            print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\nError: {Fore.RED}{e}{Fore.RESET}\n")
        except ssl.SSLError as e:
            print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\nError: {Fore.RED}{e}{Fore.RESET}\n")
        except socket.timeout as e:
            print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\nError: {Fore.RED}{e}{Fore.RESET}\n")
        except socket.error as e:
            print(f"Domain: {Fore.GREEN}{domain}{Fore.RESET}\nError: {Fore.RED}{e}{Fore.RESET}\n")



def get_certificate_info(domain: str, verbose: bool) -> tuple:
    """
    This is used to make a connection out to the requested domain, 
    captures the certificate info, expiration date and the CA.

    Returns a tuple.
    """
    ssl_date_fmt = r'%b %d %H:%M:%S %Y %Z'
    context = ssl.create_default_context()
    conn = context.wrap_socket(socket.socket(socket.AF_INET), server_hostname=domain)
    conn.settimeout(3.0)
    conn.connect((domain, 443))
    certificate = conn.getpeercert()
    expiration_date = datetime.datetime.strptime(certificate['notAfter'], ssl_date_fmt)
    ca = certificate['issuer'][-1][-1][-1]
    if verbose: print(certificate, end="\n" * 2)
    conn.close()
    return expiration_date, ca

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
