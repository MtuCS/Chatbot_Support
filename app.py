import os
import time
import json
import requests
import msal
import fitz  # PyMuPDF
import openai
import chromadb
from dotenv import load_dotenv
from fastapi import FastAPI

# Load biến môi trường
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
azure_client_id = os.getenv("AZURE_CLIENT_ID")
azure_tenant_id = os.getenv("AZURE_TENANT_ID")
azure_client_secret = os.getenv("AZURE_CLIENT_SECRET")
sharepoint_site_url = "maithujsc.sharepoint.com/sites/Trainingdocument"
drive_id = "b!SJpkxkt_aECkl7ZK6YMWBTM-60BFIl5ChlC_cxyDngG7XD9-vWJITZvMeqzfYkAW"

# Khởi tạo FastAPI app
app = FastAPI()

# Kết nối ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="training_docs")

@app.get("/")
def home():
    return {"message": "Chatbot is running!"}

@app.get("/search")
def search(query: str):
    """API tìm kiếm trong ChromaDB"""
    results = search_in_chroma(query)
    return {"query": query, "results": results}

@app.get("/chat")
def chat(query: str):
    """API trả lời câu hỏi"""
    answer = generate_answer(query)
    return {"query": query, "answer": answer}

# Chạy lệnh update dữ liệu trước khi server khởi động
update_chromadb()
