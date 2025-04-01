import re
import json
import argparse
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple
import requests
from datetime import datetime
import sys

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
    
    def __str__(self) -> str:
        if self.hotfix > 0:
            return f"{self.major}.{self.minor}.{self.patch}-h{self.hotfix}"
        return f"{self.major}.{self.minor}.{self.patch}"

@dataclass
class CVE:
    id: str
    title: str
    cvss: float
    severity: str
    affected_versions: Dict[str, List[str]]
    date_published: str
    url: str
    description: str = ""
    mitigation: str = ""

def parse_version_requirement(req_str: str) -> Tuple[str, Optional[PanVersion]]:
    """Parse version requirements like '< 10.1.6' or '< 10.2.0-h3'"""
    # Handle various formats
    req_str = req_str.strip()
    op = "<"
    
    if req_str.startswith("< "):
        version_str = req_str[2:].strip()
    elif req_str.startswith("<"):
        version_str = req_str[1:].strip()
    else:
        # For now, just assume it's a direct version without operator
        op = "="
        version_str = req_str
    
    version = PanVersion.from_string(version_str)
    return op, version

def is_vulnerable(current_version: PanVersion, requirements: List[str]) -> bool:
    """Check if the current version meets any of the vulnerability requirements."""
    for req in requirements:
        op, req_version = parse_version_requirement(req)
        if not req_version:
            continue
        
        if op == "<" and current_version < req_version:
            return True
        elif op == "=" and current_version == req_version:
            return True
        # Add other operators as needed
    
    return False

def fetch_security_advisories(limit: int = 100) -> List[CVE]:
    """Fetch security advisories directly from the JSON API."""
    url = "https://security.paloaltonetworks.com/json/"
    params = {
        "product": ["PAN-OS", "PAN-OS PA-Series", "PAN-OS VM-Series", "Panorama"],
        "sort": "-date",
        "limit": limit
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        
        cve_list = []
        for item in data.get('data', []):
            # Skip if not a CVE or no CVSS score
            if not item.get('cveId') or not item.get('cvssScore'):
                continue
            
            # Skip informational entries
            if item.get('cvssScore') == 'i':
                continue
            
            try:
                cvss = float(item.get('cvssScore', 0))
            except (ValueError, TypeError):
                cvss = 0.0
            
            # Map severity based on CVSS score
            severity = "Unknown"
            if cvss >= 9.0:
                severity = "Critical"
            elif cvss >= 7.0:
                severity = "High"
            elif cvss >= 4.0:
                severity = "Medium"
            elif cvss > 0:
                severity = "Low"
            
            # Parse affected versions
            affected_versions = {}
            for product in item.get('affectedProducts', []):
                product_name = product.get('name', '')
                if product_name.startswith('PAN-OS'):
                    major_minor = product_name.replace('PAN-OS ', '')
                    versions = product.get('versions', [])
                    if versions and versions != ['None']:
                        affected_versions[major_minor] = versions
            
            if affected_versions:  # Only add if there are affected versions
                cve = CVE(
                    id=item.get('cveId', ''),
                    title=item.get('title', ''),
                    cvss=cvss,
                    severity=severity,
                    affected_versions=affected_versions,
                    date_published=item.get('publishDate', ''),
                    url=f"https://security.paloaltonetworks.com/CVE_{item.get('cveId', '').replace('-', '_')}",
                    description=item.get('description', ''),
                    mitigation=item.get('recommendation', '')
                )
                cve_list.append(cve)
        
        return cve_list
        
    except requests.RequestException as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        return []
    except json.JSONDecodeError:
        print("Error parsing JSON response from server", file=sys.stderr)
        return []

def check_vulnerabilities(version_str: str, cve_database: List[CVE]) -> List[CVE]:
    """Check which CVEs the specified version is vulnerable to."""
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

def get_latest_versions(cve_database: List[CVE]) -> Dict[str, PanVersion]:
    """Extract the latest patch versions for each major.minor from CVEs."""
    latest_versions = {}
    
    # Extract all "fix" versions from CVEs
    for cve in cve_database:
        for major_minor, requirements in cve.affected_versions.items():
            for req in requirements:
                op, version = parse_version_requirement(req)
                if op == "<" and version:  # This is a "fixed in" version
                    current_latest = latest_versions.get(major_minor)
                    if not current_latest or version > current_latest:
                        latest_versions[major_minor] = version
    
    return latest_versions

def recommend_upgrade_path(current_version: PanVersion, latest_versions: Dict[str, PanVersion]) -> Optional[PanVersion]:
    """Recommend an upgrade path based on the current version."""
    current_key = f"{current_version.major}.{current_version.minor}"
    
    # First, check if there's a newer patch for the same major.minor
    if current_key in latest_versions and latest_versions[current_key] > current_version:
        return latest_versions[current_key]
    
    # Otherwise, suggest the latest available version
    latest_key = None
    latest_ver = None
    
    for key, version in latest_versions.items():
        major, minor = map(int, key.split('.'))
        if not latest_ver or major > latest_ver.major or (major == latest_ver.major and minor > latest_ver.minor):
            latest_key = key
            latest_ver = version
    
    return latest_ver

def export_to_csv(vulnerabilities: List[CVE], filename: str):
    """Export vulnerability findings to CSV."""
    import csv
    
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['CVE ID', 'CVSS', 'Severity', 'Date Published', 'Title', 'Description', 'Mitigation', 'URL'])
        
        for cve in vulnerabilities:
            writer.writerow([
                cve.id,
                cve.cvss,
                cve.severity,
                cve.date_published,
                cve.title,
                cve.description,
                cve.mitigation,
                cve.url
            ])

def main():
    parser = argparse.ArgumentParser(description='PAN-OS Vulnerability Checker')
    parser.add_argument('--version', '-v', help='PAN-OS version to check (e.g., 10.1.6-h6)')
    parser.add_argument('--export', '-e', help='Export results to CSV file')
    parser.add_argument('--limit', '-l', type=int, default=500, help='Limit the number of CVEs to fetch (default: 500)')
    parser.add_argument('--show-latest', action='store_true', help='Show latest available versions for each branch')
    args = parser.parse_args()
    
    version = args.version
    if not version and not args.show_latest:
        version = input("Enter your PAN-OS version (e.g., 10.1.6-h6): ")
    
    print("\nFetching security advisories...")
    cve_database = fetch_security_advisories(args.limit)
    
    if not cve_database:
        print("Error: Could not fetch security advisories.")
        return

    if args.show_latest:
        latest_versions = get_latest_versions(cve_database)
        print("\nLatest PAN-OS versions by branch (based on security advisories):")
        for branch, version in sorted(latest_versions.items()):
            print(f"PAN-OS {branch}: {version}")
        print("\nNote: These are the latest versions mentioned in security advisories and may not be the absolute latest released versions.")
    
    if version:
        try:
            current_version = PanVersion.from_string(version)
            if not current_version:
                print(f"Error: Invalid version format: {version}")
                return
                
            vulnerabilities = check_vulnerabilities(version, cve_database)
            
            # Group vulnerabilities by severity
            severity_groups = {
                "Critical": [],
                "High": [],
                "Medium": [],
                "Low": [],
                "Unknown": []
            }
            
            for cve in vulnerabilities:
                severity_groups[cve.severity].append(cve)
            
            # Print summary
            print(f"\nPAN-OS version {version} analysis:")
            print(f"Total vulnerabilities: {len(vulnerabilities)}")
            for severity, cves in severity_groups.items():
                print(f"{severity}: {len(cves)}")
            
            # Print details
            if vulnerabilities:
                print("\nVulnerability details:")
                for severity in ["Critical", "High", "Medium", "Low", "Unknown"]:
                    for cve in severity_groups[severity]:
                        print(f"\n[{cve.severity}] {cve.id} (CVSS: {cve.cvss})")
                        print(f"Title: {cve.title}")
                        print(f"Date: {cve.date_published}")
                        print(f"URL: {cve.url}")
                
                # Recommend upgrade
                latest_versions = get_latest_versions(cve_database)
                recommended = recommend_upgrade_path(current_version, latest_versions)
                
                if recommended:
                    print(f"\nRecommended upgrade: {recommended}")
                    
                # Export to CSV if requested
                if args.export:
                    export_to_csv(vulnerabilities, args.export)
                    print(f"\nExported {len(vulnerabilities)} vulnerabilities to {args.export}")
            else:
                print(f"\nPAN-OS version {version} is not vulnerable to any known CVEs in the database.")
        
        except ValueError as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()