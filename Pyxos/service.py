import logging
import uuid
from typing import Optional

import config
from database import Database

logging.basicConfig(
    format='%(levelname)s %(asctime)s: %(message)s', level=logging.INFO)


class Service:

    def __init__(self) -> None:
        logging.info("Initialize database")
        self.db: Database = Database()

    """
    Return:
    - 201: Ok
    - 400: Bad request due to user not found
    - 401: Password is wrong
    """
    def create(self, owner, password, subjects, access):
        if not (self.db.check_user(owner)):
            return error(400, "User is not found")
        if not (self.db.authenticate(owner, password)):
            return "Password is incorrect", 401

        file_id: str = str(uuid.uuid1())
        self.db.create_file(file_id, owner)

        for subject in subjects:
            self.db.add_subject(subject, file_id)

        for params in access:
            if not ("user" in params):
                return "User field missing", 400
            user_id: str = str(params["user"])

            if not ("rw" in params):
                return "RW field missing", 400
            access = params["rw"].upper()
            if (access != "TRUE") and (access != "FALSE"):
                return "RW field is not TRUE or FALSE", 400

            if not ("location" in params):
                return "Location field missing", 400
            location: str = str(params["location"])

            self.db.add_access(user_id, file_id, location, access)

        logging.info(f"Created {file_id} for {owner}")
        return file_id, 201

    """
    Return:
    - 200: Ok
    - 401: Password is wrong
    """
    def dsr(self, subject_id, password):
        auth = self.db.authenticate(config.admin, password)
        if not auth:
            return "Not authorized", 401
        outcome = self.db.delete_subject(subject_id)
        logging.info(f"DSR for subjectId = {subject_id}")
        return "Ok", 200

    """
    Return:
    - 200: Ok
    - 401: Unauthorized
    - 404: File not found
    """
    def validate(self, file_id, user_id, ip_address):
        if not self.db.check_file(file_id):
            return f"File ID = {file_id} not found", 404
        location = ip_address  # TODO: Get country from IP address
        access: Optional[bool] = self.db.check_access(file_id, user_id, location)
        logging.info(f"Validate fileId = {file_id} for userId = {user_id}")
        if access is None:
            return "Unauthorized", 401
        if access:
            return "read-only", 200
        return "read-write", 200

    """
    Return:
    - 200: Ok
    - 404: File not found!
    - 401: Password is wrong
    - 404: User not found
    """
    def invalidate(self, file_id, password, user_id):
        owner: Optional[str] = self.db.get_owner(file_id)
        if owner is None:
            return "File does not exists", 404
        if not (self.db.authenticate(owner, password)):
            return "Password is incorrect", 400
        self.db.remove_user(file_id, user_id)
        logging.info(f"Invalidate fileId = {file_id} for user = {user_id}")
        return "Success", 200

    """
    Return:
    - 200: Ok
    - 400: Bad request
    - 404: file not found!
    """
    def acknowledge(self, file_id, subject_id):
        if self.db.check_file(file_id):
            return "File id not found", 404
        outcome = self.db.acknowledge_dsr(file_id, subject_id)
        if outcome:
            logging.info(f"Acknowledge for {file_id} with subject {subject_id}")
            return "Success", 200
        return f"DSR Subject = {subject_id} does not exists", 400

    def debug(self):
        logging.info("____________________________________________________")
        self.db.debug()
        logging.info("____________________________________________________")
        return '', 200

    def shutdown(self):
        self.db.close()
