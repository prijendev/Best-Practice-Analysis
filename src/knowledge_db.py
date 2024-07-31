from sqlite import SQLite
from utils.logger_manager import CustomLogger
from utils.constants import (
    LOG_FILE_PATH,
    SQLITE_KEYWORD_TABLE_NAME,
    SQLITE_FILE_TABLE_NAME,
    SQLITE_DB_NAME,
)


class DB:

    def __init__(
        self,
        sqlite_db_name=SQLITE_DB_NAME,
        sqlite_keyword_table_name=SQLITE_KEYWORD_TABLE_NAME,
        sqlite_file_table_name=SQLITE_FILE_TABLE_NAME,
    ):
        self.sqlite = SQLite(
            sqlite_db_name, sqlite_keyword_table_name, sqlite_file_table_name
        )
        self.logger = CustomLogger(LOG_FILE_PATH).get_logger()

    def add_practice(self, best_practice, keywords):
        try:
            self.sqlite.insert_best_practice(best_practice, keywords)
            self.logger.info(
                f"Inserted best practice '{best_practice}' into knowledge store"
            )
        except Exception as e:
            self.logger.error(
                f"Error while inserting best practice '{best_practice}' into knowledge store: {str(e)}"
            )

    def insert_file(self, file_code, best_practice, response):
        try:
            self.logger.info(
                f"Inserting file with best practice '{best_practice}' into knowledge store"
            )
            self.sqlite.insert_file(file_code, best_practice, response)
        except Exception as e:
            self.logger.error(
                f"Error while inserting file response with best practice '{best_practice}' into knowledge store: {str(e)}"
            )

    def query_file(self, file_code, best_practice):
        try:
            self.logger.info(
                "Querying knowledge store for response of file and best practice"
            )
            res = self.sqlite.query_file(file_code, best_practice)
            return res
        except Exception as e:
            self.logger.error(
                f"Error while querying knowledge store for response of file with best practice '{best_practice}': {str(e)}"
            )

    def get_keywords(self, best_practice):
        try:
            keywords = self.sqlite.get_keywords(best_practice)
            if keywords:
                self.logger.info(f"Found keywords in SQLITE: {best_practice}")
                return keywords
            return keywords
        except Exception as e:
            self.logger.error(
                f"Error while querying keywords of best practice '{best_practice}' in knowledge store: {str(e)}"
            )
