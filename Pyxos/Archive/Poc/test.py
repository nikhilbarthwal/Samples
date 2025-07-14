import requests
import json

url = "http://127.0.0.1:8080"


def test(suffix, json_data):
    response = requests.get(url + suffix) if json_data is None else \
               requests.post(url + suffix, json=json_data)
    if response.status_code < 300:
        print('POST request successful!')
        print('Status Code:', response.status_code)
        print('Response:', response.text)
        if json_data is None:
            return None
        return json.loads(response.text)
    else:
        print('POST request failed!')
        print('Status Code:', response.status_code)
        print('Response:', response.text)
        return None


print("_________________________________________________________________________")
print("Create a new file and print id of it")
response = test("/admin/create", """
{
    "owner": "nikhil",
    "password": "barthwal",
    "subjects": ["apple", "mango", "banana"],
    "access": [
        { "user": "pranay", "rw": "true", "frequency": 2, "location": "usa" },
        { "user": "nino", "rw": "false", "location": "canada" },
        { "user": "nino", "rw": "false", "location": "mexico" },
        { "user": "ashish", "rw": "false" },
        { "user": "jajati", "rw": "true" }
    ]
}""")
file_id = response['id']


print("_________________________________________________________________________")
print("Nino is trying to access a file from USA, where he is not authorized")
# This will be access denied!
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "nino", ' +
     '"ip_address": "usa" } ')

print("_________________________________________________________________________")
print("Nino is trying to access a file from Canada, where he is read only access")
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "nino", ' +
     '"ip_address": "canada" } ')

print("_________________________________________________________________________")
print("Pranav access the file from the first time in USA. He is allowed")
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "pranay", ' +
     '"ip_address": "usa" } ')

print("_________________________________________________________________________")
print("Pranav access the file from the second time in USA. He is allowed")
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "pranay", ' +
     '"ip_address": "usa" } ')

print("_________________________________________________________________________")
print("Pranav access the file from the third time in USA. He is NOT allowed")
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "pranay", ' +
     '"ip_address": "usa" } ')

print("_________________________________________________________________________")
print("Admin issues a DSR request for apple, but with wrong password")
test("/admin/dsr", """{ "subject": "apple", "password": "wrong" }""")

print("_________________________________________________________________________")
print("Admin issues a DSR request for apple, but with correct password")
test("/admin/dsr", """{ "subject": "apple", "password": "password" }""")

print("_________________________________________________________________________")
print("Admin issues a DSR request for banana, but with correct password")
test("/admin/dsr", """{ "subject": "banana", "password": "password" }""")

print("_________________________________________________________________________")
print("Ashish accessed file from India and he is allowed but ...")
print("client is support to delete subjects apple and banana, since DSR is issued")
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "ashish", ' +
     '"ip_address": "india" } ')

print("_________________________________________________________________________")
print("Ashish's clients deletes subject apple and sends acknowledgement to server")
test("/client/acknowledge", '{ "file_id": "' + file_id + '", "subject": "apple" }')

print("_________________________________________________________________________")
print("Ashish's clients deletes subject banana and sends acknowledgement to server")
test("/client/acknowledge", '{ "file_id": "' + file_id + '", "subject": "banana" }')

print("_________________________________________________________________________")
print("Owner of the file decides to cut Nino's access in Canada")
test("/client/invalidate", '{ "file_id": "' + file_id + '''", "password":
     "barthwal", "user": "nino", "location": "canada" }''')

print("_________________________________________________________________________")
print("Now Nino cannot access a file from Canada, since his access is cut")
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "nino", ' +
     '"ip_address": "canada" } ')

print("_________________________________________________________________________")
print("But Nino can access a file from Mexico, since his access is not cut there")
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "nino", ' +
     '"ip_address": "mexico" } ')

print("_________________________________________________________________________")
print("Owner of the file decides to cut Ashish's access everywhere")
test("/client/invalidate", '{ "file_id": "' + file_id + '''", "password":
     "barthwal", "user": "ashish" }''')

print("_________________________________________________________________________")
print("Now Ashish cannot access the file from India")
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "ashish", ' +
     '"ip_address": "india" } ')

print("_________________________________________________________________________")
print("Jajati can access a file from Mexico, since his access is everywhere")
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "jajati", ' +
     '"ip_address": "mexico" } ')

print("_________________________________________________________________________")
print("Owner of the file decides to cut everyone's access")
test("/client/invalidate", '{ "file_id": "' + file_id + '''", "password":
     "barthwal" }''')

print("_________________________________________________________________________")
print("Now Jajati cannot access a file from Mexico, since all access is gone")
test("/client/validate", '{ "file_id": "' + file_id + '", "user_id": "jajati", ' +
     '"ip_address": "mexico" } ')

print("_________________________________________________________________________")
print("Make a GET request to debug endpoint to get a dump of database")
test("/debug", None)
