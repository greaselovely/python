import requests
import json
import os
import subprocess
import re

DEFAULT_CONFIG = {
    "firewall": {
        "label": "MY_FIREWALL",
        "rule_label": "MY_FIREWALL_RULE",
        "allowed_ports": ["22"],
        "allowed_protocols": ["TCP"]
    },
    "ip": {
        "url": "https://ipecho.net/plain"
    },
    "api": {
        "token": "YOUR_API_TOKEN_HERE"
    }
}


def load_or_create_config():
    config_file = 'linode.json'
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        # Update config with any new fields from DEFAULT_CONFIG
        updated = update_config_structure(config, DEFAULT_CONFIG)
        
        if updated:
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            print(f"Updated {config_file} with new structure. Please review and edit if necessary.")
        
        return config
    else:
        with open(config_file, 'w') as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        print(f"Created {config_file} with default values. Please edit it with your actual API token and other settings.")
        return DEFAULT_CONFIG

def update_config_structure(config, default_config):
    updated = False
    for key, value in default_config.items():
        if key not in config:
            config[key] = value
            updated = True
        elif isinstance(value, dict):
            if not isinstance(config[key], dict):
                config[key] = {}
            updated |= update_config_structure(config[key], value)
    return updated

def get_current_ip(ip_url):
    try:
        return requests.get(ip_url).text.strip()
    except requests.RequestException as e:
        print(f"Error fetching IP address: {e}")
        return None

def run_linode_cli(command, api_token):
    try:
        env = os.environ.copy()
        env['LINODE_CLI_TOKEN'] = api_token
        result = subprocess.run(['linode-cli'] + command, capture_output=True, text=True, check=True, env=env)
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error running Linode CLI command: {e}")
        print(f"Command output: {e.stderr}")
        return None

def get_firewall_id(firewall_label, api_token):
    firewalls = json.loads(run_linode_cli(['firewalls', 'list', '--json'], api_token))
    if firewalls is None:
        return None
    for firewall in firewalls:
        if firewall['label'] == firewall_label:
            return firewall['id']
    print(f"Firewall with label '{firewall_label}' not found.")
    return None

def sanitize_label(label):
    return re.sub(r'[^a-zA-Z0-9_.-]', '', label.replace(' ', '_').replace('(', '_').replace(')', '_'))

def update_or_add_firewall_rule(firewall_id, ip_address, ports, protocols, api_token, rule_label):
    current_rules_json = run_linode_cli(['firewalls', 'view', str(firewall_id), '--json'], api_token)
    if current_rules_json is None:
        return False
    
    current_rules = json.loads(current_rules_json)
    if isinstance(current_rules, list) and len(current_rules) > 0:
        current_rules = current_rules[0]
    inbound_rules = current_rules['rules']['inbound']

    sanitized_rule_label = sanitize_label(rule_label)
    existing_rule_index = next((i for i, rule in enumerate(inbound_rules) if rule['label'] == sanitized_rule_label), None)

    new_rule = {
        "label": sanitized_rule_label,
        "action": "ACCEPT",
        "protocol": protocols[0],  # Assuming we're using the first protocol
        "ports": ",".join(map(str, ports)),
        "addresses": {
            "ipv4": [f"{ip_address}/32"]
        }
    }

    if existing_rule_index is not None:
        inbound_rules[existing_rule_index] = new_rule
        print(f"Updating existing rule: {sanitized_rule_label}")
    else:
        inbound_rules.append(new_rule)
        print(f"Adding new rule: {sanitized_rule_label}")

    update_command = [
        'firewalls', 'rules-update', str(firewall_id),
        '--inbound', json.dumps(inbound_rules),
        '--outbound', json.dumps(current_rules['rules']['outbound'])
    ]
    result = run_linode_cli(update_command, api_token)
    return result is not None

def main():
    config = load_or_create_config()
    
    if config['api']['token'] == DEFAULT_CONFIG['api']['token']:
        print("Please edit the linode.json file and replace 'YOUR_API_TOKEN_HERE' with your actual Linode API token.")
        return

    current_ip = get_current_ip(config['ip']['url'])
    if not current_ip:
        return

    print(f"Current IP: {current_ip}")
    
    firewall_id = get_firewall_id(config['firewall']['label'], config['api']['token'])
    if not firewall_id:
        return

    print(f"Firewall ID: {firewall_id}")
    
    if update_or_add_firewall_rule(
        firewall_id, 
        current_ip, 
        config['firewall']['allowed_ports'], 
        config['firewall']['allowed_protocols'], 
        config['api']['token'], 
        config['firewall']['rule_label']
    ):
        print(f"Firewall updated to allow access from IP: {current_ip}")
    else:
        print("Failed to update firewall")

if __name__ == "__main__":
    main()