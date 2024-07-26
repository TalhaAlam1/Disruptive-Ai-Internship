from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF for PDFs
import pandas as pd
import re
from docx import Document

# Initialize the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

def extract_text_from_pdf(pdf_path):
    text = ""
    for path in pdf_path:
        doc = fitz.open(path)
        for page in doc:
            text += page.get_text()
        doc.close()  # Close the document after processing
    return text

def extract_text_from_excel(excel_path):
    text = ""
    for path in excel_path:
        df = pd.read_excel(path)
        for column in df.columns:
            text += ' '.join(df[column].astype(str).tolist())
    return text

def extract_text_from_doc(doc_path):
    text = ""
    for path in doc_path:
        doc = Document(path)
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
    return text

def preprocess_text(text):
    text = text.lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    return text

def embed_text(text):
    return model.encode(text)

# Define file paths
pdf_path = [
    r'C:\NIC internship work\project\uploads\Company_Profile_and_Services.pdf',
    r'C:\NIC internship work\project\uploads\files\Software Solutions.pdf',
    r'C:\NIC internship work\project\uploads\files\Project_Plan_and_Timeline.pdf',
    r'C:\NIC internship work\project\uploads\files\Company_Profile_and_Services.pdf'
]
excel_path = [
    r'C:\NIC internship work\project\uploads\files\personal_data_of_org.xlsx',
    r'C:\NIC internship work\project\uploads\files\Business_Information.xlsx',
    r'C:\NIC internship work\project\uploads\files\Transcation_data.xlsx'
]
doc_path = [
    r'C:\NIC internship work\project\uploads\files\Appendices_and_Supporting_Information.docx',
    r'C:\NIC internship work\project\uploads\files\Database.docx',
    r'C:\NIC internship work\project\uploads\files\Non-Functional_Requirements.docx',
    r'C:\NIC internship work\project\uploads\files\Software Requirements Document.docx'
]

# Extract and preprocess text from each file type
pdf_text = extract_text_from_pdf(pdf_path)
excel_text = extract_text_from_excel(excel_path)
doc_text = extract_text_from_doc(doc_path)

pdf_text_preprocessed = preprocess_text(pdf_text)
excel_text_preprocessed = preprocess_text(excel_text)
doc_text_preprocessed = preprocess_text(doc_text)

# Convert preprocessed text into vectors
pdf_vector = embed_text(pdf_text_preprocessed)
excel_vector = embed_text(excel_text_preprocessed)
doc_vector = embed_text(doc_text_preprocessed)

print(f"PDF Vector: {pdf_vector}")
print(f"Excel Vector: {excel_vector}")
print(f"Document Vector: {doc_vector}")
