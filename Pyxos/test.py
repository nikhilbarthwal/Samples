import requests
from setup import setup

url = "http://34.70.195.8:8080"

def test(suffix, json_data):
    response = requests.post(url + suffix, json=json_data)
    if response.status_code < 300:
        print('POST request successful!')
        print('Status Code:', response.status_code)
        print('Response:', response.text)
        return response.text
    else:
        print('POST request failed!')
        print('Status Code:', response.status_code)
        print('Response:', response.text)
        return None


def debug():
    response = requests.get(url + "/debug")



file_id = test("/admin/create", """
{
    "owner": "nikhil",
    "password": "barthwal",
    "subjects": ["apple", "mango", "banana"],
    "access": [
        { "user": "pranay", "rw": "true", "location": "usa" },
        { "user": "nino", "rw": "false", "location": "canada" }
    ]
}""")

debug()

# This will be access denied!
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "nino", ' +
    '"ip_address": "usa" } ')


# This whould be a read only access
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "nino", ' +
    '"ip_address": "canada" } ')

# This whould be a read/write access
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "pranay", ' +
    '"ip_address": "usa" } ')



# TODO: Test  /admin/dsr
# TODO: Test  /client/acknowledge
# TODO: Test  /admin/user/invalidate
