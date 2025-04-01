import requests
from bs4 import BeautifulSoup
import json
from urllib.parse import urljoin

# Base URL for Shodan domain lookup
BASE_URL = "https://www.shodan.io/domain/"

def fetch_page_content(url):
    """Fetch the HTML content of a given URL."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()  # Raise an error for HTTP failures
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching page: {e}")
        return None

def parse_dns_records(html):
    """Extracts DNS records and ports from the Shodan domain page."""
    soup = BeautifulSoup(html, "html.parser")
    
    dns_records = []
    table_rows = soup.select("div.nine.columns table tbody tr")
    
    for row in table_rows:
        cells = row.find_all("td")
        if len(cells) >= 3:
            subdomain = cells[0].text.strip()
            record_type = cells[1].text.strip()
            value = cells[2].text.strip()
            
            # Extract ports if available
            ports = []
            port_spans = cells[2].select(".ports .tag")
            for port in port_spans:
                ports.append(port.text.strip())

            # Remove extracted ports from value
            if ports:
                value = value.replace("".join([port.text.strip() for port in port_spans]), "").strip()

            record = {
                "subdomain": subdomain if subdomain else None,
                "type": record_type,
                "value": value,
                "ports": ports if ports else None  # Only add ports if present
            }
            dns_records.append(record)

    return dns_records

def parse_subdomains(html):
    """Extracts subdomains from the Shodan domain page."""
    soup = BeautifulSoup(html, "html.parser")
    
    subdomains = []
    subdomain_list = soup.select("#subdomains li")
    
    for item in subdomain_list:
        subdomains.append(item.text.strip())

    return subdomains

def save_data(domain, dns_records, subdomains):
    """Saves extracted data to a JSON file named after the domain."""
    data = {
        "domain": domain,
        "dns_records": dns_records,
        "subdomains": subdomains
    }
    
    filename = f"{domain.replace('.', '_')}.json"
    with open(filename, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)
    
    print(f"\nData saved to {filename}")

def main():
    """Main function to fetch, parse, and save domain data."""
    domain_name = input("Enter customer domain: ").strip()
    if not domain_name:
        print("Domain cannot be empty.")
        return
    
    full_url = urljoin(BASE_URL, domain_name)
    print(f"Fetching data from: {full_url}")
    
    html_content = fetch_page_content(full_url)
    if not html_content:
        print("Failed to retrieve page content.")
        return

    dns_records = parse_dns_records(html_content)
    subdomains = parse_subdomains(html_content)

    # Display extracted data
    print("\nExtracted DNS Records:")
    for record in dns_records:
        ports_display = f" Ports: {', '.join(record['ports'])}" if record['ports'] else ""
        print(f"{record['subdomain'] or '(root)'} ({record['type']}): {record['value']}{ports_display}")

    print("\nExtracted Subdomains:")
    print(", ".join(subdomains))

    # Save to file
    save_data(domain_name, dns_records, subdomains)

if __name__ == "__main__":
    main()
