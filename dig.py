import subprocess, json, requests

"""
ok, so you wanna do a quick dig on domains and only retrieve the first IP.  Cool.
Linux / Mac only unless you have dig on Windows

and you wanna geo-locate an IP.  Cool.
Uses ip-api.com which is a Free for non-commercial use, no API key required.

"""

domains = ["google.com",
"microsoft.com",
"facebook.com",
"apple.com",
"instagram.com",
"linkedin.com",
"pickle.com"]

ip_api_query = []

def collect_ips():
    """
    Using dig as a subprocess via python, we do a DNS lookup for each name in the 
    domain list, and capture the first returned IP, even if there are multiple or just one.
    Build a dictionary to be used for geo-location purposes as data input to requests.
    """
    for domain in domains:
        command = f'dig +noall +short {domain}'.split()     # I hate writing list of the commands and it's prone to error, so I just split it.
        ip = subprocess.Popen(command, stdout=subprocess.PIPE)
        ip, _ = ip.communicate()    # capture from stdout above
        ip = ip.decode().split()    # convert from bytes
        ip = ip[0] if len(ip) > 1 else ip[-1]   # I want the first ip in a list, otherwise the 'last' (for some reason it didn't like index 0 when only one entry and so who cares)
        ip_api_query.append({ "query" : f"{ip}", "fields" : "country,regionName,city,timezone,query"})

def get_geo():
    """
    The ip_api_query isn't formatted correctly to send as data in the requests, so we convert it and 
    set geo_data as global (just cause we can) and capture the output from the API post, and convert
    it to JSON as opposed to just receiving it as a str.
    """
    ip_api_url = "http://ip-api.com/batch"
    api_query = json.dumps(ip_api_query) # convert to proper data structure for json data in url   
    global geo_data
    geo_data = requests.post(ip_api_url, data=api_query).json()

def update_geo_data():
    """
    We send and receive only the fields we want, but it doesn't include the domain name as part of the API query,
    so to make the print easier, we add domain to each dict.
    """
    for i, g in enumerate(geo_data):
        g["domain"] = domains[i]

def print_geo_data():
    """
    iterate the list and do gets on each dict and print it out.
    """
    for geo in geo_data:
        output = f'{geo.get("domain")} -> {geo.get("query")} : {geo.get("city")}, {geo.get("regionName")} {geo.get("country")} : {geo.get("timezone")}'
        print(output)

def main():
    collect_ips()
    get_geo()
    update_geo_data()
    print_geo_data()


if __name__ == '__main__':
    main()
