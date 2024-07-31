import os
import re
import tempfile
import subprocess
import fnmatch
import stat
import shutil
from urllib.parse import urlparse
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from utils.constants import (
    FILE_EXTENSIONS,
    MODEL_NAME,
    AI71_BASE_URL,
    FIND_FRAMEWORK_PROMPT
)



class CodeLoader:
    def __init__(
        self, code_link, username, password
    ):
        self.code_link = code_link
        self.username = username
        self.password = password
        self.is_clone = False

    def load_code_files(self):
        try:
            if os.path.exists(self.code_link):
                return self.get_all_files()
            else:
                return self.clone_repo()
        except Exception as err:
            # self.logger.error(err)
            print(err)

    def clone_repo(self):
        temp_dir_path = tempfile.mkdtemp()
        try:
            parse_url = urlparse(self.code_link)
            auth_url = f"{parse_url.scheme}://{self.username}:{self.password}@{parse_url.netloc}{parse_url.path}"


            clone_command = (
                ["git", "clone"] +  [auth_url, temp_dir_path]
            )

            subprocess.run(
                clone_command,
                check=True,
                capture_output=True,
                text=True,
            )

            self.code_link = temp_dir_path
            self.is_clone = True
            return self.get_all_files()
        except Exception as err:
            # self.logger.error(err)
            print(err)

    def get_all_files(self):
        try:
            all_files = []
            for root, _, files in os.walk(self.code_link):
                for file in files:
                    if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                        all_files.append(os.path.join(root, file))
            return all_files

        except Exception as err:
            print(err)
            # self.logger.error(err)

    def create_project_structure(self, folder_url, indentation_level=0):
        project_structure = ""
        for item in os.listdir(folder_url):
            if not item.startswith("."):
                full_path: str = os.path.join(folder_url, item)
                if os.path.isdir(full_path):
                    project_structure += "  " * indentation_level + f"/{item}\n"
                    project_structure += self.create_project_structure(
                        full_path, indentation_level + 1
                    )
                else:
                    project_structure += "  " * indentation_level + f"|-- {item}\n"
        return project_structure

    def get_project_framework(self):
        project_structure = self.create_project_structure(self.code_link)

        model = ChatOpenAI(
            model=MODEL_NAME,
            base_url=AI71_BASE_URL,
            streaming=True,
        )
        prompt_template = PromptTemplate(
            template=FIND_FRAMEWORK_PROMPT,
            input_variables=["project_structure"],
        )

        chain = prompt_template | model
        return chain.invoke({"project_structure": project_structure}).content

    def on_rm_error(self, func, path, exc_info):
        os.chmod(path, stat.S_IWRITE)
        os.unlink(path)

    def delete_folder(self):
        if self.is_clone:
            try:
                shutil.rmtree(self.code_link, onerror=self.on_rm_error)
            except Exception as e:
                raise e
