import config
import logging
import sqlite3
import os

logging.basicConfig(
    format='%(levelname)s %(asctime)s: %(message)s', level=logging.DEBUG)


def setup():
    if os.path.exists(config.database_file):
        logging.info(f"Delete old database file: {config.database_file}")
        os.remove(config.database_file)

    conn = sqlite3.connect(config.database_file, check_same_thread=False)
    cursor = conn.cursor()

    logging.info(f"Creating ownership table: {config.ownership_table}")
    cursor.execute(f"""CREATE TABLE {config.ownership_table} (
        file_id VARCHAR(50) NOT NULL, owner_id VARCHAR(50) NOT NULL);""")
    conn.commit()

    logging.info(f"Creating access table: {config.access_table}")
    cursor.execute(f"""CREATE TABLE {config.access_table} (
        user_id VARCHAR(50) NOT NULL,
        file_id VARCHAR(50) NOT NULL,
        location VARCHAR(50) NOT NULL,
        access BOOLEAN NOT NULL);""")
    conn.commit()

    logging.info(f"Creating dsr table: {config.dsr_table}")
    cursor.execute(f"""CREATE TABLE {config.dsr_table} (
        subject_id VARCHAR(50) NOT NULL,
        file_id VARCHAR(50) NOT NULL,
        persist BOOLEAN NOT NULL);""")
    conn.commit()

    logging.info(f"Creating user table: {config.user_table}")
    cursor.execute(f"""CREATE TABLE {config.user_table} (
        user_id VARCHAR(50) NOT NULL, password VARCHAR(50) NOT NULL); """)
    cursor.execute(f"""INSERT INTO users (user_id, password) VALUES
        ('nikhil', 'barthwal'),
        ('pranay', 'singh'),
        ('ashish', 'shukla'),
        ('nino', '"acuna'),
        ('{config.admin}', 'password');""")
    conn.commit()

    logging.info(f"Checking all the tables ...")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    logging.info(f"Tables: {str(cursor.fetchall())}")

    cursor.close()
    conn.close()


if __name__ == '__main__':
    setup()
