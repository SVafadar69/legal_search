# set url
import requests
import pandas as pd
import os
from dotenv import load_dotenv
import os
from typing import Optional, Callable
import time
from xai_sdk import Client
import json
import boto3
import streamlit as st


from openai import OpenAI, APIError

from groq import Groq
from xai_sdk.chat import user
from new import (case_text_search_citations_list, retrieve_citation_text)

load_dotenv()

aws_access_key_id = st.secrets["AWS_ACCESS_KEY_ID"]
aws_secret_access_key = st.secrets["AWS_SECRET_ACCESS_KEY"]
groq_api_key = st.secrets["GROQ_API_KEY"]
openai_api_key = st.secrets["OPENAI_API_KEY"]
gemini_api_key = st.secrets["GEMINI_API_KEY"]

# aws_access_key_id = os.getenv("AWS_ACCESS_KEY_ID")
# aws_secret_access_key = os.getenv("AWS_SECRET_ACCESS_KEY")
# groq_api_key = os.getenv("GROQ_API_KEY")
# groq_api_key = st.secrets["GROQ_API_KEY"]
# openai_api_key = os.getenv("OPENAI_API_KEY")
# gemini_api_key = os.getenv("GEMINI_API_KEY")

print(groq_api_key)

def retrieve_prompt(mode: str = "r", encoding: str = 'utf-8', prompt_path: str = 'law_query.md') -> str:
    with open(prompt_path, mode, encoding=encoding) as file:
        prompt_text = file.read()
    return prompt_text

def retrieve_section_prompt(mode: str = "r", encoding: str = 'utf-8', prompt_path: str = 'retrieve_section.md') -> str:
    with open(prompt_path, mode, encoding=encoding) as file:
        prompt_text = file.read()
    return prompt_text

def stream_llama(prompt: str, api_key: str, model: str = 'meta-llama/llama-4-scout-17b-16e-instruct') -> str:
    client = Groq(api_key=api_key)
    
    if model == 'meta-llama/llama-4-scout-17b-16e-instruct':
        max_completion_tokens = 8192
    else:
        max_completion_tokens = 12000
    
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0,
        max_completion_tokens=max_completion_tokens,
        top_p=0.95,
        stream=True,
        stop=None)
    
    full_response = ""
    for chunk in completion:
        content = chunk.choices[0].delta.content
        if content is not None:
            full_response += content
    
    return full_response

def hipaa_opus(prompt: str, model_id: str = 'us.anthropic.claude-opus-4-1-20250805-v1:0') -> str:
    client = boto3.client(
        "bedrock-runtime", 
        aws_access_key_id=aws_access_key_id, 
        aws_secret_access_key=aws_secret_access_key, 
        region_name="us-east-2"
    )
    
    # Format the request payload using the model's native structure
    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 12000,
        "temperature": 0,
        "messages": [
            {
                "role": "user",  # Changed from "assistant" to "user"
                "content": [{"type": "text", "text": prompt.strip()}]  # Added .strip() to remove trailing whitespace
            }
        ],
    }
    
    # Convert the native request to JSON
    request = json.dumps(native_request)
    
    # Invoke the model with the request
    streaming_response = client.invoke_model_with_response_stream(
        modelId=model_id, body=request
    )
    
    # Extract and print the response text in real-time
    full_response = ""
    for event in streaming_response["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        if chunk["type"] == "content_block_delta":
            text = chunk["delta"].get("text", "")
            print(text, end="")
            full_response += text
    
    return full_response.strip()  # Strip trailing whitespace from final response

def hipaa_haiku(prompt: str, model_id: str = 'us.anthropic.claude-3-haiku-20240307-v1:0') -> str:
    client = boto3.client(
        "bedrock-runtime", 
        aws_access_key_id=aws_access_key_id, 
        aws_secret_access_key=aws_secret_access_key, 
        region_name="us-east-2"
    )
    
    # Format the request payload using the model's native structure
    native_request = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 8000,
        "temperature": 0,
        "messages": [
            {
                "role": "user",  # Changed from "assistant" to "user"
                "content": [{"type": "text", "text": prompt.strip()}]  # Added .strip() to remove trailing whitespace
            }
        ],
    }
    
    # Convert the native request to JSON
    request = json.dumps(native_request)
    
    # Invoke the model with the request
    streaming_response = client.invoke_model_with_response_stream(
        modelId=model_id, body=request
    )
    
    # Extract and print the response text in real-time
    full_response = ""
    for event in streaming_response["body"]:
        chunk = json.loads(event["chunk"]["bytes"])
        if chunk["type"] == "content_block_delta":
            text = chunk["delta"].get("text", "")
            print(text, end="")
            full_response += text
    
    return full_response.strip()  # Strip trailing whitespace from final response

st.title("Legal Case Query App")
# Initialize session state for query if it doesn't exist
if 'query' not in st.session_state:
    st.session_state.query = ""

# Text input for user query - use session state for value
user_query = st.text_input(
    "Enter your legal query:", 
    value=st.session_state.query,
    placeholder="e.g., discrimination cases in employment",
    help="Enter your search query to find relevant legal cases"
)

# Update session state when user types
st.session_state.query = user_query

# Submit button - now always visible
# Submit button - now always visible
if st.button("🔍 Search Cases", type="primary"):
    # Check if there's a query before proceeding
    if user_query:
        legal_prompt = retrieve_prompt().replace("{{USER_QUERY}}", user_query)
        new_query = hipaa_opus(legal_prompt, api_key=groq_api_key)
        citations = case_text_search_citations_list(new_query)
        citation_texts = retrieve_citation_text(citations)
        st.write(new_query)
        st.write(citations)
        index = 1
        if citation_texts:
            for text in citation_texts:
                # Get a fresh copy of the section prompt template for each iteration
                section_prompt = retrieve_section_prompt()
                section_prompt = section_prompt.replace("{{USER_QUERY}}", user_query).replace("{{TEXT}}", text)
                section = hipaa_opus(section_prompt)
                st.write(f'Case Number: {index}')
                st.write(f'Case Citation: {citations[index-1]}')
                st.write(section)
                index += 1
    else:
        st.warning("Please enter a query before searching")