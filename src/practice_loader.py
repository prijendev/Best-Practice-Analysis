import os
import re
from bs4 import BeautifulSoup
from atlassian import Confluence
from langchain_core.runnables.config import ContextThreadPoolExecutor
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from utils.logger_manager import CustomLogger
from utils.constants import (
    AI71_BASE_URL,
    LOG_FILE_PATH,
    BEST_PRACTICE_PATTERN,
    STATEMENT_PATTERN,
    REFERENCE_PATTERN,
    KEYWORD_CHUNK_SIZE,
    MAX_WORKERS_FOR_KEYWORD_CHUNKING,
    BIFURCATION_PROMPT
)
from utils.exceptions import (
    InvalidLinkError,
    NoPracticeFoundError,
    BestPracticeProcessorError,
)
from utils.utilities import _extract_base_url, extract_list


class PracticeLoader:
    def __init__(self, practice_link, frameworks=None, username=None, password=None):
        self.logger = CustomLogger(LOG_FILE_PATH).get_logger()
        self.practice_link = practice_link
        self.frameworks = (
            f"Programming languages and Frameworks: {frameworks}\n"
            if frameworks
            else ""
        )
        self.auth_user = username 
        self.auth_pass = password

    def fetch_practices(self):
        if os.path.isfile(self.practice_link):
            raw_practice_data = self.read_file()
        else:
            raw_practice_data = self.read_confluence()
        self.logger.info(f"Successfully read best practices from: {self.practice_link}")

        return raw_practice_data

    def _make_chunks(self, practices, chunk_size=KEYWORD_CHUNK_SIZE):
        chunks = []
        for i in range(0, len(practices), chunk_size):
            chunks.append(practices[i : i + chunk_size])

        return chunks

    def _make_numbered_chunks(self, chunk):
        count = 1
        ans = ""
        for best_practice in chunk:
            ans += f"Best practice {count}. {best_practice['statement']}\n"
            count += 1
        return ans

    def process_chunk(self, chunk, all_keyword_practice_map):
        best_practices = self._make_numbered_chunks(chunk)

        processed_practices = self.process_best_practice(best_practices)
        if len(processed_practices) != len(chunk):
            raise BestPracticeProcessorError(
                "The number of processed best practices does not match the number of best practices."
            )
        keyword_practice_map = self.get_keyword_practice_map(processed_practices, chunk)

        all_keyword_practice_map.append(keyword_practice_map)

    def generate_unique_key(self, base_key, keyword_dict):
        while True:
            base_key += "_"
            if base_key not in keyword_dict:
                return base_key

    def process_best_practices(self):
        try:
            unprocessed_data = self.fetch_practices()

            best_practices_dict = self.parse_best_practices(unprocessed_data)

            executor = ContextThreadPoolExecutor(
                max_workers=MAX_WORKERS_FOR_KEYWORD_CHUNKING
            )

            chunks = self._make_chunks(best_practices_dict)
            final_mapping = []
            self.logger.info(f"Received {len(chunks)} chunks")
            for chunk in chunks:
                executor.submit(
                    self.process_chunk,
                    chunk,
                    final_mapping,
                )
            executor.shutdown(wait=True)
            if not final_mapping:
                return {}
            res = final_mapping[0]
            for i in range(1, len(final_mapping)):
                for k in final_mapping[i]:
                    if k in res:
                        new_k = self.generate_unique_key(k, res)
                        res[new_k] = final_mapping[i][k]
                    else:
                        res[k] = final_mapping[i][k]
            return res

        except (
            InvalidLinkError,
            NoPracticeFoundError,
            BestPracticeProcessorError,
            ValueError,
        ) as error:
            self.logger.error(str(error))
            raise error

    def read_file(self):
        content = ""
        with open(self.practice_link, "r") as file:
            content = file.read()
        return content

    def read_confluence(self):
        client = Confluence(
            url=_extract_base_url(self.practice_link),
            username=self.auth_user,
            password=self.auth_pass,
            verify_ssl=False,
        )
        match = re.match(r".*pageId=(\d+)", self.practice_link)
        if not match:
            raise ValueError(f"Invalid URL: {self.practice_link}")
        page_id = match.group(1)

        raw_content = client.get_page_by_id(
            page_id, "space,body.view,version,container"
        )
        parsed_content = BeautifulSoup(
            raw_content["body"]["view"]["value"], "html.parser"
        )
        text_content = parsed_content.get_text()

        return text_content

    def process_best_practice(self, raw_practice_data):
        processed_practices = []
        llm = ChatOpenAI(
            model="tiiuae/falcon-180B-chat",
            base_url=AI71_BASE_URL,
        )
        prompt_template = PromptTemplate(
            template=BIFURCATION_PROMPT,
            input_variables=["framework", "best_practices"],
        )

        chain = prompt_template | llm

        res = chain.invoke(
            {
                "framework": self.frameworks,
                "best_practices": raw_practice_data,
            }
        ).content

        processed_practices = extract_list(res)

        if not processed_practices:
            raise BestPracticeProcessorError("Best Practices Processing failed.")

        self.logger.info("Best Practices processed successfully.")

        return processed_practices

    def parse_best_practices(self, raw_practice_data):
        if not raw_practice_data:
            raise ValueError("best_practice_data must be a non-empty string.")

        practices = re.split(BEST_PRACTICE_PATTERN, raw_practice_data)

        if len(practices) < 2:
            raise NoPracticeFoundError("No best practices found.")

        practices = practices[1:]
        self.logger.info(f"Extracted {len(practices)} best practices.")
        parsed_practice_dict_list = self.extract_statement_reference(practices)

        return parsed_practice_dict_list

    def extract_statement_reference(self, practices):

        statement_regex = re.compile(STATEMENT_PATTERN, re.DOTALL)
        reference_regex = re.compile(REFERENCE_PATTERN, re.DOTALL)
        parsed_list = []

        for practice in practices:
            statement_match = statement_regex.search(practice)
            reference_match = reference_regex.search(practice)

            statement = (
                statement_match.group(1).strip()
                if statement_match
                else practice.strip()
            )
            reference = reference_match.group(1).strip() if reference_match else ""

            parsed_list.append({"statement": statement, "reference": reference})
        return parsed_list

    def get_keyword_practice_map(self, processed_practices, practices_dict):
        processed_practices_dict = {p["unique_keyword"]: p for p in processed_practices}

        keyword_practice_map = {
            processed_practices_dict[keyword]["unique_keyword"]: {
                "statement": practice["statement"],
                "reference": practice["reference"],
                "is_repo_level": processed_practices_dict[keyword]["repo_level"]
                == "Yes",
                "frameworks": processed_practices_dict[keyword].get(
                    "languages_frameworks", []
                ),
            }
            for keyword, practice in zip(
                processed_practices_dict.keys(), practices_dict
            )
        }

        return keyword_practice_map

    def add_keywords(self, keyword_practice_map):
        practices = []

        for count, (keyword, info) in enumerate(keyword_practice_map.items(), start=1):
            statement = info["statement"]
            keyword_str = f"{count}) {statement} \n[keyword_name: {keyword}]\n\n"
            practices.append(keyword_str)

        return practices
