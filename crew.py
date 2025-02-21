import os
from crewai import Agent, Task, Crew
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")  # Ensure the API key is in the .env file

# Tạo Agent (Chatbot trả lời dựa trên tài liệu)
agent = Agent(
    name="TrainingBot",
    role="Chatbot đào tạo nhân viên",
    goal="Hướng dẫn nhân viên dựa trên tài liệu công ty.",
    backstory="Bạn là chatbot hướng dẫn nhân viên mới dựa trên tài liệu công ty.",
    verbose=True,
    allow_delegation=False,
    openai_api_key=openai.api_key
)

# Tạo Task (Tìm kiếm & trả lời câu hỏi)
def find_answer(question):
    results = collection.query(query_texts=[question], n_results=1)
    if results["documents"]:
        return results["documents"][0]
    return "Không tìm thấy thông tin."

task = Task(
    description="Trả lời câu hỏi của nhân viên dựa trên tài liệu đào tạo.",
    agent=agent,
    expected_output="Một câu trả lời từ tài liệu đào tạo nhân viên.",
    run=lambda question: find_answer(question)
)

# Tạo Crew
crew = Crew(agents=[agent], tasks=[task])

# Chạy thử
question = "What is the vision of Mai Thu Packaging"
print(crew.kickoff(inputs={"question": question}))
