import sqlite3
import json
import hashlib
from datetime import datetime

from utils.logger_manager import CustomLogger
from utils.constants import (
    LOG_FILE_PATH,
    SQLITE_KEYWORD_TABLE_NAME,
    SQLITE_FILE_TABLE_NAME,
    SQLITE_DB_NAME,
    IGNORE_CHARS,
)


class SQLite:
    def __init__(
        self,
        db_name=SQLITE_DB_NAME,
        keyword_table_name=SQLITE_KEYWORD_TABLE_NAME,
        file_table_name=SQLITE_FILE_TABLE_NAME,
    ):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.keyword_table_name = keyword_table_name
        self.file_table_name = file_table_name
        self.logger = CustomLogger(LOG_FILE_PATH).get_logger()
        self._create_table()

    def _create_hash(self, input):
        hasher = hashlib.sha256()
        hasher.update(input.encode("utf-8"))
        return hasher.hexdigest()

    def _create_table(self):
        try:
            self.logger.info("Creating SQLite tables if they do not exist")
            # Create keyword table if it does not exist
            create_keyword_table_query = (
                f"CREATE TABLE IF NOT EXISTS {self.keyword_table_name} ("
                "best_practice_hash TEXT PRIMARY KEY,"
                "keywords JSON,"
                "updated_by TEXT,"
                "updated_at DATETIME"
                ")"
            )
            # Create file table if it does not exist
            create_file_table_query = (
                f"CREATE TABLE IF NOT EXISTS {self.file_table_name}("
                "file_hash TEXT,"
                "best_practice_hash TEXT,"
                "response JSON,"
                "updated_by TEXT,"
                "updated_at DATETIME,"
                "PRIMARY KEY (file_hash, best_practice_hash)"
                ")"
            )
            self.conn.execute(create_keyword_table_query)
            self.conn.execute(create_file_table_query)
            self.conn.commit()
        except Exception as e:
            self.logger.error(f"Error while creating SQLite DB tables: {e}")
            raise

    def insert_best_practice(self, best_practice, keywords):
        try:
            self.logger.info(
                f"Inserting best practice '{best_practice}' in {self.keyword_table_name} table"
            )
            # Create hash for the best practice
            best_practice_hash = self._create_hash(self._clean_text(best_practice))

            # Insert best practice and its associated keywords into the table
            insert_query = (
                f"INSERT OR REPLACE INTO {self.keyword_table_name} "
                "(best_practice_hash, keywords, updated_by, updated_at) "
                "VALUES (?, ?, ?, ?)"
            )
            self.conn.execute(
                insert_query,
                (
                    best_practice_hash,
                    json.dumps(keywords),
                    "admin",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            self.conn.commit()
        except Exception as e:
            self.logger.error(
                f"Error while inserting best practice in SQLite table {self.keyword_table_name}: {e}"
            )
            raise

    def insert_file(self, file_code, best_practice, response):
        try:
            self.logger.info(
                f"Inserting file with the best practice '{best_practice}' into table {self.file_table_name}"
            )
            # Create hashes for the file code and best practice
            best_practice_hash = self._create_hash(self._clean_text(best_practice))
            file_hash = self._create_hash(self._clean_text(file_code))

            # Insert file and best practice hash into the table
            insert_query = f"INSERT OR REPLACE INTO {self.file_table_name} (file_hash, best_practice_hash, response, updated_by, updated_at) VALUES (?, ?, ?, ?, ?)"
            self.conn.execute(
                insert_query,
                (
                    file_hash,
                    best_practice_hash,
                    json.dumps(response),
                    "admin",
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            self.conn.commit()
        except Exception as e:
            self.logger.error(
                f"Error while inserting file entry in SQLite table {self.file_table_name}: {e}"
            )
            raise

    def query_file(self, file_code, best_practice):
        try:
            self.logger.info(
                f"Querying SQLite table '{self.file_table_name}' for response of file and best practice '{best_practice}'"
            )
            # Create hashes for the file code and best practice
            best_practice_hash = self._create_hash(self._clean_text(best_practice))
            file_hash = self._create_hash(self._clean_text(file_code))

            # Query the table for file response
            file_select_query = f"select * from {self.file_table_name} as ks where ks.file_hash = ? and ks.best_practice_hash = ?"
            res = self.conn.execute(
                file_select_query, (file_hash, best_practice_hash)
            ).fetchone()
            if res:
                return json.loads(res[2])
        except Exception as e:
            self.logger.error(
                f"Error while checking for file in SQLite table {self.file_table_name}: {e}"
            )
            raise

    def _clean_text(self, best_practice):
        for ch in IGNORE_CHARS:
            best_practice = best_practice.replace(ch, "")
        return best_practice

    def get_keywords(self, best_practice):
        try:
            self.logger.info(
                f"Querying keywords for best practice '{best_practice}' in SQLite table {self.keyword_table_name}"
            )
            # Create hash for the best practice
            best_practice_hash = self._create_hash(self._clean_text(best_practice))

            # Query the table for keywords
            best_practice_select_query = f"select * from {self.keyword_table_name} as ks where ks.best_practice_hash = ?"
            res = self.conn.execute(
                best_practice_select_query, (best_practice_hash,)
            ).fetchone()
            if res:
                return json.loads(res[1])
        except Exception as e:
            self.logger.error(
                f"Error while checking for keyword for best practice '{best_practice}' in SQLite table {self.keyword_table_name}: {e}"
            )
            raise

    def __del__(self):
        try:
            self.logger.info("Closing SQLite connection")
            self.conn.close()
        except Exception as e:
            self.logger.error(f"Error while closing SQLite connection: {e}")
