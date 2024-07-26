from flask import Flask, request, jsonify
import pandas as pd
import os
from docx import Document
import re
from sentence_transformers import SentenceTransformer
import fitz  # PyMuPDF for PDFs
import firebase_admin
from firebase_admin import credentials, firestore
import logging

# Initialize logging
logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
UPLOAD_FOLDER = r'C:\NIC internship work\neww-proj\uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


# Initialize Firebase Admin SDK
cred = credentials.Certificate(r'C:\NIC internship work\neww-proj\bts-jk-firebase.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Initialize the SentenceTransformer model
model = SentenceTransformer('all-MiniLM-L6-v2')

# Helper functions for text extraction
def extract_text_from_pdf(pdf_path):
    text = ""
    doc = fitz.open(pdf_path)
    for page in doc:
        text += page.get_text()
    doc.close()
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

# Function to push data to Firestore
def push_to_firestore(data):
    try:
        db.collection('documents').add(data)
        logging.debug("Data pushed to Firestore successfully: %s", data)
    except Exception as e:
        logging.error("Error pushing data to Firestore: %s", e)

# Route to handle file uploads
@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)

    try:
        if file.filename.endswith('.xlsx'):
            text = extract_text_from_excel(file_path)
        elif file.filename.endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif file.filename.endswith('.docx'):
            text = extract_text_from_doc(file_path)
        else:
            return jsonify({'error': 'Invalid file format'}), 400

        # Check if text is extracted
        if not text.strip():
            logging.error("No text extracted from the uploaded file.")
            return jsonify({'error': 'No text extracted from the uploaded file.'}), 400

        preprocessed_text = preprocess_text(text)
        vector = embed_text(preprocessed_text)

        # Push data to Firestore
        push_to_firestore({
            'text': text,
            'vector': vector.tolist(),
            'file_type': file.filename.split('.')[-1]
        })

        return jsonify({'text': text, 'vector': vector.tolist()}), 200

    except Exception as e:
        logging.error("Error during file upload: %s", e)
        return jsonify({'error': 'Failed to process file'}), 500

if __name__ == '__main__':
    app.run(debug=True)
