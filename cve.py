import re
from dataclasses import dataclass
from typing import Dict, List, Optional
import requests
from bs4 import BeautifulSoup

@dataclass
class PanVersion:
    major: int
    minor: int
    patch: int
    hotfix: int = 0

    @classmethod
    def from_string(cls, version_str: str) -> Optional['PanVersion']:
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-h(\d+))?$'
        match = re.match(pattern, version_str)
        if not match:
            return None
        
        return cls(
            major=int(match.group(1)),
            minor=int(match.group(2)),
            patch=int(match.group(3)),
            hotfix=int(match.group(4)) if match.group(4) else 0
        )

    def __lt__(self, other: 'PanVersion') -> bool:
        if self.major != other.major:
            return self.major < other.major
        if self.minor != other.minor:
            return self.minor < other.minor
        if self.patch != other.patch:
            return self.patch < other.patch
        return self.hotfix < other.hotfix

@dataclass
class CVE:
    id: str
    title: str
    cvss: float
    affected_versions: Dict[str, List[str]]

def parse_version_requirement(req_str: str) -> Optional[PanVersion]:
    match = re.match(r'^< (.+)$', req_str.strip())
    if not match:
        return None
    return PanVersion.from_string(match.group(1))

def is_vulnerable(current_version: PanVersion, requirements: List[str]) -> bool:
    for req in requirements:
        req_version = parse_version_requirement(req)
        if req_version and current_version < req_version:
            return True
    return False

def scrape_security_advisories() -> List[CVE]:
    url = "https://security.paloaltonetworks.com/?product=PAN-OS&product=PAN-OS+PA-Series+&product=PAN-OS+VM-Series&product=Panorama&sort=-date"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        cve_list = []
        for row in soup.find_all('tr'):
            # Find CVSS score
            cvss_tag = row.find('b', class_='tag CVSS')
            if not cvss_tag:
                continue

            cvss_text = cvss_tag.text.strip()
            if cvss_text == 'i':  # Skip informational entries
                continue
            
            cvss = float(cvss_text)
            
            # Get CVE ID and title
            link = row.find('a')
            if not link:
                continue
                
            cve_id = link.text.strip().split('\n')[0]
            title = link.text.strip().split('\n')[1] if len(link.text.strip().split('\n')) > 1 else ""
            
            # Parse affected versions
            affected_versions = {}
            version_cells = row.find_all('td', class_='zpad')
            if len(version_cells) >= 2:
                products = version_cells[0].find_all('div')
                versions = version_cells[1].find_all('div')
                
                for product, version in zip(products, versions):
                    product_text = product.text.strip()
                    if product_text.startswith('PAN-OS'):
                        version_text = version.text.strip()
                        if version_text != 'None':
                            major_minor = product_text.replace('PAN-OS ', '')
                            affected_versions[major_minor] = version_text.split(', ')
            
            if affected_versions:  # Only add if there are affected versions
                cve_list.append(CVE(
                    id=cve_id,
                    title=title,
                    cvss=cvss,
                    affected_versions=affected_versions
                ))
        breakpoint()
        return cve_list
        
    except requests.RequestException as e:
        print(f"Error fetching data: {e}")
        return []

def check_vulnerabilities(version_str: str, cve_database: List[CVE]) -> List[CVE]:
    current_version = PanVersion.from_string(version_str)
    if not current_version:
        raise ValueError(f"Invalid version format: {version_str}")

    vulnerable_to = []
    version_key = f"{current_version.major}.{current_version.minor}"

    for cve in cve_database:
        if version_key in cve.affected_versions:
            if is_vulnerable(current_version, cve.affected_versions[version_key]):
                vulnerable_to.append(cve)

    return vulnerable_to

def main():
    version = input("Enter your PAN-OS version (e.g., 10.1.6-h6): ")
    print("\nFetching security advisories...")
    
    cve_database = scrape_security_advisories()
    if not cve_database:
        print("Error: Could not fetch security advisories.")
        return

    try:
        vulnerabilities = check_vulnerabilities(version, cve_database)
        if vulnerabilities:
            print(f"\nPAN-OS version {version} is vulnerable to {len(vulnerabilities)} CVEs:")
            for cve in vulnerabilities:
                print(f"\nCVE ID: {cve.id}")
                print(f"Title: {cve.title}")
                print(f"CVSS Score: {cve.cvss}")
                print(f"Affected versions: {cve.affected_versions}")
        else:
            print(f"\nPAN-OS version {version} is not vulnerable to any known CVEs in the database.")
    
    except ValueError as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()