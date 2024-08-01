import os

CURRENT_DIRECTORY = os.getcwd()
LOG_FILE_TIME_FORMAT = "%d-%m-%Y"  # Time format for log file name
LOG_FOLDER_PATH = os.path.join(CURRENT_DIRECTORY, "logs")
LOG_FILE_PATH = os.path.join(LOG_FOLDER_PATH, "log.log")
FILE_EXTENSIONS = [".py"]
MODEL_NAME = "tiiuae/falcon-180B-chat"
EMBEDING_MODEL = "text-embedding-3-small"
AI71_BASE_URL = "https://api.ai71.ai/v1/"
IGNORABLE_CHARACTERS = ["'", '"', " ", "`", "\n"]



BEST_PRACTICE_PATTERN = r"Practice \d+\."
STATEMENT_PATTERN = r"^(.*?)\n*Reference:"
REFERENCE_PATTERN = r"Reference: (.*)"


KEYWORD_CHUNK_SIZE = 20
MAX_WORKERS_FOR_KEYWORD_CHUNKING = 10
BEST_PRACTICES_CHUNK_SIZE = 10
MAX_FILES_PROCESS_CONCURRENTLY = 3
MAX_CHUNKS_PROCESS_CONCURRENTLY = 3
FILE_THREAD_PREFIX = "file_analysis_thread"
CHUNK_THREAD_PREFIX = "chunk_analysis_thread"
STATEMENT_KEYWORD_PATTERN = r"(.+)\[keyword_name: (.+)\]"
CODE_LINES_CHUNK_SIZE = 500

DOCUMENTATION_CHUNK_TOKEN_LIMIT = 50
DOCUMENTATION_CHUNK_OVERLAP = 0
DOCUMENTATION_SPLIT_MODEL = "gpt-4"
DOCUMENTATION_VECTOR_DB_NAME = "all_documentations"
SCHEDULAR_LOG_FILE_PATH = os.path.join(LOG_FOLDER_PATH, "schedular_log.log")

DB_FOLDER_PATH = os.path.join(CURRENT_DIRECTORY, "db")
SQLITE_DB_NAME = os.path.join(DB_FOLDER_PATH, "sqlite.db")
SQLITE_KEYWORD_TABLE_NAME = "Keyword_Knowledge_Store"
SQLITE_FILE_TABLE_NAME = "File_Knowledge_Store"
INDEX_FOLDER_PATH = os.path.join(DB_FOLDER_PATH, "vector_db")


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

CODE_LEVEL_PROMPT = """
You are an expert in code analysis and best practices understanding. Your task is to analyze and validate the given code against specified best practices. Follow these steps:

1. Thoroughly understand the below provided best practices and code. \n
2. Analyze each line of code against each best practice.\n
3. For each best practice, you have following options, select one option from available options :\n
- "Violated": The code does not adhere to the practice. \n
- "Not Violated": The code aligns with the practice. \n
- "Not Relevant": The practice doesn't apply to this code.\n
- "Unknown": You cannot understand or evaluate the practice.\n

Give me answer based on current code and file only.\n
Forget all the past answers and conversations.\n
Respond strictly in JSON format without any additional description or any markdown formatting. For each best practice, use the following structure: \n
best_practice_keyword in response is same as best practices dict provided keyword. \n

[[{{
best_practice_1_keyword:[
   ["Violated","code line where this best practice is violated",
   "Suggestion to follow this best practice"],
   ["Violated","2nd instance of code line where this best practice is violated",
   "Suggestion to follow this best practice"],
   ...,
   ...,
],
best_practice_2_keyword:[
   ["Not Violated"]
],
best_practice_3_keyword:[
   ["Not Relevant"]
]
}}]]

Context:
- Frameworks: {project_frameworks}\n
- File name: {file_path} \n
- Code: {code} \n
- Best Practices: {best_practices} \n
Proceed with your analysis step by step.
"""

UNKNOWN_RESPONSE_PROMPT = """You are an expert developer.
Giving you a best practice:

<best_practice>

{best_practice}

</best_practice>

I am giving you a code.
Code file path: {file_path}

Code:
<Code>
{code}
</Code>

I am giving you extra information related to this best practice:

<context>
{context}
</context>


The context may contain code snippets or description related to this best practice.
The context can be empty as well or can contain irrelevant information.
Understand the best practice properly using the context given or if the context is empty or irrelevant then understand the best practice based on the statement given.

Your task is to check whether the given code follows this best practice or not.
You have to give me exact lines of code in where the best practice is not followed.

You only have three options:
1) "Violated": Use this option when the particular line of the code does not follow the given best practice. \n
2) "Not Violated": Use this option when all the whole code follows the given best practice.\n
3) "Not Relevant": Use this option when the best practice is not relevant for the given code.

The response should be strictly in the list formate:
[
    ["Violated", "code snippet where this best practice is violated", "Suggestion for the given code line to follow this best practice"]],
    ["Violated", "code snippet where this best practice is violated", "Suggestion for the given code line to follow this best practice"]],
    ...
]
Your response should not consists of extra description.
If the given code does not violates the best practice then simply give an empty list in your response without any extra description.
If the code is not related to the best practice then simply give an empty list in your response without any extra description.
No need to give response for all lines of code, give me that line of code which is actually violated in your response.
Lets go step by step.
"""

SYSTEM_PROMPT = """
Given a best practice as a query input.
This is some context related to this best practice:
<context>

{context}

</context>
Give response compulsory related to the best practice statement provided.
Include necessary code snippets and description related to this best practice compulsory from the provided context only.

Note: **No need to return the entire context, only return that content from the context in detail which is related to this best practice.**

Note: **If the context provided is not related to the best practice, then simply print "Error" in your response. No other extra description should be included in your response in this case.**
"""

REPO_LEVEL_PRACTICE_EVALUATION_PROMPT = """
You are an expert code reviewer.Given {frameworks} the project structure provided below.please analyze it.
Project Structure:
{directory_structure}

Best Practices to Evaluate: {best_practices}
Check for all best practices one by one.
You have to first analyze structure and then evaluate best practice.
Check whether given best practice violated or not based on given project structure.
Your response must be in following  format:
[[{{
    best_practice_keyword: [["Violated/Not Violated","suggested solution"]],
    best_practice_keyword: [["Violated/Not Violated","suggested solution"]],
    best_practice_keyword: [["Violated/Not Violated","suggested solution"]],
    ...
}}]]
Your response must not contain any other text.
In response only json is there no other text.
"""