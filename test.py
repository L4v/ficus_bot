import requests
import json


get_response = requests.get(f"https://api.github.com/repos/L4v/ficus_bot/commits/master")
get_response_json = get_response.json()
print(get_response_json["commit"]["message"])