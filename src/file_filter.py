from fuzzywuzzy import fuzz
from collections import defaultdict

from utils.logger_manager import CustomLogger
from utils.constants import (
    LOG_FILE_PATH,
    SIMILARITY_SEARCH_THRESHOLD,
)
from utils.utilities import read_file


class FileFilter:

    def __init__(self, files, practice_dict_list):
        self.files = files
        self.practice_dict_list = practice_dict_list
        self.filtered_files = defaultdict(list)
        self.logger = CustomLogger(LOG_FILE_PATH).get_logger()

    def similarity_search(self, path, content):
        for practice_dict in self.practice_dict_list:
            for key, practice in practice_dict.items():
                for keyword in practice["keywords"]:
                    if (
                        fuzz.token_set_ratio(content, keyword)
                        >= SIMILARITY_SEARCH_THRESHOLD
                    ):
                        self.filtered_files[path].append(
                            f"{practice["statement"]}\n[keyword_name: {key}]"
                        )
                        break

    def read_files(self):
        for file in self.files:
            try:
                content = read_file(file)
                self.similarity_search(file, content)
                self.logger.info("Filtered files.")
            except Exception as e:
                self.logger.error(f"Error while reading file: {file}: {str(e)}")
        return self.filtered_files
