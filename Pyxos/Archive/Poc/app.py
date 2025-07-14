from flask import Flask, request
from service import Service, error
from typing import Dict, Tuple, Optional
import traceback
import json

app = Flask(__name__)
service = Service()


def handle(required_keys, optional_keys, handler) -> Tuple[str, int]:
    try:
        data = request.get_json()
        if data is None:
            return error(400, "No body found")

        try:
            json_data = json.loads(data)
        except:
            return error(400, "Unable to parse payload")

        params: Dict[str, Optional[str]] = {}

        for key in required_keys:
            try:
                params[key] = json_data.get(key)
            except KeyError:
                return error(400, "parameter " + key + " not found!")

        for key in optional_keys:
            try:
                params[key] = json_data.get(key)
            except KeyError:
                params[key] = None

        return handler(params)
    except:
        return str(traceback.format_exc()), 400


@app.route('/')
def start():
    return 'Pyxos service running in Google Cloud!\n', 200


"""
Endpoint: POST /client/validate
    - fileId (string): Unique identifier of the file being accessed.
    - userId (string): User ID requesting access.

Return:
    - 200: Ok
    - 401: Unauthorized
"""


@app.route("/client/validate", methods=["POST"])
def validate():
    return handle(["file_id", "user_id", "ip_address"], [],
                  lambda p: service.validate(
                      p["file_id"], p["user_id"], p["ip_address"]))


""""
Endpoint: POST /admin/user/invalidate
    - fileId: Unique identifier of the file.
    - password: Password for the user which made the request.
    - userId (optional): User ID for which access needs to be invalidated.
      If no userId is provided, then the entire file is deleted.
# Check if access is invalidated and return list to be deleted
Return:
    - 200: Ok
    - 404: File not found!
    - 401: Password is wrong
    - 404: User not found
"""


@app.route("/client/invalidate", methods=["POST"])
def invalidate():
    return handle(["file_id", "password"], ["user", "location"],
                  lambda p: service.invalidate(
                      p["file_id"], p["password"], p["user"], p["location"]))


"""
Endpoint: /client/acknowledge
Request Parameters:
    - fileId: Id of the file on which DSR is being acknowledged.
    - subjectId: The subject for which the DSR is acknowledged.

Return:
    - 200: Ok
    - 404: file not found!
    - 404: subject not found!
"""


@app.route("/client/acknowledge", methods=["POST"])
def acknowledge():
    return handle(["file_id", "subject"], [],
                  lambda p: service.acknowledge(p["file_id"], p["subject"]))


"""
Endpoint: POST /admin/dsr , and ONLY BE MADE BY ADMIN
    - subjectId: Unique identifier of the subject for which the DSR is being issued.
    - password: Verify that the person making the request is a admin

Return:
    - 200: Ok
    - 404: subject not found!
    - 401: Password is wrong

"""


@app.route("/admin/dsr", methods=["POST"])
def dsr():
    return handle(["subject", "password"], [],
                  lambda p: service.dsr(p["subject"], p["password"]))


"""
Endpoint: POST /admin/create , and ONLY BE MADE BY ADMIN
    - owner: Owner of the file
    - password: Password of the owner
    - subjects: List of subjects
    - access: Tuple of users, access type (Tue for full access and False for
              read only access), and list of countries.

Return:
    - 201: Created
    - 400: Bad request due to user not found
    - 401: Password is wrong

"""


@app.route("/admin/create", methods=["POST"])
def create():
    return handle(["owner", "password", "subjects", "access"],
                  ["expiry", "frequency"],
                  lambda p: service.create(p["owner"], p["password"], p["subjects"],
                                           p["access"], p["expiry"], p["frequency"]))


@app.route("/debug")
def debug():
    return str(service.debug()), 200


if __name__ == '__main__':
    app.run(port=8080)
