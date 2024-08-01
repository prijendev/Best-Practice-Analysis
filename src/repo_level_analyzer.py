from utils.constants import (
    REPO_LEVEL_PRACTICE_EVALUATION_PROMPT,
    LOG_FILE_PATH,
    AI71_BASE_URL,
    MODEL_NAME
)
from ast import literal_eval
from utils.utilities import extract_list_of_lists
from utils.logger_manager import CustomLogger
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import json


class RepoLevelAnalyzer:
    def __init__(self, directory_structure, frameworks, best_practices):
        self.directory_structure = directory_structure
        self.frameworks = frameworks
        self.best_practices = best_practices
        self.logger = CustomLogger(LOG_FILE_PATH).get_logger()

    def execute_analyze(self):
        final_response = ""
        frameworks = f"the frameworks '{self.frameworks}'" if self.frameworks else ""
        
        try:
            model = ChatOpenAI(
                temperature = 0, 
                model_name = MODEL_NAME, 
                base_url=AI71_BASE_URL
            )
            prompt_template = PromptTemplate(
                template=REPO_LEVEL_PRACTICE_EVALUATION_PROMPT,
                input_variables=["best_practices", "directory_structure", "frameworks"],
            )
            chain = prompt_template | model
            result = chain.invoke(
                {
                    "best_practices": self.best_practices, 
                    "directory_structure": self.directory_structure, 
                    "frameworks": frameworks,
                }
            )
            final_response = self.format_output(result.content)
        except ValueError as e:
            raise ValueError(f"Analysis failed due to an unexpected error: {str(e)}")
        except Exception as e:
            self.logger.error(f"Analysis failed due to an unexpected error: {e}")
        self.logger.info("Repo Level Analysis completed.")
        return final_response

    def format_output(self, response):
        try:
            response = extract_list_of_lists(response)
        except ValueError as e:
            raise ValueError(
                f"Failed to parse the response into a structured format: {str(e)}"
            )

        formatted_output = {}
        for best_practice, res in zip(self.best_practices, response):
            for key, details in best_practice.items():
                formatted_output[key] = [
                    {
                        "status": res[0] if res else None,
                        "suggestion": res[1] if len(res) > 1 and res[1] else None,
                    }
                ]
        return formatted_output
