from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

from knowledge_db import DB
from utils.logger_manager import CustomLogger
from utils.constants import AI71_BASE_URL, IGNORE_CHARS, LOG_FILE_PATH,KEYWORD_PROMPT


class KwGenerator:

    def __init__(self, best_practices_dict, framework):
        self.practices_dict_list = best_practices_dict
        self.framework = framework
        self.logger = CustomLogger(LOG_FILE_PATH).get_logger()

    def clean_keyword(self, keyword):
        strip_chars = "".join(IGNORE_CHARS)
        return keyword.strip(strip_chars)

    def generate_keywords(self, practice):
        try:
            llm = ChatOpenAI(
                model="tiiuae/falcon-180B-chat",
                base_url=AI71_BASE_URL,
            )
            prompt_template = PromptTemplate(
                template=KEYWORD_PROMPT,
                input_variables=["framework", "best_practices"],
            )

            chain = prompt_template | llm

            res = chain.invoke(
                {
                    "framework": self.framework,
                    "best_practices": practice,
                }
            ).content

            keywords = res[1:-1].split(",")
            cleaned_keywords = [self.clean_keyword(k) for k in keywords]
            return cleaned_keywords
        except Exception as e:
            self.logger.error(f"Failed to generate keywords: {e}")
            return []

    def get_practices_with_keywords(self):
        for practice_dict in self.practices_dict_list:
            for _, details in practice_dict.items():
                practice = details["statement"]
                keywords = self.get_keywords(practice)
                details["keywords"] = keywords
        return self.practices_dict_list

    def get_keywords(self, best_practice: str):
        # fetch_or_generate_keywords

        db = DB()
        keywords = db.get_keywords(best_practice)
        self.logger.info(f"Fetched keywords for best practice : {best_practice}")

        if not keywords:
            keywords = self.generate_keywords(best_practice)
            db.add_practice(best_practice, keywords)
            self.logger.info(f"Stored keywords for best practice : {best_practice}")
        return keywords
