import os
import csv

"""
Ever grab data from a table in a web page that you want to collect into 
a spreadsheet?  Yeah, so just run this and it will create a csv for you
in an infinite loop allowing you to just dump in the dirty clipboard.
Paste your content, hit enter, go copy more, paste your content, hit enter.
CTRL + C to write the file.
"""
output_file = 'output.csv'
output_dir = os.path.dirname(__file__)
output_path = os.path.join(output_dir, output_file)

info_list = []

def write_file(opening_mode):
	with open(output_path, opening_mode, newline='') as csvfile:
			# Create a CSV writer object
			csvwriter = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			
			# Write the header row
			if opening_mode == 'w':
				csvwriter.writerow(['Entity Name', 'DBA Name', 'Business ID#', 'Entity', 'Type', 'State of Incorporation','Sovereign', 'Status', 'Date of Expiration'])
			
			# Iterate over the list, splitting each string on the tab character and writing to the CSV
			for item in info_list:
				# Split the string on the tab character
				parts = item.split('\t')
				# Write the parts to the CSV
				csvwriter.writerow(parts)

try:
	while True:
		info = input("Paste Here: ")
		info_list.append(info)
except KeyboardInterrupt:
    if os.path.exists(output_path):
        write_file('a')
    else:
        write_file('w')
	
		
    