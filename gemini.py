from langchain_community.utilities import SQLDatabase
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_ollama import ChatOllama
from dotenv import load_dotenv
from pydantic import BaseModel, Field
import os

# -------------------------
# ENV
# -------------------------
load_dotenv()

host = 'localhost'
port = '3306'
database_schema = 'text_to_sql'

mysql_uri = f"mysql+pymysql://{os.getenv('SQL_USER')}:{os.getenv('SQL_PASSWORD')}@{host}:{port}/{database_schema}"

# -------------------------
# MODELS
# -------------------------
llm = ChatGoogleGenerativeAI(
    model='gemini-2.5-flash-lite',
    api_key=os.getenv('GOOGLE_API_KEY')
)

llm2 = ChatOllama(
    model='gemma4:31b-cloud'
)

# -------------------------
# DB
# -------------------------
db = SQLDatabase.from_uri(mysql_uri, sample_rows_in_table_info=1)

# -------------------------
# Pydantic schemas
# -------------------------
class SQLResponse(BaseModel):
    sql: str = Field(description="ONLY a SELECT SQL query")

class SQLValidation(BaseModel):
    is_valid: bool
    reason: str

# -------------------------
# schema helper
# -------------------------
def get_schema(_):
    return db.get_table_info()

# -------------------------
# SQL generation chain
# -------------------------
sql_prompt = ChatPromptTemplate.from_template("""
You are a SQL expert.

Generate ONLY a valid SQL SELECT query.

Rules:
- Only SELECT queries
- No explanations
- Single line output

Schema:
{schema}

Question:
{question}
""")

sql_chain = (
    RunnablePassthrough.assign(schema=get_schema)
    | sql_prompt
    | llm.with_structured_output(SQLResponse)
)

# -------------------------
# validation chain
# -------------------------
validation_prompt = ChatPromptTemplate.from_template("""
You are a SQL validator.

Check correctness and safety of the SQL.

Rules:
- Only validate
- Do NOT modify SQL

Schema:
{schema}

Question:
{question}

SQL:
{sql}
""")

validation_chain = (
    RunnablePassthrough.assign(schema=get_schema)
    | validation_prompt
    | llm.with_structured_output(SQLValidation)
)

# -------------------------
# answer chain
# -------------------------
answer_prompt = ChatPromptTemplate.from_template("""
Given the question and SQL result, produce a clear natural language answer.

Question: {question}
Result: {result}

Answer:
""")

answer_chain = answer_prompt | llm2 | StrOutputParser()

# -------------------------
# test inputs
# -------------------------
user_inputs = [
    "What was the budget of Product 12",
    "What are the names of all products in the products table?",
    "List all customer names from the customers table.",
    "Find the name and state of all regions in the regions table.",
    "What is the name of the customer with Customer Index = 1"
]

# -------------------------
# pipeline execution
# -------------------------
responses = []

for question in user_inputs:

    result = None
    final_answer = None

    # 1. Generate SQL
    resp = sql_chain.invoke({"question": question})

    if not hasattr(resp, "sql"):
        raise ValueError("LLM did not return SQL field")

    query = resp.sql.strip().rstrip(";")

    # 2. Hard safety check
    if not query.lower().startswith("select"):
        result = "Rejected: only SELECT queries allowed"
        final_answer = result

    else:
        # 3. Validate SQL
        validation = validation_chain.invoke({
            "question": question,
            "sql": query
        })

        if not validation.is_valid:
            result = f"Rejected SQL: {validation.reason}"
            final_answer = result

        else:
            # 4. Execute SQL
            try:
                result = db.run(query)
            except Exception as e:
                result = f"Error: {e}"

            # 5. Generate answer
            if isinstance(result, str) and result.startswith("Error"):
                final_answer = f"SQL execution failed: {result}"
            else:
                final_answer = answer_chain.invoke({
                    "question": question,
                    "result": result
                })

    # store output
    responses.append({
        "question": question,
        "query": query,
        "query result": result,
        "answer": final_answer
    })

# -------------------------
# output
# -------------------------
print(responses)