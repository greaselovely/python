import re
import os
import argparse
from datetime import datetime
import ipaddress

def extract_ips(text):
    """
    Extract IPv4 and IPv6 addresses from the given text.

    Args:
    text (str): The input text to search for IP addresses.

    Returns:
    tuple: Two lists containing found IPv4 and IPv6 addresses respectively.
    """
    ipv4_pattern = r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)(?:\.(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)){3}'
    ipv6_pattern = r'(?:(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,7}:|(?:[0-9a-fA-F]{1,4}:){1,6}:[0-9a-fA-F]{1,4}|(?:[0-9a-fA-F]{1,4}:){1,5}(?::[0-9a-fA-F]{1,4}){1,2}|(?:[0-9a-fA-F]{1,4}:){1,4}(?::[0-9a-fA-F]{1,4}){1,3}|(?:[0-9a-fA-F]{1,4}:){1,3}(?::[0-9a-fA-F]{1,4}){1,4}|(?:[0-9a-fA-F]{1,4}:){1,2}(?::[0-9a-fA-F]{1,4}){1,5}|[0-9a-fA-F]{1,4}:(?:(?::[0-9a-fA-F]{1,4}){1,6})|:(?:(?::[0-9a-fA-F]{1,4}){1,7}|:)|fe80:(?::[0-9a-fA-F]{0,4}){0,4}%[0-9a-zA-Z]{1,}|::(?:ffff(?::0{1,4}){0,1}:){0,1}(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])|(?:[0-9a-fA-F]{1,4}:){1,4}:(?:(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9])\.){3,3}(?:25[0-5]|(?:2[0-4]|1{0,1}[0-9]){0,1}[0-9]))'
    
    ipv4_addresses = re.findall(ipv4_pattern, text)
    ipv6_addresses = re.findall(ipv6_pattern, text)
    
    return ipv4_addresses, ipv6_addresses

def sort_ip_addresses(ip_list):
    """
    Sort IP addresses and remove duplicates.

    Args:
    ip_list (list): A list of IP addresses as strings.

    Returns:
    list: A sorted list of unique IP addresses.
    """
    return sorted(set(ip_list), key=lambda ip: ipaddress.ip_address(ip))

def write_ips_to_file(ips, filename):
    """
    Write IP addresses to a file, one per line.

    Args:
    ips (list): A list of IP addresses to write.
    filename (str): The name of the file to write to.
    """
    with open(filename, 'w') as f:
        for ip in ips:
            f.write(f"{ip}\n")
    print(f"IPs saved to: {filename}")

def main():
    """
    Main function to process the input file and extract IP addresses.
    """
    parser = argparse.ArgumentParser(description="Extract IP addresses from a file.")
    parser.add_argument("-f", "--file", required=True, help="Input file name")
    args = parser.parse_args()

    input_file = args.file

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    ipv4_output = f"ipv4_addresses_{timestamp}.txt"
    ipv6_output = f"ipv6_addresses_{timestamp}.txt"

    try:
        with open(input_file, 'r') as f:
            text = f.read()

        ipv4_addresses, ipv6_addresses = extract_ips(text)

        sorted_ipv4 = sort_ip_addresses(ipv4_addresses)
        sorted_ipv6 = sort_ip_addresses(ipv6_addresses)
        if sorted_ipv4:
            write_ips_to_file(sorted_ipv4, ipv4_output)
        if sorted_ipv6:
            write_ips_to_file(sorted_ipv6, ipv6_output)

        print(f"\nFound {len(sorted_ipv4)} unique IPv4 addresses and {len(sorted_ipv6)} unique IPv6 addresses.")

    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()