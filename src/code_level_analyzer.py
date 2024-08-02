from concurrent.futures import as_completed
import re
from langchain_core.runnables.config import ContextThreadPoolExecutor
from langchain_community.vectorstores.faiss import FAISS
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from collections import defaultdict

from knowledge_db import DB
from doc_db import DocumentationDB
from utils.logger_manager import CustomLogger
from utils.utilities import extract_json, read_file, create_output_dict, extract_list
from utils.constants import (
    BEST_PRACTICES_CHUNK_SIZE,
    MAX_FILES_PROCESS_CONCURRENTLY,
    MAX_CHUNKS_PROCESS_CONCURRENTLY,
    LOG_FILE_PATH,
    FILE_THREAD_PREFIX,
    CHUNK_THREAD_PREFIX,
    STATEMENT_KEYWORD_PATTERN,
    CODE_LINES_CHUNK_SIZE,
    DOCUMENTATION_SPLIT_MODEL,
    DOCUMENTATION_CHUNK_OVERLAP,
    DOCUMENTATION_CHUNK_TOKEN_LIMIT,
    CODE_LEVEL_PROMPT,
    UNKNOWN_RESPONSE_PROMPT,
    SYSTEM_PROMPT,
    MODEL_NAME,
    EMBEDING_MODEL,
    AI71_BASE_URL
)

class CodeAnalyzer:

    def __init__(
        self, project_frameworks, file_practice_mapping, processed_best_practice_dict_list
    ):
        self.project_frameworks = project_frameworks
        self.file_practice_mapping = file_practice_mapping
        self.best_practice_keyword_dict = processed_best_practice_dict_list
        self.db_store = DB()
        self.logger = CustomLogger(LOG_FILE_PATH).get_logger()

    def split_file_by_code_lines_limit(self, input_file_path: str, allowed_lines_per_file: int):
        with open(input_file_path, "r") as file:
            lines = file.readlines()

        non_empty_lines = [line for line in lines if line.strip()]
        contents = []
        for i in range(0, len(non_empty_lines), allowed_lines_per_file):
            contents.append(non_empty_lines[i : i + allowed_lines_per_file])
        return contents

    def combine_chunk_responses(self, curr_response, processed_response):
        for kw in processed_response:
            if kw in curr_response:
                curr_response[STATEMENT_KEYWORD_PATTERN].extend(processed_response[kw])
            else:
                curr_response[kw] = processed_response[kw]

    def query_existing_data_in_knowledge_store(self, best_practices_list, file_path_str, old_responses):
        code = read_file(file_path_str)
        found_best_practice = []
        for best_practice in best_practices_list:
            try:
                found = re.search(STATEMENT_KEYWORD_PATTERN, best_practice, re.DOTALL)
                if found:
                    statement, keyword = found.groups()
                    statement = statement.strip()
                    keyword = keyword.strip()
                    res = self.db_store.query_file(code, statement)

                    if res:
                        if file_path_str not in old_responses:
                            old_responses[file_path_str] = {}
                        old_responses[file_path_str][keyword] = res
                        found_best_practice.append(best_practice)
                        self.logger.info(
                            f"Found exisitng response for {best_practice} in knowledge store"
                        )
            except Exception as e:
                self.logger.error(f"Error in querying knowledge store or response is not found in knowledge store: {str(e)}")

        remaining_best_practice = []
        for i in range(len(best_practices_list)):
            best_practice = best_practices_list[i]
            if best_practice not in found_best_practice:
                remaining_best_practice.append(best_practice)

        return remaining_best_practice

    def combine_responses_into_final_response(self, old_res, new_res):
        try:
            for file_path in new_res:
                if file_path not in old_res:
                    old_res[file_path] = {}
                old_res[file_path].update(new_res[file_path])

            final_response = {}
            for file_path in old_res:
                final_response[file_path] = {}
                for keyword in old_res[file_path]:
                    if not len(old_res[file_path][keyword]):
                        continue
                    all_violated_response = [
                        response
                        for response in old_res[file_path][keyword]
                        if response["status"].lower() == "violated"
                    ]
                    if len(all_violated_response):
                        final_response[file_path][keyword] = all_violated_response

            return final_response
        except Exception as e:
            self.logger.error(f"Error while combing old and new response: {str(e)}")
            return {}

    def execute_file_analyze(self):
        old_responses = {}
        final_response={}
        try:
            with ContextThreadPoolExecutor(
                max_workers=MAX_FILES_PROCESS_CONCURRENTLY,
                thread_name_prefix=FILE_THREAD_PREFIX,
            ) as executor:
                future_to_file = {}
                for file_path, best_practices in self.file_practice_mapping.items():
                    remaining_best_practices = self.query_existing_data_in_knowledge_store(
                        best_practices, file_path, old_responses
                    )
                    if not len(remaining_best_practices):
                        continue

                    all_chunks = self.split_file_by_code_lines_limit(file_path, CODE_LINES_CHUNK_SIZE)
                    for each_file_chunk in all_chunks:
                        future_to_file[
                            executor.submit(
                                self.analyze_file_chunk_concurrently,
                                each_file_chunk,
                                file_path,
                                remaining_best_practices,
                            )
                        ] = file_path
                unknown_handled_practices = []
                new_responses = {}
                for future in as_completed(future_to_file):
                    file_path = future_to_file[future]
                    try:
                        response = future.result()
                        if file_path not in new_responses:
                            new_responses[file_path] = {}
                        self.combine_chunk_responses(
                            new_responses[file_path], self._handle_unknown_responses(
                                response, file_path, unknown_handled_practices
                            )
                        )
                    except Exception as exc:
                        self.logger.error(
                            f"File analysis failed for {file_path}: {exc}"
                        )
            for file_path in new_responses:
                for best_practice_keyword in new_responses[file_path]:
                    try:
                        best_practice_statement = self.best_practice_keyword_dict[
                            best_practice_keyword
                        ]["statement"]
                        file_content = read_file(file_path)
                        self.db_store.insert_file(
                            file_content,
                            best_practice_statement,
                            new_responses[file_path][best_practice_keyword],
                        )
                    except Exception as e:
                        self.logger.error(
                            f"Error while storing {file_path} with best practice {best_practice_statement} in db store: {str(e)}"
                        )
            final_response = self.combine_responses_into_final_response(old_responses, new_responses)
        except Exception as e:
            self.logger.error(f"Threading failed: {e}")

        self.logger.info("Code level analysis completed.")
        return final_response

    def analyze_file_chunk_concurrently(self, file_chunk_str, file_path_str, best_practices_list):
        combined_data = {}
        try:
            with ContextThreadPoolExecutor(
                max_workers=MAX_CHUNKS_PROCESS_CONCURRENTLY,
                thread_name_prefix=CHUNK_THREAD_PREFIX,
            ) as executor:
                futures = [
                    executor.submit(self.analyze_chunk, file_chunk_str, file_path_str, chunk)
                    for chunk in self._chunk_best_practices(best_practices_list)
                ]
                for future in as_completed(futures):
                    try:
                        chunk_result = future.result()
                        combined_data.update(chunk_result)
                    except Exception as exc:
                        self.logger.error(
                            f"Chunk analysis failed for {file_path_str}: {exc}"
                        )
        except Exception as e:
            self.logger.error(f"Chunk thread pool setup failed for {file_path_str}: {e}")
        return combined_data

    def analyze_chunk(self, code_chunk, file_path, best_practice_chunk):
        try:
            final_res = {}
            model = ChatOpenAI(
                temperature = 0, 
                model_name = MODEL_NAME,
                base_url=AI71_BASE_URL
            )
            
            prompt_template = PromptTemplate(
                template=CODE_LEVEL_PROMPT,
                input_variables=["best_practices", "project_frameworks", "file_path", "code"],
            )
            chain = prompt_template | model
            result = chain.invoke(
                {
                    "best_practices": best_practice_chunk, 
                    "project_frameworks": self.project_frameworks, 
                    "file_path": file_path, 
                    "code": code_chunk
                }
            )
            res = self.format_output(result.content)
            final_res.update(res)
            self.logger.info(f"Chunk analysis completed for {file_path}")
            return final_res
        except Exception as e:
            self.logger.error(f"Chunk analysis failed and get exception for {file_path}: {e}")
            return {}

    def _chunk_best_practices(self, best_practices_list):
        return [
            best_practices_list[i : i + BEST_PRACTICES_CHUNK_SIZE]
            for i in range(0, len(best_practices_list), BEST_PRACTICES_CHUNK_SIZE)
        ]

    def format_output(self, res):
        formatted_res = {}
        try:
            res = extract_json(res)
            formatted_res = {
                key: self._process_output(value_list) for key, value_list in res.items()
            }
        except Exception as e:
            self.logger.error(f"Unable to format  output of LLM call: {e}")
        return formatted_res

    def _handle_unknown_responses(self, response, file_path, unknown_handled_practices):
        new_response = {}
        for keyword, values in response.items():
            if keyword not in new_response:
                new_response[keyword] = []
            for value in values:
                if (
                    value["status"] == "Unknown"
                    and [keyword, file_path] not in unknown_handled_practices
                ):
                    best_practice = self.best_practice_keyword_dict[keyword]
                    new_response[keyword].append(
                        self._handle_unknown_responses2(best_practice, file_path)
                    )
                    unknown_handled_practices.append([keyword, file_path])
                    self.logger.info(f"Handled unknown response for: {best_practice}")
                elif value["status"] != "Unknown":
                    new_response[keyword].append(value)
        return new_response

    def _get_best_practice_context(self, best_practice):
        loader = WebBaseLoader(best_practice["reference"])
        response_docs = loader.load()

        text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                model_name=DOCUMENTATION_SPLIT_MODEL,
                chunk_size=DOCUMENTATION_CHUNK_TOKEN_LIMIT,
                chunk_overlap=DOCUMENTATION_CHUNK_OVERLAP,
            )
        response_docs = text_splitter.split_documents(response_docs)

        embeddings = OpenAIEmbeddings(model= EMBEDING_MODEL, dimensions= 768)
        
        vector_store = FAISS.from_documents(response_docs, embeddings)
        retriever = vector_store.as_retriever()

        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "{input}"),
            ]
        )
        llm = ChatOpenAI(
            temperature = 0, 
            model_name = MODEL_NAME, 
            base_url=AI71_BASE_URL
        )
        question_answer_chain = create_stuff_documents_chain(llm, prompt)
        chain = create_retrieval_chain(retriever, question_answer_chain)
        solution = ""
        try:
            for chunk in chain.stream({"input": best_practice["statement"]}):
                resp = chunk.get("answer")
                if resp:
                    solution += resp
        except Exception as ex:
            self.logger.error(str(ex))
        return solution

    def _handle_unknown_responses2(self, best_practice,code_file):
        if not best_practice["reference"]:
            self.logger.info(
                f"Checking best_practice: {best_practice} in documentation db"
            )
            try:
                context = DocumentationDB().query(best_practice["statement"])
                self.logger.info("Got context from documentation db")
            except Exception as ex:
                self.logger.error(str(ex))
                return [{"status": "Skipped"}]
        else:
            context = self._get_best_practice_context(best_practice)

        self.logger.info(f"Splitting code_file: {code_file} for analyzing unknown response")
        all_chunks = self.split_file_by_code_lines_limit(code_file, 50)

        with ContextThreadPoolExecutor(
                max_workers=MAX_CHUNKS_PROCESS_CONCURRENTLY,
                thread_name_prefix=CHUNK_THREAD_PREFIX,
            ) as executor:
                futures = []
                for chunk in all_chunks:
                    futures.append(
                        executor.submit(self._handle_unknown_responses3, best_practice, context, chunk, code_file)
                    )
                combined_results = []
                for future in as_completed(futures):
                    try:
                        chunk_result = future.result()
                        combined_results.extend(chunk_result)
                    except Exception as exc:
                        self.logger.error(str(exc))
        return combined_results

    def _handle_unknown_responses3(self, best_practice, context, file_content, code_file):
        
        model = ChatOpenAI(
            temperature = 0, 
            model_name = MODEL_NAME, 
            base_url=AI71_BASE_URL
        )
        prompt_template = PromptTemplate(
            template=UNKNOWN_RESPONSE_PROMPT,
            input_variables=["file_path", "context", "code", "best_practice"],
        )
        chain = prompt_template | model
        response = chain.invoke(
            {
                "file_path": code_file,
                "context": context,
                "code": file_content,
                "best_practice": best_practice,
            }
        ).content
        try:
            response = extract_list(response)
            if not response or len(response) == 0:
                return [{"status": "Unknown"}]

            if isinstance(response, list) and len(response):
                if isinstance(response[0], str):
                    return [create_output_dict(response)]
                return self._process_output(response)
            return [{"status": "Unknown"}]

        except Exception as err:
            raise Exception("While parsing response to JSON: " + str(err))

    def _process_output(self, output_values):
        processed_output = [create_output_dict(value) for value in output_values]
        return processed_output