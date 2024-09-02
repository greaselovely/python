import os
import re

"""
I wrote this to take a text file full of whatever
crap and extract all IPs out of it.
Then it takes all IPs, condenses them down and sorts them.
Writes them out to the output file.  I also avoid subnet masks at the bottom.
"""

path = os.path.curdir
input_file = "raw.txt"
output_file = "ip.txt"
input = os.path.join(path, input_file)
output = os.path.join(path, output_file)

with open(input, 'r') as f:
    text = f.read().splitlines()

pattern = r'[0-9]+(?:\.[0-9]+){3}'

first = []
for line in text:
    ip = re.findall(pattern, line) # creates a list of IPs
    # print(ip)
    if ip:
        for i in ip:
            first.append(i)

final = list(set(first))
final.sort()

if len(final) > 0:
    with open(output, 'w') as w:
        for ip in final:
            if ip[-7:] == "255.255":
                continue
            elif ip[-4:] == ".0.0":
                continue
            else:
                print(ip)
                w.write(f"{ip}\n")
