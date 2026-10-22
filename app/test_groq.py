
import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

llm = ChatGroq(
    model=os.getenv("GROQ_MODEL", "openai/gpt-oss-20b"),
    api_key=os.environ["GROQ_API_KEY"],
    temperature=0,
)

response = llm.invoke(
    "Reply with exactly: Groq connection successful"
)

print(response.content)
