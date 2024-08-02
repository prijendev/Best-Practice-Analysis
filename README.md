# CodeSensi
CodeSensei is designed to enhance code quality, identify bugs, and maintain code standards as software development cycles speed up and codebases grow. <br>

## Key Features
* <b>Detailed Analysis Report: </b> Users can submit a repository link to their code along with corresponding best practice documents. CodeSensei generates a detailed analysis report.
* <b>Visual Indicator: </b>The report highlights areas needing improvement with color-coded highlights and annotated comments.
* <b>Actionable Suggestion: </b>Provides actionable suggestions based on best practices to help users align their code with coding standards and improve overall quality.

By using CodeSensei, developers can ensure their code adheres to best practices, ultimately leading to higher quality and more maintainable software.

## Tools and Technologies used
* <b>Langchain: </b>Langchain provides the platform the create LLM powered application effectively, it have a lot of integrations and functionality.
* <b>SQlite: </b>It is used for caching LLM response where we store keywords and response, this prevents LLM calls saves cost.
* <b>FAISS: </b>It is used as cache as well when we get unknown response from LLM in first run.
* <b>Falcon 180B: </b>This is LLM which is used to run majority of prompt in this application.
* <b>Streamlit: </b>It is an open source framework which used to develop beautiful frontend with less code. 

## Steps to Run Application
* Clone this repository in your local system
  ```
  git clone https://github.com/prijendev/Best-Practice-Analysis.git
  ```
* Open Best-Practice-Analysis folder.
* Create new environment file by the name of .env and add the following api keys:
  ```
  OPENAI_API_KEY="A171 API Key"
  ```
* Open Best-Practice-Analysis folder in your terminal and type the following command:
  ```
  streamlit run ./src/frontend.py
  ```
  This command will open the streamlit UI to use this application
