from flask import Flask, request, jsonify
import pandas as pd
from PyPDF2 import PdfReader
import os
from docx import Document
import re
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF for PDFs

app = Flask(__name__)
UPLOAD_FOLDER = r'C:\NIC internship work\project\uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Helper functions for text extraction
def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    doc.close()  # Close the document after processing
    return text

def extract_text_from_excel(excel_path):
    text = ""
    df = pd.read_excel(excel_path)
    for column in df.columns:
        text += ' '.join(df[column].astype(str).tolist())
    return text

def extract_text_from_doc(doc_path):
    text = ""
    doc = Document(doc_path)
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

# Route to handle Excel file upload
@app.route('/upload/excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.xlsx'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        text = extract_text_from_excel(file_path)
        preprocessed_text = preprocess_text(text)
        vector = embed_text(preprocessed_text)
        return jsonify({'data': text, 'vector': vector.tolist()}), 200
    return jsonify({'error': 'Invalid file format'}), 400

# Route to handle PDF file upload
@app.route('/upload/pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.pdf'):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        text = extract_text_from_pdf(file_path)
        preprocessed_text = preprocess_text(text)
        vector = embed_text(preprocessed_text)
        return jsonify({'text': text, 'vector': vector.tolist()}), 200
    return jsonify({'error': 'Invalid file format'}), 400

# Route to handle document file upload
@app.route('/upload/document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and (file.filename.endswith('.txt') or file.filename.endswith('.docx')):
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)
        if file.filename.endswith('.txt'):
            text = open(file_path).read()
        elif file.filename.endswith('.docx'):
            text = extract_text_from_doc(file_path)
        preprocessed_text = preprocess_text(text)
        vector = embed_text(preprocessed_text)
        return jsonify({'text': text, 'vector': vector.tolist()}), 200
    return jsonify({'error': 'Invalid file format'}), 400

# New route to handle multiple file types
@app.route('/upload/all', methods=['POST'])
def upload_all():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    if file.filename.endswith('.xlsx'):
        text = extract_text_from_excel(file_path)
    elif file.filename.endswith('.pdf'):
        text = extract_text_from_pdf(file_path)
    elif file.filename.endswith('.txt'):
        text = open(file_path).read()
    elif file.filename.endswith('.docx'):
        text = extract_text_from_doc(file_path)
    else:
        return jsonify({'error': 'Invalid file format'}), 400

    preprocessed_text = preprocess_text(text)
    vector = embed_text(preprocessed_text)
    return jsonify({'text': text, 'vector': vector.tolist()}), 200

if __name__ == '__main__':
    app.run(debug=True)
