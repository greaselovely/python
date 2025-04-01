import requests
import xmltodict
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


# NGFW API details
firewall_ip = "10.29.60.5"
ngfw_api_key = "LUFRPT1uK2haejlOYmZ3ck5Vb2M0eUZxMTdaSUNjeE09YnJMaXJwbGd3eENvMUF2YUlVZzVxcng5c1ZIU1IzZWtTS1VKK0dFUU1TTUhveTZRbVpDeFRQelhmZEdZTjdCRg=="

# Cortex XDR API details
xdr_api_url = "https://api-swcommercial.xdr.paloaltonetworks.com/public_api/v1/incidents/"
xdr_api_key = "32bknxb4GAdhWK8MZqedbjaufOpKqXctKdZo7A1OiJwFNXwVp5gcW9J1yqeqK3uE2EUfwPBu28Vu89v83SlMv8L0D7UH74HLATkg2FxvgvsOTNxahpFtgO1UBgwnGKC9"
xdr_api_key_id = "1"

def check_fqdn_resolution():
    url = f"https://{firewall_ip}/api/"
    params = {
        "type": "op",
        "cmd": "<show><dns-proxy><fqdn><all></all></fqdn></dns-proxy></show>",
        "key": ngfw_api_key
    }
    response = requests.get(url, params=params, verify=False)
    response.raise_for_status()
    return response.text

def parse_fqdn_response(response_xml):
    unresolved_fqdns = []
    response_dict = xmltodict.parse(response_xml)
    
    # Access the <result> section
    result = response_dict.get("response", {}).get("result", "")

    # Ensure result is a string, then split by lines and parse manually
    if isinstance(result, str):
        lines = result.splitlines()
        for line in lines:
            line = line.strip()
            if line and "::  unknown" in line:  # Check for unresolved FQDNs
                fqdn_name = line.split()[0]
                unresolved_fqdns.append(fqdn_name)
    else:
        print("Unexpected format in <result>: Skipping parsing.")

    return unresolved_fqdns


def create_xdr_incident(unresolved_fqdns):
    headers = {
        "Authorization": xdr_api_key,
        "x-xdr-auth-id": xdr_api_key_id
    }
    payload = {
        "alerts": [],
        "description": f"FQDN resolution issues detected for: {', '.join(unresolved_fqdns)}",
        "status": "new",
        "severity": "high",
        "incident_type": "Networking"
    }
    response = requests.post(xdr_api_url, json=payload, headers=headers)
    response.raise_for_status()
    print("Incident created successfully in Cortex XDR.")

if __name__ == "__main__":
    try:
        fqdn_response = check_fqdn_resolution()
        print(fqdn_response)
        unresolved_fqdns = parse_fqdn_response(fqdn_response)
        if unresolved_fqdns:
            print(f"Unresolved FQDNs detected: {unresolved_fqdns}")
            create_xdr_incident(unresolved_fqdns)
        else:
            print("All FQDNs resolved successfully.")
    except Exception as e:
        print(f"Error: {e}")
