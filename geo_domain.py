import pathlib
import requests
import json
import pandas as pd
import random
import os
import dns.resolver
import tabulate
from requests.packages.urllib3.exceptions import InsecureRequestWarning

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

"""
to do
if the first line of the table has no ip resolution, the order of the table is not maintained
it doesn't show the domain and ip first.
"""


"""
With this you can resolve names on domains_list and we'll only return the first IP and provide geo-location.
Uses ip-api.com which is a Free for non-commercial use, no API key required.
if you don't have domains.txt in this parent dir, with your own list, we'll generate one for you.  Why?  Cuz.
"""

domains_list = []
ip_api_query = []
domains_file = "domains.txt"
opendns_file = 'opendns.txt'

lpath = pathlib.Path(__file__).parent
opendns = os.path.join(lpath, opendns_file)
domains = os.path.join(lpath, domains_file)

def clear():
    """
    Clears the screen.
    """
    os.system("cls" if os.name == "nt" else "clear")

def open_file():
    """
    attempt to open the domains.txt file and populate the domains_list.
    If the file doesn't exist, we just return out
    """
    global domains_list
    try:
        if os.path.getsize(domains) > 0:
            with open(domains, 'r') as f:
                domains_list = f.read().splitlines()    # create a list from existing file 
    except FileNotFoundError:
        return
    
def write_file():
    """
    Since the domains.txt file was empty / didn't exist
    we take the domain_gen results and save it to domains.txt
    """
    with open(domains, 'w') as f:
        for domain in domains_list:
            f.write(domain + '\n')

def collect_ips():
    """
    Using dnspython, we do a DNS lookup for each name in the 
    domain list, and capture the first returned IP, even if there are multiple or just one.
    Build a dictionary to be used for geo-location purposes as data input to requests.
    """
    if len(domains_list) == 0: domain_gen()  # create a list of domains_list
    for domain in domains_list:
        try:
            result = dns.resolver.resolve(domain, 'A')
            ip = result[0].to_text()
        except dns.resolver.NoAnswer:
            ip = "0.0.0.0"
        except dns.resolver.NoNameservers:
            ip = "0.0.0.0"
        except dns.resolver.LifetimeTimeout:
            ip = "0.0.0.0"
        except dns.resolver.NXDOMAIN:
            ip = "0.0.0.0"
        if not ip: ip = "0.0.0.0"   # If all of the above fail, and there is no IP returned, we are just creating a catch all with 0's
        ip_api_query.append({ "query" : f"{ip}", "fields" : "country,regionName,city,timezone,query"})

def domain_gen():
    """
    There's a 10K line domain list on github from opendns, 
    so we just go grab it and grab 10 random domains_list from it
    and append it to the domains_list list.  To avoid using this, 
    create the domains.txt file, and enter a list of domains in it.
    """
    if os.path.isfile(opendns) and os.path.getsize(opendns) > 0:
        domains_list_from_opendns = open(opendns, 'r').read()
    else:
        url = "https://raw.githubusercontent.com/opendns/public-domain-lists/master/opendns-random-domains.txt"
        domains_list_from_opendns = requests.get(url, verify=False).text
        with open(opendns, 'w') as f:
            f.write(domains_list_from_opendns)
    
    domains_list_from_opendns = domains_list_from_opendns.split()

    i = 0
    while i < 10:
        random_domain = random.choice(domains_list_from_opendns)
        domains_list.append(random_domain)
        i += 1
    write_file()

def get_geo():
    """
    The ip_api_query isn't formatted correctly to send as data in the requests, so we convert it and 
    set geo_data as global and capture the output from the API post, and convert
    it to JSON as opposed to just receiving it as a str.
    """
    ip_api_url = "http://ip-api.com/batch"
    api_query = json.dumps(ip_api_query) # convert to proper data structure for json data in url   
    global geo_data
    geo_data = requests.post(ip_api_url, data=api_query).json()

def update_geo_data():
    """
    We send (and receive) only the fields we want to the geo API, 
    but it doesn't include the domain name as part of the API query,
    so to make the print easier, we add domain to each dict.
    """
    for i, g in enumerate(geo_data):
        g["domain"] = domains_list[i]
    

def print_geo_data():
    """
    Convert geo_data (a dict) to a DataFrame (df), re-order columns, set index of the DataFrame, rename columns for aesthetics, and print that sh*t

    Original columns are: 
       0           1       2       3       4       5
    country, regionName, city, timezone, query, domain

    We re-order like this for a better display:
    city, regionName, country, timezone, query, domain

    thus when we print the DataFrame it will look like this:
    domain, query, city, regionName, country, timezone
    
    We then rename the column headers to:
    Domain, IP Address, City, Region/State, Country, Time Zone

    """
    df = pd.DataFrame.from_dict(geo_data)
    df = df.fillna('-')
    cols = df.columns.tolist()
    cols = [cols[5], cols[4], cols[2], cols[1], cols[0], cols[3]]   # re-order the columns for display
    # print(cols)
    df = df[cols]
    df = df.rename(columns={'domain': 'Domain', 'query': 'IP Address', 'city': 'City', 'regionName': 'Region/State', 'country': 'Country', 'timezone' : 'Time Zone'})
    print(tabulate.tabulate(df, showindex=False, headers=df))
    


def main():
    clear()
    open_file()
    collect_ips()
    get_geo()
    update_geo_data()
    print_geo_data()

    with open(domains, 'w') as f:
        pass

if __name__ == '__main__':
    main()
