import os

CURRENT_DIRECTORY = os.getcwd()
LOG_FILE_TIME_FORMAT = "%d-%m-%Y"  # Time format for log file name
LOG_FOLDER_PATH = os.path.join(CURRENT_DIRECTORY, "logs")
LOG_FILE_PATH = os.path.join(LOG_FOLDER_PATH, "log.log")
FILE_EXTENSIONS = [".py"]
MODEL_NAME="tiiuae/falcon-180B-chat"
AI71_BASE_URL = "https://api.ai71.ai/v1/"
IGNORABLE_CHARACTERS = ["'", '"', " ", "`", "\n"]



BEST_PRACTICE_PATTERN = r"Practice \d+\."
STATEMENT_PATTERN = r"^(.*?)\n*Reference:"
REFERENCE_PATTERN = r"Reference: (.*)"


KEYWORD_CHUNK_SIZE = 20
MAX_WORKERS_FOR_KEYWORD_CHUNKING = 10


DB_FOLDER_PATH = os.path.join(CURRENT_DIRECTORY, "db")
SQLITE_DB_NAME = os.path.join(DB_FOLDER_PATH, "sqlite.db")
SQLITE_KEYWORD_TABLE_NAME = "Keyword_Knowledge_Store"
SQLITE_FILE_TABLE_NAME = "File_Knowledge_Store"


LOGGER_BACKUP_COUNT = 30  # Last number of days to keep log files
LOG_LEVEL = "INFO"  # Default log levels
TIMELY_LOGGER_INTERVAL = (
    "midnight"  # Interval like days, minutes, seconds, etc. for timely logger
)
LOG_FILE_TIME_FORMAT = "%d-%m-%Y"


SIMILARITY_SEARCH_THRESHOLD = 65

IGNORE_CHARS = ["'", '"', " ", "`", "\n"]

REPO_LEVEL_PROMPT = """You are an expert code reviewer.Given {frameworks} the project structure provided below.please analyze it.
Project Structure:
{directory_structure}

Best Practices to Evaluate: {best_practices}
Check for all best practices one by one.
You have to first analyze structure and then evaluate best practice.
Check whether given best practice violated or not based on given project structure.
Your response must be in following  format:
{{
    best_practice_keyword: ["Violated/Not Violated","suggested solution"],
    best_practice_keyword: ["Violated/Not Violated","suggested solution"],
    best_practice_keyword: ["Violated/Not Violated","suggested solution"],
    ...
}}
Your response must not contain any other text.
In response only json is there no other text.
"""

FIND_FRAMEWORK_PROMPT = """You are an expert software engineer who has knowledge in web frameworks.

directory structure:
{project_structure}

Analyze the provided directory structure, filenames, and file extensions to determine the primary web frameworks or programming language used in the project. More specifically, Focus on Python, Java, and JavaScript frameworks.(Example : 'Django', 'Flask', 'Spring')

If you determine more than two frameworks then only two most accurate frameworks for this project should be returned by you. If you cannot determine the framework based on provide directory structure, return empty list else follow the below format for the output strictly.
Provide only the list of framework names or programming language in output without additional text.
Output format:
If you determine one framework: [framework1]
If you determine more than two frameworks, return two most accurate :[framework1, framework2]
If framework is not identifiable, return the primary programming language used: [programming language]
If neither a framework nor a primary language can be determined, return []
"""


KEYWORD_PROMPT = """
Generate an exhaustive list of code-related keywords from the provided best practice description that indicate potential deviations from best practices. Only include keywords related to code snippets, libraries, packages, functions, commands, or tools that can be directly searched within files or are commonly used in relevant contexts.

For example:
- If the best practice is 'Use `with` statements to open files instead of `open()` directly to ensure proper resource management,' generate keywords like 'open()'.
- If the best practice is 'Always use `requests` library for HTTP requests instead of `urllib2`,' generate keywords like 'urllib2', 'requests', 'HTTP', etc., but also consider additional relevant keywords such as 'get', 'post', 'session', etc.

The keywords must be solely based on the provided best practice description.

Project code uses {framework} framework.
Best practice: {best_practices}.

Your response should be in the following format:
[Keyword1, Keyword2, ...]
Do not add unnecessary quotes around keywords.
"""


BIFURCATION_PROMPT = """
You are a natural language understanding expert and an expert software developer.

I will provide you with a list of best practices. Each best practice is numbered sequentially, starting with "Best practice 1.", "Best practice 2.", etc.

Your task is to:
1. Understand each best practice in the context of the provided language and framework.
2. Generate a unique keyword for each best practice that perfectly maps to it.

Context:
Framework: {framework}
Best practice: {best_practices}

Request:
1. Create a Python list where each element is a JSON object containing the unique keyword for the corresponding best practice, in the same sequence.
2. Ensure the length of the list matches the number of best practices.
3. Each keyword should be a compulsory string.
4. Determine if the best practice is related to directory structure of the project. If the best practice is related to the directory structure, the answer should be "Yes"; otherwise, "No".\n
Example:
Directory Level Best Practice
App-specific log files should be under the \"store\" directory. This is a directory structure related best practice. So answer should be `repo_level: yes` for this best practice.\n

Non Directory/Code Level Best Practice
When making API calls through python request module, always handle status codes
using response.raise_for_status() method. The answer should be `repo_level: no`
for this best practice.\n

Format your final response strictly as follows:
[
    {{
        "unique_keyword": "Unique keyword for best practice 1",
        "repo_level": "yes",
    }},
    {{
        "unique_keyword": "Unique keyword for best practice 2",
        "repo_level": "no",
    }},
]

Do not include any additional description in your response.
"""
