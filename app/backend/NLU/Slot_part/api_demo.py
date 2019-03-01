import requests

r = requests.get('http://127.0.0.1:5000/NLU/get_requirement/"不要华为的"')

print(r.text)