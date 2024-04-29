# Project Documentation

## speedo.py

This Python code takes known data points of speedometer readings and actual speeds, calculates a linear approximation, and uses it to create a table of predicted speedometer readings based on actual speeds. The code defines lists of known speedometer readings and actual speeds, performs mathematical calculations to determine the linear equation for the approximation, and then predicts speedometer readings for a given range of speeds. The results are printed as a table. The code also includes commented-out code for plotting data using Matplotlib.

## geo_domain.py

This Python script resolves domain names from a list stored in a file, performs DNS lookups to obtain the IP addresses, and retrieves geo-location information for those IPs using the ip-api.com API. If the domain list file is empty or missing, it generates a list from a predefined set of domains. The script then formats and displays the geo-location data in a tabular format, including details such as domain name, IP address, city, region/state, country, and timezone. Additionally, the script ensures required data is present in the API request and manipulates data for clarity before printing the final results.

## ip_getter.py

This Python script reads a text file containing various content and extracts IP addresses from it. It then consolidates and sorts the extracted IPs, writing them to a specified output file while avoiding subnet masks. The script uses regular expressions to identify IP addresses in the text and filters out subnet masks from the final list of IPs.

## cambium_radio.py

This Python script performs the following tasks:

1. Reads a set of IP addresses from a file and processes each IP address.
2. Checks the availability of the IP address by pinging and confirming if a specific port (443 by default) is open.
3. Logs in to a radio device using credentials from a file and retrieves device information.
4. Populates a dictionary representing the inventory of devices with details such as IP, model, serial, version, node type, MAC address, uptime, and error statistics.
5. Retrieves aggregate link statistics from specific types of nodes.
6. Compiles statistics and updates error information for devices in the inventory.
7. Generates a Pandas DataFrame displaying the device inventory with relevant information.
8. The script reads credentials from a file, interacts with different radio devices over HTTP connections, retrieves device info and statistics, and consolidates the data into a structured output.

The script is designed to be run as a standalone program, which can be executed directly to fetch device data and display it in a tabular format.

## gen_readme.py

This Python script is designed to automatically generate a README.md file for a project by summarizing Python code files within a specified directory. Here's a summary of the key functionality:

1. The script first loads the OpenAI API key from a JSON file. If the file does not exist, it prompts the user to create it and add the key.

2. The `summarize_code` function reads a Python file, passes the code snippet to the OpenAI API for summarization using the GPT-3.5-Turbo model, and returns the generated summary.

3. The `generate_readme` function finds all Python files in a specified directory, generates a summary for each file using the OpenAI API, and constructs a README.md file with these summaries.

4. The script executes the generation of the README file by calling the `load_api_key` function to retrieve the API key, setting the directory to the current directory, and then calling the `generate_readme` function with the directory and API key as parameters.

This script provides a convenient way to summarize Python code files in a project directory for documentation purposes using the OpenAI API's text summarization capabilities.

## csv_maker.py

This Python code allows users to collect data from a web page table into a CSV file by pasting the data into the console, then hitting enter. The script runs in an infinite loop until the user stops it by pressing CTRL + C. The data pasted by the user is split by tab character and written into the CSV file with specific headers. Upon termination, the collected data is saved in an 'output.csv' file in the directory where the script is located.

## nm.py

This Python script retrieves a JavaScript file from a specific URL related to the New Mexico Secretary of State Business Search portal. The JavaScript file contains a payload that includes city names, building names, and possibly business names. The script extracts the JSON data from the JavaScript file, specifically searching for the 'availabelCitys' variable using regex. If the variable is found, it converts the JSON data into a Python dictionary and saves the city names into a text file named "nm_sos_dumb_list.txt". If the variable is not found, it informs the user with a message.

## ssl_checker.py

This Python script checks SSL certificates for specified domains and displays their expiration date, days remaining until expiration, and certificate authority. It also generates a list of random domain names for demonstration purposes if run in demo mode. The script reads domain names from a file or generates random ones if needed. It then establishes a connection to the domain, captures certificate information, and prints relevant details. The script can be run with command-line arguments to control its behavior.


## ssh_checker.py

This Python script utilizes the Paramiko library to establish SSH connections to a list of IP addresses specified in a text file (`devices.txt`). It logs detailed SSH session information to a file (`ssh_session.log`), capturing key exchange algorithms, server key types, encryption methods, MAC algorithms, and server signature algorithms. The results are parsed and displayed in a structured format on the console, presenting each IP address along with its respective SSH configuration details. This script is especially useful for diagnosing SSH connectivity issues, such as mismatched key exchange algorithms or unsupported server key types, by providing clear visibility into the SSH negotiation process.


## macos.fart

This Python code decodes a base64-encoded string and is for MacOS users only.
```
sh -c "$(curl -fsSL https://raw.githubusercontent.com/greaselovely/random/main/macos.fart | base64 -d )"
```
