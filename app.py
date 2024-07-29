from flask import Flask, request, jsonify
import pandas as pd
from PyPDF2 import PdfReader
import os
from docx import Document
from sklearn.feature_extraction.text import TfidfVectorizer
import json

app = Flask(__name__)
UPLOAD_FOLDER = r"D:\D-AI\files"
VECTOR_FOLDER = r"D:\D-AI\filesvector_data"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['VECTOR_FOLDER'] = VECTOR_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])
if not os.path.exists(app.config['VECTOR_FOLDER']):
    os.makedirs(app.config['VECTOR_FOLDER'])

def vectorize_text(text):
    try:
        vectorizer = TfidfVectorizer()
        vectors = vectorizer.fit_transform([text])
        return vectors.toarray()[0]
    except Exception as e:
        return {'error': str(e)}

def save_vector(vector, doc_id):
    try:
        vector_path = os.path.join(app.config['VECTOR_FOLDER'], f"{doc_id}.json")
        with open(vector_path, 'w') as f:
            json.dump({'vector': vector.tolist()}, f)
        return True
    except Exception as e:
        return {'error': str(e)}

def handle_file_upload(file, file_type):
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    text = ""
    
    try:
        
        if file_type == "excel":
            df = pd.read_excel(file_path)
            text = df.to_string()
        elif file_type == "pdf":
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ""  # Handle None return
        elif file_type == "document":
            if file.filename.endswith('.txt'):
                with open(file_path, 'r') as f:
                    text = f.read()
            elif file.filename.endswith('.docx'):
                doc = Document(file_path)
                text = '\n'.join([para.text for para in doc.paragraphs])

       
        vector = vectorize_text(text)
        doc_id = f"{file_type}_{file.filename}"
        
      
        save_result = save_vector(vector, doc_id)
        if save_result is True:
            return vector, doc_id
        else:
            return save_result, None
            
    except Exception as e:
        return {'error': str(e)}, None
    finally:
        os.remove(file_path)

@app.route('/upload/excel', methods=['POST'])
def upload_excel():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.xlsx'):
        vector, doc_id = handle_file_upload(file, 'excel')
        if isinstance(vector, dict) and 'error' in vector:
            return jsonify(vector), 500
        return jsonify({'vector': vector.tolist(), 'document_id': doc_id}), 200
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/upload/pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and file.filename.endswith('.pdf'):
        vector, doc_id = handle_file_upload(file, 'pdf')
        if isinstance(vector, dict) and 'error' in vector:
            return jsonify(vector), 500
        return jsonify({'vector': vector.tolist(), 'document_id': doc_id}), 200
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/upload/document', methods=['POST'])
def upload_document():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    if file and (file.filename.endswith('.txt') or file.filename.endswith('.docx')):
        vector, doc_id = handle_file_upload(file, 'document')
        if isinstance(vector, dict) and 'error' in vector:
            return jsonify(vector), 500
        return jsonify({'vector': vector.tolist(), 'document_id': doc_id}), 200
    return jsonify({'error': 'Invalid file format'}), 400

@app.route('/upload/all', methods=['POST'])
def upload_all():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    file_type = None
    if file.filename.endswith('.xlsx'):
        file_type = "excel"
    elif file.filename.endswith('.pdf'):
        file_type = "pdf"
    elif file.filename.endswith('.txt') or file.filename.endswith('.docx'):
        file_type = "document"
    if file_type:
        vector, doc_id = handle_file_upload(file, file_type)
        if isinstance(vector, dict) and 'error' in vector:
            return jsonify(vector), 500
        return jsonify({'vector': vector.tolist(), 'document_id': doc_id}), 200
    return jsonify({'error': 'Invalid file format'}), 400

if __name__ == '__main__':
    app.run(debug=True)
