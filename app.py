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

app = FastAPI()


# Load biến môi trường
load_dotenv()
openai_api_key = os.getenv("OPENAI_API_KEY")
azure_client_id = os.getenv("AZURE_CLIENT_ID")
azure_tenant_id = os.getenv("AZURE_TENANT_ID")
azure_client_secret = os.getenv("AZURE_CLIENT_SECRET")
sharepoint_site_url = "maithujsc.sharepoint.com/sites/Trainingdocument"
drive_id = "b!SJpkxkt_aECkl7ZK6YMWBTM-60BFIl5ChlC_cxyDngG7XD9-vWJITZvMeqzfYkAW"

# Kết nối ChromaDB
chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="training_docs")

def get_access_token():
    app = msal.ConfidentialClientApplication(
        azure_client_id,
        authority=f"https://login.microsoftonline.com/{azure_tenant_id}",
        client_credential=azure_client_secret
    )
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return token.get("access_token")

def get_files_in_folder():
    """Lấy danh sách các file PDF từ SharePoint"""
    token = get_access_token()
    if not token:
        print("❌ Không thể lấy token truy cập!")
        return []
    
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root/children"
    response = requests.get(url, headers=headers)
    
    if response.status_code == 200:
        files = response.json().get("value", [])
        return [file["name"] for file in files if file["name"].endswith(".pdf")]
    else:
        print("❌ Lỗi lấy danh sách file:", response.json())
        return []

def download_file(file_name):
    """Tải file PDF từ SharePoint về thư mục downloads"""
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{file_name}:/content"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        os.makedirs("downloads", exist_ok=True)
        with open(f"downloads/{file_name}", "wb") as f:
            f.write(response.content)
        print(f"✅ Đã tải file: {file_name}")
    else:
        print(f"❌ Lỗi tải file {file_name}: {response.json()}")

def extract_text_from_pdf(pdf_file):
    """Trích xuất văn bản từ file PDF"""
    doc = fitz.open(pdf_file)
    return "\n".join(page.get_text() for page in doc)

def get_embedding(text):
    """Tạo embedding từ văn bản"""
    response = openai.Embedding.create(model="text-embedding-ada-002", input=text)
    return response["data"][0]["embedding"]

def update_chromadb():
    """Tải tài liệu mới từ SharePoint và cập nhật vào ChromaDB"""
    pdf_files = get_files_in_folder()
    
    for file_name in pdf_files:
        pdf_path = f"downloads/{file_name}"
        if not os.path.exists(pdf_path):
            download_file(file_name)
        
        text = extract_text_from_pdf(pdf_path)
        if text.strip():
            collection.add(documents=[text], embeddings=[get_embedding(text)], ids=[file_name])
            print(f"✅ Đã cập nhật vào ChromaDB: {file_name}")
        else:
            print(f"⚠️ File {file_name} không có nội dung!")

def search_in_chroma(query, top_k=3):
    """Tìm kiếm câu hỏi trong ChromaDB"""
    embedding = get_embedding(query)
    results = collection.query(query_embeddings=[embedding], n_results=top_k)
    return [result[0] for result in results["documents"]]

def generate_answer(query):
    """Trả lời câu hỏi dựa trên dữ liệu trong ChromaDB"""
    context = "\n".join(search_in_chroma(query))
    if context:
        prompt = f"Trả lời câu hỏi sau dựa trên thông tin dưới đây:\n\n{context}\n\nCâu hỏi: {query}\nTrả lời:"
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "Bạn là một trợ lý thông minh."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=150
        )
        return response['choices'][0]['message']['content'].strip()
    else:
        return "Xin lỗi, tôi không tìm thấy thông tin phù hợp."

def chat():
    """Khởi chạy chatbot"""
    print("Chào bạn! Tôi là trợ lý ảo của Mai Thư. Bạn có thể hỏi tôi bất cứ câu hỏi nào.")
    while True:
        user_input = input("Bạn: ")
        if user_input.lower() in ["exit", "quit", "bye"]:
            print("Tạm biệt!")
            break
        print(f"\nCâu hỏi của bạn: {user_input}\n")
        answer = generate_answer(user_input)
        print(f"Chatbot: {answer}")

if __name__ == "__main__":
    update_chromadb()  # Cập nhật dữ liệu trước khi chạy chatbot
    chat()
