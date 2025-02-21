import os
import requests
import openai
import fitz  
import chromadb
import msal
from dotenv import load_dotenv
from langchain.text_splitter import RecursiveCharacterTextSplitter
import sys
sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

openai.api_key = os.getenv("OPENAI_API_KEY")

azure_client_id = os.getenv("AZURE_CLIENT_ID")
azure_tenant_id = os.getenv("AZURE_TENANT_ID")
azure_client_secret = os.getenv("AZURE_CLIENT_SECRET")

sharepoint_site_url = "maithujsc.sharepoint.com/sites/Trainingdocument"
drive_id = "b!SJpkxkt_aECkl7ZK6YMWBTM-60BFIl5ChlC_cxyDngG7XD9-vWJITZvMeqzfYkAW"

os.makedirs("downloads", exist_ok=True)

chroma_client = chromadb.PersistentClient(path="./chroma_db")
collection = chroma_client.get_or_create_collection(name="training_docs")

if collection:
    print(f"✅ Collection '{collection.name}' đã được tạo thành công.")
else:
    print("❌ Lỗi khi tạo collection.")

def get_access_token():
    app = msal.ConfidentialClientApplication(
        azure_client_id,
        authority=f"https://login.microsoftonline.com/{azure_tenant_id}",
        client_credential=azure_client_secret
    )
    token = app.acquire_token_for_client(scopes=["https://graph.microsoft.com/.default"])
    return token["access_token"]

def get_files_in_folder():
    token = get_access_token()
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
    token = get_access_token()
    headers = {"Authorization": f"Bearer {token}"}
    url = f"https://graph.microsoft.com/v1.0/drives/{drive_id}/root:/{file_name}:/content"
    
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        with open(f"downloads/{file_name}", "wb") as f:
            f.write(response.content)
        print(f"✅ Đã tải file: {file_name}")
    else:
        print(f"❌ Lỗi tải file {file_name}: {response.json()}")
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(pdf_file)
    return "\n".join(page.get_text() for page in doc)

def chunk_text(text, chunk_size=500, chunk_overlap=100):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_text(text)

def get_embedding(text):
    response = openai.Embedding.create(model="text-embedding-ada-002", input=[text])
    return response.data[0].embedding

pdf_files = get_files_in_folder()
for file in pdf_files:
    download_file(file)
    pdf_path = f"downloads/{file}"
    text = extract_text_from_pdf(pdf_path)
    
    if text.strip():
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            collection.add(
                documents=[chunk],
                embeddings=[get_embedding(chunk)],
                ids=[f"{file}_{i}"]
            )
        print(f"✅ Đã lưu {len(chunks)} đoạn từ {file} vào ChromaDB")
    else:
        print(f"⚠️ File {file} không có nội dung!")

print(f"📝 Số lượng tài liệu trong ChromaDB: {collection.count()}")
