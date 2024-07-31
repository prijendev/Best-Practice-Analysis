import json
import os
from code_loader import CodeLoader
from practice_loader import PracticeLoader
from file_filter import FileFilter
from keyword_generator import KwGenerator
from utils.utilities import (
    get_code_related_practices,
)
from dotenv import load_dotenv
load_dotenv()


def run(repo_link, best_practices_doc_link):

    code_loader = CodeLoader(
        code_link=repo_link,
        username="",
        password="",
    )

    code_files = code_loader.load_code_files()
    project_frameworks = code_loader.get_project_framework()
    practice_loader = PracticeLoader(
        best_practices_doc_link, project_frameworks, os.getenv("username"), os.getenv("password")
    )

    practice_dict_list = practice_loader.process_best_practices()
    code_related_practices = get_code_related_practices(
        practice_dict_list, "is_repo_level", False
    )

    generator = KwGenerator(code_related_practices, project_frameworks)
    best_practices_with_keywords = generator.get_practices_with_keywords()

    filter = FileFilter(code_files, best_practices_with_keywords)
    files = filter.read_files()
    res = json.load(open("test/res.json","r"))
    return res

if __name__ == "__main__":
    run("github link", "best practice doc link")
