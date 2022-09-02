import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import os
import json
import subprocess as sub
import platform
import socket

requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import sys # delete me one you update the variables below.
sys.exit() # delete me one you update the variables below.


########
path = "/my/folder/or/path/to/stuff/and/things" # even on Windows if you use '/' it works and saves time on path problems
input_file = "ip.txt" # list of IPs to run through; see: ip.getter.py
output_file = "CambiumDeviceInfo.csv" # CSV Output

auspw='{"username":"admin","password":"MyAwesomePasswordHere"}'
########


"""
Fakey Grind 360 to McTwist
    -Giggly Bits
"""

########

dirname = os.path.dirname(path)
input = os.path.join(path, input_file)
output = os.path.join(path, output_file)

def convert_to_json(s):
    return json.loads(s.content.decode('utf-8'))

def ping(ip):
    if platform.system() == "Windows":
        count = "-n"
    else:
        count = "-c"
    command = f"ping {count} 1 -w 2 {ip}".split()
    resp = sub.call(command, stdout=sub.DEVNULL) # suppress stdout
    return resp

def check_port(ip, port=443):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex((ip, port))
    sock.close
    return result


# read IPs from input_file
with open(input, 'r') as f:
    text = f.read().splitlines()

# do stuff and things
def main():
    with open(output, 'w') as f:
        f.write(f"Name,IP,Model,Serial,Version,Uptime (D H:M:s),Note\n")
        i = 1
        for ip in text:
            """
            Let's test the endpoint to make sure we can get to it
            and that the endpoint is listening on the port we are 
            expecting, if either test fails, move on to the next IP.
            """
            # PING and check if port is open!
            if ping(ip) == 0:
                if check_port(ip) == 0: # Can ping IP
                    pass # and port is open, so go do stuff
                else:
                    f.write(f"-,{ip},,,,Unreachable\n")
                    continue # nothing to do
            else:
                f.write(f"-,{ip},,,,Unreachable\n") # Cannot ping IP
                continue # nothing to do


            """
            Login to the radio and retrieve the session 'key'
            that we will pass to the url to get device info
            We're going to ping it first, which is not reliable 
            but neither is waiting on requests to time out and 
            break the script
            """
            # Login and get API key
            url = f"https://{ip}/local/userLogin"
            try:
                login = requests.post(url, data=auspw, verify=False)
                user = json.loads(auspw)['username']
                if login.status_code == 401:
                    name = "nada"
                    f.write(f"-,{ip},,,,Inaccessible\n")
                    continue
                bearer = convert_to_json(login)['message']
            except ConnectionError:
                print(f"Something is broke")

            """
            We take bearer, (the value of 'message' from the radio login, like an api key)
            post it to the radio via header, and retrieve the data into 'devinfo'
            data comes to us in bytes, we decode it, convert it to a dict using json 
            and grab values from the keys in the dict
            """
            header = '{"Authorization" : "Bearer ' + bearer + '"}' # this was tricky to figure out, settled on a str and then convert it
            header = json.loads(header) # convert to dict
            url = f"https://{ip}/local/getDeviceInfo"          
            json_data = ''
            try:
                devinfo = requests.post(url, headers=header, json=json_data, verify=False)
                devinfo = convert_to_json(devinfo)
            
                name = devinfo['name']
                model = devinfo['model']
                serial = devinfo['msn']
                version = devinfo['swVer']
                uptime_sec = devinfo['uptime']
                uptime = str(datetime.timedelta(seconds = uptime_sec))
                uptime = uptime.replace(',', '')
                
                print(f"[{i}] {name}")
                i += 1
                f.write(f"{name},{ip},{model},{serial},'{version},{uptime},{user}\n")
            except ConnectionError:
                print(f"Something is broke")

if __name__ == "__main__":
    main()
