#!/usr/bin/env python3
import dns.resolver
import socket
import requests
import random
import time
import statistics
import concurrent.futures
from typing import List, Dict, Set
from dataclasses import dataclass
import platform
import subprocess
import re
import os
import json
from datetime import datetime, timedelta

@dataclass
class DNSResult:
    domain: str
    nameserver: str
    resolution_time: float
    success: bool
    error: str = None

class DomainListManager:
    def __init__(self, source_url: str, known_good_file: str = "known_good_domains.json", target_size: int = 500):
        self.source_url = source_url
        self.known_good_file = known_good_file
        self.target_size = target_size
        self.cache_max_age = timedelta(hours=8)

    def load_or_create_verified_list(self, nameservers: List[str], workers: int = 10) -> List[str]:
        """Load or create list of verified domains, maintaining target size"""
        known_good = self._load_known_good()
        
        if len(known_good) >= self.target_size and not self._should_refresh_cache():
            print(f"Using {len(known_good)} domains from known good list")
            return known_good
        
        print(f"Current known good domains: {len(known_good)}")
        needed_domains = self.target_size - len(known_good)
        
        if needed_domains > 0:
            print(f"Need {needed_domains} more domains to reach target of {self.target_size}")
            new_domains = self._fetch_and_verify_domains(nameservers, needed_domains, workers)
            
            # Combine existing known good with new verified domains
            all_domains = list(set(known_good + new_domains))
            self._save_known_good(all_domains)
            print(f"Updated known good list now contains {len(all_domains)} domains")
            return all_domains
            
        return known_good

    def _should_refresh_cache(self) -> bool:
        """Check if cache needs refreshing"""
        if not os.path.exists(self.known_good_file):
            return True
        
        try:
            with open(self.known_good_file, 'r') as f:
                cache_data = json.load(f)
                last_update = datetime.fromisoformat(cache_data['last_update'])
                return datetime.now() - last_update > self.cache_max_age
        except Exception as e:
            print(f"Cache read error: {e}")
            return True

    def _fetch_and_verify_domains(self, nameservers: List[str], needed_domains: int, workers: int) -> List[str]:
        """Fetch and verify new domains until we have enough"""
        source_domains = self._fetch_source_domains()
        random.shuffle(source_domains)  # Randomize to avoid testing same domains each time
        
        valid_domains = []
        batch_size = min(needed_domains * 2, len(source_domains))  # Test more than needed as some will fail
        
        print(f"Testing {batch_size} domains to find {needed_domains} valid ones...")
        domains_to_test = source_domains[:batch_size]
        
        def verify_domain_all_ns(domain: str) -> tuple[str, bool]:
            return domain, any(self._check_domain(domain, ns) for ns in nameservers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(verify_domain_all_ns, domain): domain 
                      for domain in domains_to_test}
            completed = 0

            for future in concurrent.futures.as_completed(futures):
                completed += 1
                if completed % 100 == 0:
                    print(f"Progress: {completed}/{batch_size} domains...", end='\r')

                domain, is_valid = future.result()
                if is_valid:
                    valid_domains.append(domain)
                    if len(valid_domains) >= needed_domains:
                        break

        print(f"\nFound {len(valid_domains)} new valid domains")
        return valid_domains

    def _load_known_good(self) -> List[str]:
        """Load known good domains from cache file"""
        try:
            with open(self.known_good_file, 'r') as f:
                cache_data = json.load(f)
                domains = cache_data['domains']
                print(f"Loaded {len(domains)} domains from known good list")
                return domains
        except Exception as e:
            print(f"No existing known good list found or error loading: {e}")
            return []

    def _save_known_good(self, domains: List[str]):
        """Save known good domains to cache file"""
        cache_data = {
            'last_update': datetime.now().isoformat(),
            'domains': domains
        }
        with open(self.known_good_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"Saved {len(domains)} domains to known good list")

    def _verify_domains(self, domains: List[str], nameservers: List[str], workers: int) -> List[str]:
        """Verify domains against nameservers"""
        valid_domains = set()
        total = len(domains)
        print(f"Verifying {total} domains...")

        def verify_domain_all_ns(domain: str) -> tuple[str, bool]:
            return domain, any(self._check_domain(domain, ns) for ns in nameservers)

        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(verify_domain_all_ns, domain): domain 
                      for domain in domains}
            completed = 0

            for future in concurrent.futures.as_completed(futures):
                completed += 1
                if completed % 100 == 0:
                    print(f"Progress: {completed}/{total} domains...", end='\r')

                domain, is_valid = future.result()
                if is_valid:
                    valid_domains.add(domain)

        print(f"\nFound {len(valid_domains)} valid domains")
        return list(valid_domains)

    def _check_domain(self, domain: str, nameserver: str) -> bool:
        """Check if a domain resolves"""
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [nameserver]
        resolver.timeout = 2
        resolver.lifetime = 2
        
        try:
            resolver.resolve(domain, 'A')
            return True
        except Exception:
            return False

    def _save_verified_domains(self, domains: List[str]):
        """Save verified domains to cache file"""
        cache_data = {
            'last_update': datetime.now().isoformat(),
            'domains': domains
        }
        with open(self.cache_file, 'w') as f:
            json.dump(cache_data, f, indent=2)
        print(f"Saved {len(domains)} verified domains to {self.cache_file}")

    def _load_cached_domains(self) -> List[str]:
        """Load domains from cache file"""
        try:
            with open(self.cache_file, 'r') as f:
                cache_data = json.load(f)
                domains = cache_data['domains']
                print(f"Loaded {len(domains)} domains from cache")
                return domains
        except Exception as e:
            print(f"Error loading cache: {e}")
            return []

    def _fetch_source_domains(self) -> List[str]:
        """Fetch domains from source URL"""
        try:
            response = requests.get(self.source_url)
            response.raise_for_status()
            return [line.strip() for line in response.text.split('\n') if line.strip()]
        except requests.RequestException as e:
            print(f"Error fetching domain list: {e}")
            return self._get_fallback_domains()
    
    def _get_fallback_domains(self) -> List[str]:
        """Return a list of reliable domains in case source URL fails"""
        return [
            "google.com", "facebook.com", "amazon.com", "microsoft.com",
            "apple.com", "netflix.com", "youtube.com", "instagram.com",
            "twitter.com", "linkedin.com", "github.com", "reddit.com",
            "wikipedia.org", "cloudflare.com", "adobe.com", "twitch.tv",
            "spotify.com", "slack.com", "zoom.us", "office.com"
        ]

def get_nameservers_linux() -> List[str]:
    """Get DNS servers from /etc/resolv.conf"""
    nameservers = []
    try:
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                if line.startswith('nameserver'):
                    nameserver = line.split()[1].strip()
                    nameservers.append(nameserver)
    except Exception as e:
        print(f"Error reading resolv.conf: {e}")
    return nameservers

def get_nameservers_windows() -> List[str]:
    """Get DNS servers using ipconfig /all command"""
    nameservers = []
    try:
        output = subprocess.check_output(['ipconfig', '/all'], text=True)
        for line in output.split('\n'):
            if 'DNS Servers' in line:
                ip_match = re.search(r'\d+\.\d+\.\d+\.\d+', line)
                if ip_match:
                    nameservers.append(ip_match.group())
    except Exception as e:
        print(f"Error getting Windows DNS servers: {e}")
    return nameservers

def get_nameservers_mac() -> List[str]:
    """Get DNS servers using scutil --dns command"""
    nameservers = []
    try:
        output = subprocess.check_output(['scutil', '--dns'], text=True)
        for line in output.split('\n'):
            if 'nameserver[' in line:
                ip_match = re.search(r'\d+\.\d+\.\d+\.\d+', line)
                if ip_match:
                    nameservers.append(ip_match.group())
    except Exception as e:
        print(f"Error getting macOS DNS servers: {e}")
    return nameservers

def get_system_nameservers() -> List[str]:
    """Get DNS servers from system and include Apple's masked DNS"""
    nameservers = []
    
    # Get system nameservers
    system = platform.system().lower()
    if system == 'linux':
        nameservers.extend(get_nameservers_linux())
    elif system == 'windows':
        nameservers.extend(get_nameservers_windows())
    elif system == 'darwin':
        nameservers.extend(get_nameservers_mac())
    else:
        print(f"Unsupported operating system: {system}")
    
    # Add Apple's masked DNS server
    try:
        apple_dns = socket.gethostbyname('mask.apple-dns.net')
        if apple_dns not in nameservers:
            nameservers.append(apple_dns)
            print(f"Added Apple's masked DNS: {apple_dns}")
    except socket.gaierror as e:
        print(f"Could not resolve Apple's masked DNS: {e}")
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(nameservers))

def resolve_domain_with_nameserver(domain: str, nameserver: str) -> DNSResult:
    """Resolve a domain using a specific nameserver"""
    resolver = dns.resolver.Resolver()
    resolver.nameservers = [nameserver]
    # Use 5 second timeout for all servers for consistency
    resolver.timeout = 5.0  # 5 second timeout
    resolver.lifetime = 5.0  # 5 second total query lifetime
    
    start_time = time.time()
    try:
        resolver.resolve(domain, 'A')
        resolution_time = time.time() - start_time
        return DNSResult(domain=domain, nameserver=nameserver, 
                        resolution_time=resolution_time, success=True)
    except Exception as e:
        resolution_time = time.time() - start_time
        return DNSResult(domain=domain, nameserver=nameserver,
                        resolution_time=resolution_time, success=False, error=str(e))

def test_dns_resolution(domains: List[str], nameservers: List[str], 
                       workers: int = 10) -> List[DNSResult]:
    """Test DNS resolution for each domain against each nameserver"""
    results = []
    total_tests = len(domains) * len(nameservers)
    completed = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_params = {
            executor.submit(resolve_domain_with_nameserver, domain, nameserver): 
            (domain, nameserver)
            for domain in domains
            for nameserver in nameservers
        }
        
        for future in concurrent.futures.as_completed(future_to_params):
            completed += 1
            if completed % 10 == 0:
                print(f"Completed {completed}/{total_tests} tests...", end='\r')
            results.append(future.result())
    
    print(f"\nCompleted all {total_tests} tests")
    return results

def print_nameserver_statistics(results: List[DNSResult]):
    """Print statistics grouped by nameserver"""
    nameserver_results = {}
    for result in results:
        if result.nameserver not in nameserver_results:
            nameserver_results[result.nameserver] = []
        nameserver_results[result.nameserver].append(result)
    
    for nameserver, ns_results in nameserver_results.items():
        successful_times = [r.resolution_time for r in ns_results if r.success]
        failed_times = [r.resolution_time for r in ns_results if not r.success]
        
        print(f"\nNameserver: {nameserver}")
        print("-" * 50)
        print(f"Total queries: {len(ns_results)}")
        print(f"Successful: {len(successful_times)}")
        print(f"Failed: {len(failed_times)}")
        
        if successful_times:
            print("\nResolution Times (seconds):")
            print(f"  Average: {statistics.mean(successful_times):.4f}")
            print(f"  Median:  {statistics.median(successful_times):.4f}")
            print(f"  Min:     {min(successful_times):.4f}")
            print(f"  Max:     {max(successful_times):.4f}")
            if len(successful_times) > 1:
                print(f"  StdDev:  {statistics.stdev(successful_times):.4f}")
        
        if failed_times:
            print("\nFailed Resolutions (showing first 5):")
            failed_results = [r for r in ns_results if not r.success]
            for result in failed_results[:5]:
                print(f"  {result.domain}: {result.error}")
            if len(failed_results) > 5:
                print(f"  ... and {len(failed_results) - 5} more failures")
        
        print("\nTop 5 Slowest Successful Resolutions:")
        successful_results = [r for r in ns_results if r.success]
        sorted_results = sorted(successful_results, 
                              key=lambda x: x.resolution_time, reverse=True)
        for result in sorted_results[:5]:
            print(f"  {result.domain}: {result.resolution_time:.4f}s")

def main():
    print("DNS Resolution Time Tester")
    print("=" * 50)
    
    # Get system DNS servers
    nameservers = get_system_nameservers()
    if not nameservers:
        print("No DNS servers found. Please check your network configuration.")
        return
    
    print("Detected DNS servers:")
    for ns in nameservers:
        print(f"  - {ns}")
    
    # Initialize domain list manager with target size of 500 domains
    source_url = "https://raw.githubusercontent.com/fgont/domain-list/refs/heads/master/umbrella-domains.txt"
    manager = DomainListManager(source_url, target_size=500)
    
    # Get verified domains (from known good list or create new entries as needed)
    verified_domains = manager.load_or_create_verified_list(nameservers)
    
    if not verified_domains:
        print("No valid domains found. Please check your internet connection or domain list.")
        return
    
    # Get random sample for this test run
    num_test_domains = min(100, len(verified_domains))
    test_domains = random.sample(verified_domains, num_test_domains)
    print(f"\nTesting {len(test_domains)} random domains from known good list...")
    
    # Run tests
    results = test_dns_resolution(test_domains, nameservers)
    
    # Print results
    print_nameserver_statistics(results)

if __name__ == "__main__":
    main()