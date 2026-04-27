import os
import json
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

# Load env
#load_dotenv(dotenv_path="D:/pythonPractice/mykeys.env")

load_dotenv()

# Initialize LLM
llm = ChatOpenAI(
    api_key=os.getenv("OPENAI_API_KEY"),
    model="gpt-4o-mini"
)

# Prompt
prompt = PromptTemplate(
    input_variables=["incident"],
    template="""
You are an operations expert.

Analyze the incident and return ONLY valid JSON:

{{
  "summary": "1 line summary",
  "impact": "business impact",
  "root_cause": "probable cause",
  "recommendations": "Provide 4-5 clear, actionable troubleshooting steps separated by '.'",
  "confidence": "0-100%",
  "severity": "High/Medium/Low"
}}

Incident:
{incident}
"""
)

chain = prompt | llm | StrOutputParser()

# Function
def analyze_incident(incident):
    ai_output = chain.invoke({"incident": incident})
    return json.loads(ai_output)