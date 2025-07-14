from typing import Optional, List, Dict, Tuple
from objects import FileAccess, FileItem, Users
import logging
import uuid
import json
import pickle
import os


logging.basicConfig(
    format='%(levelname)s %(asctime)s: %(message)s', level=logging.INFO)


database_file = "data.db"


def write2db(data: Dict[str, FileItem]):
    with open(database_file, 'wb') as output_file:
        pickle.dump(data, output_file, pickle.HIGHEST_PROTOCOL)


def error(code: int, msg: str) -> Tuple[str, int]:
    return '{"error": "' + msg + '"}', code


class Service:

    def __init__(self) -> None:
        self.data: Dict[str, FileItem] = {}
        if os.path.exists(database_file):
            with open(database_file, "rb") as input_file:
                self.data: Dict[str, FileItem] = pickle.load(input_file)
        self.users: Users = Users()

    def create(self, owner: str, password: str, subjects: List[str], accesses: Dict,
               expiry: Optional[str], frequency: Optional[int]) -> Tuple[str, int]:

        logging.info(f"Creating file: owner = {owner} and subjects = [{subjects}]")
        logging.info(f"Expiry is {expiry} and Frequency is {frequency}")
        for access in accesses:
            logging.info(f"Access: {access}")

        if not self.users.check_user(owner):
            return error(400, "Owner is not found")
        if not (self.users.authenticate(owner, password)):
            return error(401, "Password is incorrect")

        file_id: str = str(uuid.uuid1())
        file_access: List[FileAccess] = []

        for access in accesses:
            if not ("user" in access):
                return error(400, "User field missing")
            user_id: str = str(access["user"])

            if not ("rw" in access):
                return error(400, "RW field missing")
            access_type = None
            if access["rw"].upper() == "TRUE":
                access_type = True
            if access["rw"].upper() == "FALSE":
                access_type = False
            if access_type is None:
                return "RW field is not TRUE or FALSE", 400

            location: Optional[str] = access["location"] if "location" in access \
                                      else None

            frequency = None
            if "frequency" in access:
                try:
                    frequency = int(access["frequency"])
                    if frequency <= 0:
                        return error(400,
                                     "Frequency is not positive integer")
                except ValueError:
                    return error(400, "Frequency is not positive integer")

            file_access.append(FileAccess(user_id, access_type, location, frequency))

        logging.info(f"Creating a file with id = {file_id}")
        write2db(self.data)
        self.data[file_id] = FileItem(owner, subjects, file_access, expiry)
        return ('{ "status": "ok", "id": "' + file_id + '" }'), 200

    def dsr(self, subject_id, password) -> Tuple[str, int]:
        logging.info(f"DSR request for subject = {subject_id}")
        auth = self.users.authenticate("admin", password)
        if not auth:
            return error(401, "Not authorized")

        for file_id in self.data.keys():
            if self.data[file_id].delete_subject(subject_id):
                logging.info(f"Deleted subject = {subject_id} from file = {file_id}")
        write2db(self.data)
        return '{ "status": "ok" }', 200

    def validate(self, file_id, user_id, location) -> Tuple[str, int]:
        if not (file_id in self.data):
            return error(404, f"File ID = {file_id} not found")

        result: Tuple[Optional[bool], str] = \
            self.data[file_id].check_access(user_id, location)
        access: Optional[bool] = result[0]
        err: str = result[1]

        if access is None:
            return error(401, err)
        assert err == ""
        logging.info(
            f"Checking fileId = {file_id} for userId = {user_id} at {location}")
        write2db(self.data)
        access_type = '{ "access": "' + ("read-write" if access else "read-only")
        subjects = '", "dsr": [' + (", ".join(self.data[file_id].dsr())) + ']}'
        return (access_type + subjects), 200

    def invalidate(self, file_id: str, password: str, user_id: Optional[str],
                   location: Optional[str]) -> Tuple[str, int]:

        if not (file_id in self.data):
            return error(404, f"File ID = {file_id} not found")

        if (user_id is None) and (location is not None):
            return error(404, f"Location = {location} provided but not user")

        owner: str = self.data[file_id].owner
        if not (self.users.authenticate(owner, password)):
            return error(400, "Password is incorrect")

        if user_id is None:
            self.data[file_id].remove_all_users()
            return '{ "status": "ok" }', 200

        result: bool = self.data[file_id].remove_user(user_id, location)
        if result:
            logging.info(f"Invalidate user = {user_id} for fileId = {file_id}")
            write2db(self.data)
            return '{ "status": "ok" }', 200
        return error(400, "user not present")

    def acknowledge(self, file_id, subject_id):
        if not (file_id in self.data):
            return error(404, f"File ID = {file_id} not found")

        status: Optional[bool] = self.data[file_id].remove_subject(subject_id)
        if status is None:
            return error(400,
                         f"Subject = {subject_id} not in file_id = {file_id}")
        if status:
            return error(400,
                         f"DSR for Subject id = {subject_id} was never issued")

        write2db(self.data)
        return '{ "status": "ok" }', 200

    def debug(self):
        data = {}
        for file_id in self.data:
            data[file_id] = self.data[file_id].dictionary()
        return json.dumps(data), 200
