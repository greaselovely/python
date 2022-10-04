import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
import json
import subprocess as sub
import socket
import datetime
import pandas as pd

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import sys
sys.exit()  # Delete me once you do stuff below.


#######
if os.name == "nt":
    path = "c:/path/to/stuff/and/things"
else:
    path = "/mnt/c/path/to/stuff/and/things"
input_file = "ip.txt"
output_file = "CambiumReport.csv"
# create a creds file that looks like this:
# {"username":"admin","password":"MyRadPassword"}
# or just enter that as cred = {"username":"admin","password":"MyRadPassword"}
# your call
with open(path + "/creds", 'r') as cred:
    auspw=cred.read()
#######


dirname = os.path.dirname(path)
input = os.path.join(path, input_file)
output = os.path.join(path, output_file)
df_table = []
df_index = []
stats = []
inventory = {}
rx_errors = ''
tx_errors = ''

def clear():
    os.system("cls") if os.name == "nt" else os.system("clear")

def convert_to_json(s):
    return json.loads(s.content.decode('utf-8'))

def ping(ip):
    if os.name == "nt":
        nop = "-n"
    else:
        nop = "-c"
    command = f"ping {nop} 1 -w 2 {ip}".split()
    resp = sub.call(command, stdout=sub.DEVNULL) # suppress stdout
    return resp

def check_port(ip, port=443):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(3)
    resp = sock.connect_ex((ip, port))
    sock.close
    return resp

def createInventory(*args):
    # creates a dict to refer to later
    ip, name, model, serial, version, nodetype, mac_address, uptime, rx_errors, tx_errors = args
    inventory[name] = {'ip':ip,'model':model,'serial':serial,
                    'version':version,'nodetype':nodetype,
                    'mac_address':mac_address,'uptime':uptime,
                    'rx_errors':rx_errors, 'tx_errors':tx_errors}
    
def create_df_table():
    for key in inventory.keys():
        df_index.append(key)
        df_table.append(list(inventory.get(key).values()))

    df = pd.DataFrame(data=df_table)
    df.columns

    df.set_axis(["IP","Model","Serial","Version","Node Type","MAC","Uptime","RX Errors","TX Errors"],axis=1,inplace=True)
    df.set_axis([df_index], axis=0, inplace=True)
    return df.to_string()

def getHeader(bearer):
    global header
    header = '{"Authorization" : "Bearer ' + bearer + '"}' # this was tricky to figure out, settled on a str and then convert it
    header = json.loads(header) # convert to dict

def DeviceLogin(ip):
    """
    Login to the radio and retrieve the session 'key'
    that we will pass to the url to get device info
    """
    # Login and get API key
    url = f"https://{ip}/local/userLogin"
    try:
        login = requests.post(url, data=auspw, verify=False)
        if login.status_code == 401:
            print(login.status_code)
        bearer = convert_to_json(login)['message']
    except ConnectionError:
        print(f"Something is broke")
    getHeader(bearer)

def getDeviceInfo(ip):
    """
    We take bearer, (the value of 'message' from the radio login, like an api key)
    post it to the radio via header, and retrieve the data into 'devinfo'
    data comes to us in bytes, we decode it, convert it to a dict using json 
    and grab values from the keys in the dict
    """
    url = f"https://{ip}/local/getDeviceInfo"          
    json_data = ''
    try:
        devinfo = requests.post(url, headers=header, json=json_data, verify=False)                
        devinfo = convert_to_json(devinfo)
        
        name = devinfo['name']
        model = devinfo['model']
        serial = devinfo['msn']
        version = devinfo['swVer']
        nodetype = devinfo['type']
        mac_address = devinfo['mac']
        uptime_sec = devinfo['uptime']
        uptime = str(datetime.timedelta(seconds = uptime_sec))
        uptime = uptime.replace(',', '')
        
    except ConnectionError:
        print(f"Something is broke")
    return name, model, serial, version, nodetype, mac_address, uptime

def getAggrLinkStats(ip):
    try:
        url = f"https://{ip}/local/getAggrNetworkStats"
        # json_data = {"nodes":[],"iface":["nic1", "nic2", "nic3"]}
        json_data = {} # doesn't seem to matter if we pass info to the radio or not, it dumps everything
        nicinfo = requests.post(url, headers=header, json=json_data, verify=False)
        nicinfo = nicinfo.text # only the node type "DN" or "POP" maintains stats, "CN" does not
        return nicinfo

    except ConnectionError:
        print("b0rk3n")
   
def createStats():
    for device in inventory.values():
        if device['nodetype'] == "POP":
            ip = device['ip']
            DeviceLogin(ip)
            stat = getAggrLinkStats(ip)
            stat = json.loads(stat)
            for s in stat:
                stats.append(s)

def updateErrors():
    for stat in stats:
        for device in inventory.values():
            if device['mac_address'] == stat['mac'] and stat['iface'] == 'nic3': # nic3 = SFP on the radio
                device['rx_errors'] = stat['rx_errors']
                device['tx_errors'] = stat['tx_errors']

def main():
    # read IPs from input_file
    with open(input, 'r') as f:
        text = f.read().splitlines()

    # clear()
    for ip in text:
        # Ping and check if port is open!
        if ping(ip) == 0:
            if check_port(ip) == 0: # Can ping IP
                pass # and port is open, so go do stuff
            else:
                continue # nothing to do
        else:
            continue # nothing to do
        
        DeviceLogin(ip)
        name, model, serial, version, nodetype, mac_address, uptime = getDeviceInfo(ip)
        createInventory(ip, name, model, serial, version, nodetype, mac_address, uptime, rx_errors, tx_errors)
    
    createStats()
    
    updateErrors()
    
    print(create_df_table())


if __name__ == "__main__":
    main()
