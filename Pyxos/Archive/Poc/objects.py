from typing import Optional, List, Dict, Tuple
from datetime import datetime

import logging

class FileAccess:
    def __init__(self, user: str, access_type: bool, country: Optional[str],
                 frequency: Optional[int]) -> None:
        self.user: str = user
        self.access_type: bool = access_type
        self.country: Optional[str] = country
        self.frequency: Optional[int] = frequency


class FileItem:

    def __init__(self, owner: str, subjects: List[str], access_list:
                 List[FileAccess], expiry: Optional[str]) -> None:
        self.owner: str = owner
        self.subjects: Dict[str, bool] = {}
        for subject in subjects:
            self.subjects[subject] = True
        self.expiry: Optional[datetime] = None if expiry is None else \
            datetime.strptime(expiry, "%Y-%m-%d")
        self.access: Dict[Tuple[str, Optional[str]], Tuple[Optional[int], bool]] = {}
        for access in access_list:
            self.access[access.user, access.country] = \
                (access.frequency, access.access_type)

    def delete_subject(self, subject: str):
        if subject in self.subjects:
            self.subjects[subject] = False
            return True
        else:
            return False

    def dsr(self):
        return [('"' + subject + '"') for subject in self.subjects.keys()
                if not self.subjects[subject]]

    def check_access(self, user_id, location) -> Tuple[Optional[bool], str]:

        if (self.expiry is not None) and (datetime.now() > self.expiry):
            return None, "File expired"

        key1: Tuple[str, Optional[str]] = (user_id, location)
        key2: Tuple[str, Optional[str]] = (user_id, None)
        key = None
        if key1 in self.access:
            key = key1
        if key2 in self.access:
            key = key2

        if key is None:
            return None, "Not authorized"

        access: Tuple[int, bool] = self.access[key]
        if access[0] is None:
            return access[1], ""
        assert access[0] >= 0
        if access[0] == 0:
            return None, "Access frequency expired"
        self.access[key] = (access[0] - 1, access[1])
        return access[1], ""

    def remove_user(self, user_id: str, location: Optional[str]) -> bool:

        if location is None:
            keys: List[Tuple[str, str]] = [key for key in self.access.keys()
                                           if key[0] == user_id]
            if len(keys) == 0:
                return False
            for key in keys:
                del self.access[key]
            return True

        key: Tuple[str, str] = (user_id, location)
        if key in self.access:
            del self.access[key]
            return True
        return False

    def remove_all_users(self):
        self.access = {}

    def remove_subject(self, subject: str) -> Optional[bool]:
        if not (subject in self.subjects):
            return None
        status: bool = self.subjects[subject]
        if not status:
            del self.subjects[subject]
        return status

    def dictionary(self) -> Dict:
        result = {"owner": self.owner}
        if self.expiry is not None:
            result["expiry"] = str(self.expiry.strftime("%Y-%m-%d"))

        def subject_dict(sbj: str) -> Dict:
            return {"subject": sbj, "status": self.subjects[sbj]}

        def access_dict(key: Tuple[str, str], value: Tuple[Optional[int], bool]):
            r: Dict = {"user": key[0], "type": value[1] }
            if key[1] is not None:
                r["country"] = key[1]
            if value[0] is not None:
                r["frequency"] = value[0]
            return r

        result["subjects"] = [subject_dict(subject)
                              for subject in self.subjects.keys()]

        result["access"] = [access_dict(access, self.access[access])
                            for access in self.access]
        return result


class Users:

    def __init__(self) -> None:
        self.users: Dict[str, str] = {"nikhil": "barthwal", "ashish": "shukla",
                                      "pranay": "singh", "nino": "acuna",
                                      "admin": "password", "jajati": "secret"}

    def check_user(self, user: str) -> bool:
        return user in self.users

    def authenticate(self, user: str, password: str) -> bool:
        return self.users[user] == password
