import re
import os
import requests
import json

"""
While farting around collecting data via the NM Sec of State Biz Search
I found a javascript that contained an absurd payload in it with what 
was supposed to be nothing but city names, but it also contains building
names and perhaps some business names.  Pretty dumb honestly.  So this 
just goes to collect that script and dump it to a file.  As of this 
writing of this dumb script, it was up to 39,795 lines long.  Dumb.
"""


city_list_file = "nm_sos_dumb_list.txt"

url = 'https://portal.sos.state.nm.us/BFS/bundles/common/scripts?v=__Y_29wAC3pPlcKA30bFWRsdIrK7_Ofa6SFtIjQwTHc1'

# Fetch the content of the JavaScript file
response = requests.get(url, verify=False)
content = response.text

# Use regex to extract the JSON string assigned to the variable
# This regex looks for the pattern: var availabelCitys = jQuery.parseJSON('...json here...');
# And yes, available is misspelled.  Even dumber.
pattern = r"var availabelCitys = jQuery\.parseJSON\('(\[.*?\])'\);"
match = re.search(pattern, content, re.DOTALL)

if match:
    # Extract the JSON string
    json_str = match.group(1)
    
    # Convert the JSON string to a Python dictionary
    cities_list = json.loads(json_str)
    output_dir = os.path.dirname(__file__)
    output_path = os.path.join(output_dir, city_list_file)
    with open(output_path, 'w') as f:
        f.write('\n'.join(cities_list))
    
else:
    print("Could not find the 'availabelCitys' variable in the JavaScript content.")


