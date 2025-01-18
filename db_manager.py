import json
import os

FOLDER_PATH = os.getcwd()
if os.getcwd() == "/":
    FOLDER_PATH = "/home/maxet24/doklad_gen"

# File path
file_path = FOLDER_PATH + "/logs/doklad_db.json"

def get_db():
    try:
        with open(file_path, "r") as file:
            data = json.load(file)
        return data
    except FileNotFoundError:
        # If the file doesn't exist, return an empty dictionary
        return {}

def set_db(data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=2)

if __name__ == "__main__":
    print(json.dumps(get_db(), indent=4))
    print(file_path)