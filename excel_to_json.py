import pandas as pd
import os
import json
import glob

def excel_to_json(file_path):
    # Read all sheets from Excel file
    excel_data = pd.read_excel(file_path, sheet_name=None)
    
    # Convert each sheet to JSON
    json_data = {}
    for sheet_name, df in excel_data.items():
        # Convert DataFrame to JSON
        json_data[sheet_name] = json.loads(df.to_json(orient='records'))
    
    return json_data

def combine_json_files(directory):
    combined_data = {}
    
    # Get all JSON files in directory
    json_files = glob.glob(os.path.join(directory, '*.json'))
    
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
            # Flatten the data structure by merging all sheets
            for sheet_name, records in data.items():
                for record in records:
                    employee_id = record.get('Employee ID')
                    if employee_id:
                        if employee_id not in combined_data:
                            combined_data[employee_id] = {}
                        # Update employee record with new data
                        combined_data[employee_id].update(record)
    
    # Save as a single database file
    with open('employee_database.json', 'w') as f:
        json.dump(combined_data, f, indent=4)
    print("Created employee database with combined records")

def process_directory(directory):
    # Process all Excel files in the directory
    for filename in os.listdir(directory):
        if filename.endswith('.xlsx'):
            file_path = os.path.join(directory, filename)
            json_data = excel_to_json(file_path)
            
            # Save JSON to file
            json_filename = filename.replace('.xlsx', '.json')
            with open(json_filename, 'w') as json_file:
                json.dump(json_data, json_file, indent=4)
            print(f"Converted {filename} to {json_filename}")
    
    # Combine all JSON files
    combine_json_files(directory)

if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.abspath(__file__))
    process_directory(current_directory)
