from os import environ
from requests import get
from dotenv import load_dotenv

from openai import OpenAI

load_dotenv()

BASE_ID = environ.get("BASE_ID")
TABLE_NAME = 'Sales'
AIRTABLE_API_KEY = environ.get("AIRTABLE_API_KEY")
DEEPSEEK_API_KEY = environ.get("DEEPSEEK_API_KEY")

def query_airtable(filter_formula):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{TABLE_NAME}"
    headers = {
        "Authorization": f"Bearer {AIRTABLE_API_KEY}",
        "Content-Type": "application/json"
    }
    params = {"filterByFormula": filter_formula}
    response = get(url, headers=headers, params=params)
    return response.json()


# Function to ask the LLM to generate the Airtable filter based on the natural language query
def ask_llm_to_generate_filter(question):
    # Construct the prompt for the LLM
    prompt = f"Generate an Airtable filter formula for the following question: '{question}'. " \
             "The fields in my Airtable are: 'Name' (text), 'SalesAmount' (number)."

    model_url = "http://localhost:5000/ask"

    response = get(model_url, json={"question": prompt})
    return response.json()


def analyze_sales_data(filtered_data):
    # Assuming filtered_data is a list of sales records
    branches_sales = {}

    for record in filtered_data:
        branch = record['fields'].get('Branch')
        sales = record['fields'].get('SalesAmount', 0)
        
        if branch not in branches_sales:
            branches_sales[branch] = 0
        branches_sales[branch] += sales
    
    # Now ask the LLM to analyze and summarize the result
    analysis_prompt = f"Given these sales figures by branch: {branches_sales}, which branch has the most sales?"

    client = OpenAI(api_key=DEEPSEEK_API_KEY, base_url="https://api.deepseek.com")
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "system", "content": "You are a helpful assistant, serving as a chatbot to answer questions about Sales data."},
            {"role": "user", "content": analysis_prompt},
        ],
        stream=False
    )
    return response.choices[0].text.strip()


# Example Flow:
user_question = "How much does Filial 2 sold?"
filter_formula = ask_llm_to_generate_filter(user_question)
#airtable_data = query_airtable(filter_formula)
print(filter_formula)
#print(airtable_data)

#answer = analyze_sales_data(airtable_data)
#print(answer)
