import os

from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_community.document_loaders import WebBaseLoader
from langchain_openai import ChatOpenAI, OpenAIEmbeddings

from utils.logger_manager import CustomLogger
from utils.constants import (
    INDEX_FOLDER_PATH,
    EMBEDING_MODEL,
    DOCUMENTATION_SPLIT_MODEL,
    DOCUMENTATION_CHUNK_OVERLAP,
    DOCUMENTATION_CHUNK_TOKEN_LIMIT,
    DOCUMENTATION_VECTOR_DB_NAME,
    SCHEDULAR_LOG_FILE_PATH,
    MODEL_NAME,
    AI71_BASE_URL,
    SYSTEM_PROMPT,
    SYSTEM_PROMPT
)

URL = [
    "https://ibmsecuritydocs.github.io/qradar_appfw_v2/docs/tutorials/adding_csrf_protection.html"
]

class DocumentationDB:

    def __init__(self, index_name=DOCUMENTATION_VECTOR_DB_NAME):
        self.logger = CustomLogger(SCHEDULAR_LOG_FILE_PATH).get_logger()
        self.index_folder_path = os.path.join(INDEX_FOLDER_PATH, index_name)
        self.embedding = OpenAIEmbeddings(model= EMBEDING_MODEL, dimensions= 768)
        self.db = self.get_db() 
        if self.db is not None:
            self.db.save_local(self.index_folder_path)

    def get_db(self):
        self.logger.info("Documentation DB already exists")
        if os.path.isdir(self.index_folder_path):
            return FAISS.load_local(
                self.index_folder_path,
                self.embedding,
                allow_dangerous_deserialization=True,
            )
        else:
            if not len(URL):
                raise Exception("No URL provided")
            loader = WebBaseLoader(URL)
            all_documents = loader.load()
            text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
                model_name=DOCUMENTATION_SPLIT_MODEL,
                chunk_size=DOCUMENTATION_CHUNK_TOKEN_LIMIT,
                chunk_overlap=DOCUMENTATION_CHUNK_OVERLAP,
            )
            all_documents = text_splitter.split_documents(all_documents)
            return FAISS.from_documents(all_documents, self.embedding)

    def query(self, query_string):
        db_instance = self.db
        if db_instance is None:
            raise Exception(f"Vector Database: {self.index_folder_path}, does not exists")
        retriever = db_instance.as_retriever()
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", SYSTEM_PROMPT),
                ("human", "{input}"),
            ]
        )
        model = ChatOpenAI(
            temperature = 0, 
            model_name = MODEL_NAME,
            base_url=AI71_BASE_URL
        )
        question_answer = create_stuff_documents_chain(model, prompt)
        chain = create_retrieval_chain(retriever, question_answer)

        solution = ""
        try:
            self.logger.info(f"Querying in vector db for: {query_string}")
            for chunk in chain.stream({"input": query_string}):
                resp = chunk.get("answer")
                if resp:
                    solution += resp
        except Exception as e:
            self.logger.error(str(e))
        return solution