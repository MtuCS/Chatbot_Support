# import fitz 
# def extract_text_from_pdf(pdf_file):
#     """Trích xuất văn bản từ file PDF"""
#     doc = fitz.open(pdf_file)  # Mở file PDF
#     text = ""
#     for page_num in range(doc.page_count):
#         page = doc.load_page(page_num)
#         text += page.get_text()  # Trích xuất văn bản từ mỗi trang
#     return text