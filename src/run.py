import json
import os
from code_loader import CodeLoader
from practice_loader import PracticeLoader
from file_filter import FileFilter
from keyword_generator import KwGenerator
from utils.utilities import (
    get_code_related_practices,
    filter_best_practices,
    generate_final_response
)
from code_level_analyzer import CodeAnalyzer
from repo_level_analyzer import RepoLevelAnalyzer
from dotenv import load_dotenv
load_dotenv()


def run(repo_link, best_practices_doc_link,username,password):
    try:
        code_loader = CodeLoader(
            code_link=repo_link,
            username="",
            password="",
        )

        code_files = code_loader.load_code_files()
        project_frameworks = code_loader.get_project_framework()
        practice_loader = PracticeLoader(
            best_practices_doc_link, project_frameworks, username, password
        )

        practice_dict_list = practice_loader.process_best_practices()
        code_related_practices = get_code_related_practices(
            practice_dict_list, "is_repo_level", False
        )

        generator = KwGenerator(code_related_practices, project_frameworks)
        best_practices_with_keywords = generator.get_practices_with_keywords()

        filter = FileFilter(code_files, best_practices_with_keywords)
        files = filter.read_files()

        code_level_response = CodeAnalyzer(
            project_frameworks, files, practice_dict_list
        ).execute_file_analyze()

        repo_best_practices = filter_best_practices(
            practice_dict_list, "is_repo_level", True
        )
        repo_level_response = RepoLevelAnalyzer(
            code_loader.project_structure,
            project_frameworks,
            repo_best_practices,
        ).execute_analyze()
        if repo_level_response:
            code_level_response[code_loader.code_link] = (
                repo_level_response
            )
        
        final_response = generate_final_response(
            code_level_response,
            practice_dict_list,
        )
        print(final_response)
        return final_response
    except (
        ValueError,
        Exception,
    ) as error:
        raise error
    finally:
        # Cleanup
        code_loader.delete_folder()

if __name__ == "__main__":
    run("github link", "best practice doc link", "username", "password")
