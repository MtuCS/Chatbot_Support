# # File: chroma_helper.py
# import openai
# import chromadb
# import os

# openai.api_key = os.getenv("OPENAI_API_KEY")
# chroma_client = chromadb.PersistentClient(path="./chroma_db")
# collection = chroma_client.get_or_create_collection(name="training_docs")

# def get_embedding(text):
#     response = openai.embeddings.create(input=text, model="text-embedding-ada-002")
#     return response.data[0].embedding

# def add_to_chroma(text, file_name):
#     embedding = get_embedding(text)
#     collection.add(
#         documents=[text],
#         embeddings=[embedding],
#         ids=[file_name]
#     )
