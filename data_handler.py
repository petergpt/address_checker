import csv
import json
import os

class DataHandler:

    def read_csv(self, file_path):
        """Reads the input CSV file and returns the addresses as a list of strings."""
        addresses = []
        try:
            with open(file_path, mode='r', newline='', encoding='utf-8') as csvfile:
                reader = csv.reader(csvfile)
                for row in reader:
                    # Ensure row is not empty
                    if row and any(field.strip() for field in row):
                        addresses.append(' '.join(row))
            if not addresses:
                print(f"Warning: No valid addresses found in the CSV file {file_path}.")
        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
        except Exception as e:
            print(f"Error reading CSV file: {str(e)}")
        return addresses

    def save_txt(self, file_path, data):
        """Saves data to a plain text file."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as txtfile:
                txtfile.write("\n".join(data))  # Save each address as one string per line
        except Exception as e:
            print(f"Error saving TXT file {file_path}: {str(e)}")


    def save_json(self, file_path, data):
        """Saves data to a JSON file."""
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as jsonfile:
                json.dump(data, jsonfile, indent=4)
        except Exception as e:
            print(f"Error saving JSON file {file_path}: {str(e)}")

    def read_json(self, file_path):
        """Reads data from a JSON file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as jsonfile:
                return json.load(jsonfile)
        except FileNotFoundError:
            print(f"Error: File {file_path} not found.")
            return None
        except json.JSONDecodeError:
            print(f"Error: Failed to decode JSON from file {file_path}.")
            return None
        except Exception as e:
            print(f"Error reading JSON file {file_path}: {str(e)}")
            return None
