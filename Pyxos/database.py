import config
import logging
import sqlite3


logging.basicConfig(
    format='%(levelname)s %(asctime)s: %(message)s', level=logging.DEBUG)


class Database:

    def __init__(self) -> None:
        self.conn = sqlite3.connect(config.database_file, check_same_thread=False)
        logging.info("Connected to SQLite")
        self.cursor = self.conn.cursor()

    def close(self):
        self.cursor.close()
        self.conn.close()

    def debug(self):
        logging.info(f"Checking all the tables ...")
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        result = self.cursor.fetchall()
        for r in result:
            table = str(r[0])
            logging.info(f" *** Showing table {table} ***")
            self.cursor.execute(f"SELECT * FROM {table};")
            for result in self.cursor.fetchall():
                logging.info(result)

    def check(self, table: str, condition: str):
        self.cursor.execute(f"SELECT COUNT(*) FROM {table} WHERE {condition};")
        count = int(self.cursor.fetchone()[0])
        assert count < 2
        result = count == 1
        if result:
            logging.info(f"verifying {condition} exists")
            return True
        logging.info(f"verifying {condition} does not exists")
        return False

    def create_file(self, file_id, owner: str):
        self.cursor.execute(f"""INSERT INTO {config.ownership_table} (file_id,
                                owner_id) VALUES ('{file_id}', '{owner}')""")
        self.conn.commit()

    def add_subject(self, file_id, subject_id: str):
        self.cursor.execute(f"""INSERT INTO {config.dsr_table}
            (subject_id, file_id, persist) VALUES
            ('{subject_id}', '{file_id}', 'TRUE');""")
        self.conn.commit()

    def add_access(self, user_id: str, file_id: str, location: str, access: str):
        self.cursor.execute(f"""INSERT INTO {config.access_table}
            (user_id, file_id, location, access) VALUES
            ('{user_id}', '{file_id}', '{location}', '{access}');""")
        self.conn.commit()

    def check_access(self, file_id: str, user_id: str, location: str):
        self.cursor.execute(f"""SELECT access FROM {config.access_table}
            WHERE file_id = '{file_id}' AND user_id = '{user_id}'
            AND location = '{location}';""")
        result = self.cursor.fetchone()
        if result is None:
            return None
        outcome = result[0]
        return outcome == 'TRUE'

    def get_owner(self, file_id):
        self.cursor.execute(f"""SELECT user_id FROM {config.ownership_table}
                                WHERE file_id = '{file_id}';""")
        # count = str(self.cursor.fetchone()[0])
        # assert count < 2
        # result = count == 1
        logging.debug(f"78 -> {self.cursor.fetchone()}")
        return ""
        # count = str(self.cursor.fetchone()[0])
        # assert count < 2
        # result = count == 1
        # if result:
        #    logging.info(f"verifying {user} exists")
        #    return True
        # logging.info(f"verifying {user} does not exists")
        # return False

    def check_user(self, user):
        self.cursor.execute(
            f"SELECT COUNT(*) FROM {config.user_table} WHERE user_id = '{user}';")
        count = int(self.cursor.fetchone()[0])
        assert count < 2
        result = count == 1
        if result:
            logging.info(f"verifying user = {user} exists")
            return True
        logging.info(f"verifying user = {user} does not exists")
        return False

    def check_file(self, file_id):
        self.cursor.execute(f"SELECT COUNT(*) FROM {config.ownership_table} " +
                            f"WHERE file_id = '{file_id}';")
        count = int(self.cursor.fetchone()[0])
        assert count < 2
        result = count == 1
        if result:
            logging.info(f"verifying file id = {file_id} exists")
            return True
        logging.info(f"verifying file id = {file_id} does not exists")
        return False

    def delete_subject(self, subject_id):
        self.cursor.execute(f"""UPDATE {config.dsr_table} SET persiste = FALSE
                                WHERE subject_id = '{subject_id}';""")
        logging.info(f"Marking persistance for subject = {subject_id} as false")

    def authenticate(self, user, password):
        self.cursor.execute(f"""SELECT COUNT(*) FROM {config.user_table} WHERE
                                user_id = '{user}' AND password = '{password}';""")
        count = int(self.cursor.fetchone()[0])
        assert count < 2
        result = count == 1
        if result:
            logging.info(f"successfully authenticated {user}")
            return True
        logging.info(f"failed to authenticate {user}")
        return False

    def acknowledge_dsr(self, file_id, subject_id):
        self.cursor.execute(f"""SELECT persist FROM {config.dsr_table} WHERE
                        subject_id = '{subject_id}' AND file_id = '{file_id}';""")
        print(self.cursor.fetchone())
        count = 0
        assert count < 2
        result = count == 1
        if result:
            logging.info(f"successfully authenticated {file_id}")
            return True
        logging.info(f"failed to authenticate {file_id}")
        return False

    def delete(self):
        for table in [config.ownership_table, config.access_table,
                      config.dsr_table, config.user_table]:
            logging.info(f"Deleting table {table}")
            self.cursor.execute(f"DROP TABLE {table};")
