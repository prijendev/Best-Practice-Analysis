import glob
import os
import json
from ast import literal_eval
from collections import defaultdict
from urllib.parse import urlparse
import shutil

from utils.constants import (
    LOG_FOLDER_PATH,
    DB_FOLDER_PATH,
    LOG_FILE_PATH,
    # REPORT_FOLDER_PATH,
)
from utils.logger_manager import CustomLogger


def create_folders_if_not_exist():
    """Create the log and db folders if they don't exist."""
    if not os.path.isdir(LOG_FOLDER_PATH):
        os.mkdir(LOG_FOLDER_PATH)

    if not os.path.isdir(DB_FOLDER_PATH):
        os.mkdir(DB_FOLDER_PATH)


create_folders_if_not_exist()

logger = CustomLogger(LOG_FILE_PATH).get_logger()


def read_file(file_path):
    """Reads the file content

    params:
        - file_path

    return:
        - str : File content
    """
    logger.info("Reading file: " + file_path)
    with open(file_path, "r", encoding="utf-8") as f:
        file_content = f.read()
    return file_content


def read_directory_tree(code_directory_link: str):
    """Reads the directory tree"""
    logger.info("Reading directory tree: " + code_directory_link)
    all_files = []
    for root, _, files in os.walk(code_directory_link):
        for file in files:
            if file.endswith(".py"):
                all_files.append(os.path.join(root, file))
    return all_files


def trim(response: str) -> str:
    """Function to extract JSON string from
    a string

    params:
        - response

    return:
        - str : JSON string
    """

    try:
        logger.info("Starting trimming response")
        first_occurrence = response.index("{")
        last_occurrence = response.rindex("}")
        if last_occurrence < first_occurrence:
            return "{}"
        return response[first_occurrence : last_occurrence + 1]
    except Exception as e:
        print(e)
        return "{}"


def extract_keywords_list(response: str) -> str:
    try:
        first_occurrence = response.index("[")
        last_occurrence = response.rindex("]")
        if last_occurrence < first_occurrence:
            return "[]"
        return response[first_occurrence : last_occurrence + 1]
    except Exception as e:
        print(e)
        return "[]"


def extract_json(text: str) -> dict:
    """Function to extract JSON object from
    a string

    params:
        - text

    return:
        - dict[str, str] : Extracted JSON object
    """
    logger.info("Starting JSON extraction")
    extracted_text = trim(text)
    return json.loads(extracted_text)


def get_all_best_practices_statements():
    return {}


def extract_list(resp):
    """
    Extracts the list representation from the given text.

    Parameters:
        resp (str): The text from which the list needs to be extracted.

    Returns:
        list: The list representation found in the text.

    Raises:
        ValueError: If no list representation is found in the text.
    """
    # Find the indices of the first and last occurrence of '[' and ']' respectively
    first_occurrence = resp.index("[")
    last_occurrence = resp.rindex("]")

    # If there is no list representation in the text, return an empty list
    if last_occurrence < first_occurrence:
        return []

    # Extract the list representation from the text and evaluate it to a Python object
    return eval(resp[first_occurrence : last_occurrence + 1])


def extract_list_of_lists(string_repr):
    # Safely evaluate the string to a Python object
    list_of_lists = literal_eval(string_repr)
    # Check if the result is indeed a list of lists
    if all(isinstance(lst, list) for lst in list_of_lists):
        return list_of_lists
    else:
        raise ValueError("The string does not represent a list of lists")


def _extract_base_url(url):
    """
    Extracts the full domain from a given URL.

    Parameters:
        url (str): The URL from which to extract the full domain.

    Returns:
        str: The full domain extracted from the URL.
    """
    parsed_url = urlparse(url)

    full_domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
    return full_domain


def get_code_related_practices(processed_best_practice_dict_list, filter_key, filter_value):
    code_level_best_practices = []
    for key, best_practice_details in processed_best_practice_dict_list.items():
        if best_practice_details.get(filter_key) == filter_value:
            code_level_best_practices.append({key: best_practice_details})
    return code_level_best_practices

def find_file_paths(root_directory, file_names):
    file_paths = []
    for file_name in file_names:
        # Search for files with the given name in all subdirectories of the root directory
        search_pattern = os.path.join(root_directory, "**", file_name)
        # glob.glob returns a list of path names that match search_pattern
        found_paths = glob.glob(search_pattern, recursive=True)
        file_paths.extend(found_paths)
    return file_paths


def create_output_dict(value):
    return {
        "status": value[0] if value else None,
        "code": value[1] if len(value) > 1 and value[1] else None,
        "suggestion": value[2] if len(value) > 2 and value[2] else None,
    }


def generate_final_response(code_level_response, processed_best_practice_dict_list):
    final_response = defaultdict(dict)
    for file_path, final_details in code_level_response.items():
        for keyword in final_details.keys():
            final_response[file_path][
                processed_best_practice_dict_list[keyword]["statement"]
            ] = final_details[keyword]

    return final_response


def extract_repo_name(url):
    url = url.rstrip("/")
    parsed_url = urlparse(url)
    path_parts = parsed_url.path.split("/")
    repo_name = path_parts[-1].replace(".git", "")
    return repo_name


def ignore_style_css(dir, files):
    return ["style.css"]  # Specify the file you want to ignore here


def copy_ui_directory(source_dir, destination_dir):

    if os.path.exists(os.path.join(destination_dir, "index.html")) and os.path.exists(
        os.path.join(destination_dir, "main.js")
    ):
        return

    try:
        shutil.copytree(
            source_dir, destination_dir, ignore=ignore_style_css, dirs_exist_ok=True
        )
    except Exception as e:
        logger.error(f"Error while copying UI folder into directory :{e}")


# def make_reports_dirs(repo_name):
#     try:
#         if not os.path.exists(REPORT_FOLDER_PATH):
#             os.makedirs(REPORT_FOLDER_PATH)

#         directory_path = f"{REPORT_FOLDER_PATH}/{repo_name}"
#         if os.path.exists(directory_path):
#             return directory_path
#         else:
#             os.makedirs(directory_path, exist_ok=True)
#             return directory_path

#     except Exception as e:
#         logger.error(
#             f"Error while creating the folder : {repo_name} in Reports directory :{e}"
#         )


def store_json_output(directory_path, analysis_response):
    try:
        with open(f"{directory_path}/data.json", "w") as json_file:
            json.dump(analysis_response, json_file, indent=4)
    except Exception as e:
        print(
            f"An error occurred while writing to the JSON file for report generation: {e}"
        )

def filter_best_practices(processed_best_practice_dict_list, filter_key, filter_value):
    filter_best_practices = []
    for key, best_practice_deta in processed_best_practice_dict_list.items():
        if best_practice_deta.get(filter_key) == filter_value:
            filter_best_practices.append({key: best_practice_deta})
    return filter_best_practices