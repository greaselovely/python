import sys
import csv

def parse_org_file(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()
    
    # Parse "Name - Title" format
    people = [line.strip().split(' - ') for line in lines if line.strip()]
    
    # Create CSV rows with employee, manager relationships
    csv_rows = []
    for i, (name, title) in enumerate(people):
        if i == 0:  # CEO has no manager
            manager = ""
        else:
            manager_idx = (i - 1) // 2
            manager = people[manager_idx][0]
        
        csv_rows.append([name, title, manager])
    
    return csv_rows

def write_lucidchart_csv(rows, output_file):
    with open(output_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name', 'Title', 'Manager'])  # Header
        writer.writerows(rows)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python script.py input_file.txt output_file.csv")
        sys.exit(1)
    
    rows = parse_org_file(sys.argv[1])
    write_lucidchart_csv(rows, sys.argv[2])
    print(f"CSV file created: {sys.argv[2]}")

# Example input file format:
# John Smith - CEO
# Jane Doe - VP Engineering
# Bob Wilson - VP Sales