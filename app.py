import os
import pandas as pd
from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from docx import Document
from sentence_transformers import SentenceTransformer
import chromadb
import logging
from transformers import pipeline

app = Flask(__name__)
UPLOAD_FOLDER = r"D:\RAG-IMP\data"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Initialize logging
logging.basicConfig(level=logging.INFO)

# Initialize ChromaDB client with the new API
chroma_client = chromadb.PersistentClient(path="chroma_persist")  # specify the directory for persistence

try:
    collection = chroma_client.create_collection(name="document_vectors")
except Exception as e:
    logging.error(f"Error creating collection: {e}")
    # Retrieve the existing collection if it already exists
    collection = chroma_client.get_collection(name="document_vectors")

# Load the Hugging Face model for embeddings
model_name = 'sentence-transformers/all-MiniLM-L6-v2'
embedding_model = SentenceTransformer(model_name)

# Initialize the QA pipeline
qa_pipeline = pipeline("question-answering", model="distilbert-base-cased-distilled-squad")

def store_vector_in_chromadb(text, metadata):
    try:
        # Convert embedding to list
        vector = embedding_model.encode(text).tolist()
        logging.info(f"Attempting to store vector for {metadata['filename']}")

        collection.add(
            documents=[text],
            embeddings=[vector],
            ids=[metadata['filename']],
            metadatas=[metadata]
        )
        logging.info(f"Successfully stored vector for {metadata['filename']}")
    except Exception as e:
        logging.error(f"Error storing vector in ChromaDB: {e}")

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
    file.save(file_path)
    
    text = ''
    try:
        if file.filename.endswith('.xlsx'):
            df = pd.read_excel(file_path)
            text = df.to_string(index=False)
        elif file.filename.endswith('.pdf'):
            with open(file_path, 'rb') as f:
                reader = PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text() or ''
        elif file.filename.endswith('.txt'):
            with open(file_path, 'r') as f:
                text = f.read()
        elif file.filename.endswith('.docx'):
            doc = Document(file_path)
            text = '\n'.join([para.text for para in doc.paragraphs])
        
        if text.strip():
            metadata = {'filename': file.filename, 'file_type': file.filename.split('.')[-1]}
            store_vector_in_chromadb(text, metadata)
            return jsonify({'message': 'Vector stored successfully'}), 200
        else:
            return jsonify({'error': 'No text found in file'}), 400
    finally:
        os.remove(file_path)

@app.route('/retrieve_and_answer', methods=['POST'])
def retrieve_and_answer():
    data = request.json
    query = data.get('query', '')

    try:
        # Generate query embedding
        query_vector = embedding_model.encode(query).tolist()

        # Retrieve similar vectors
        results = collection.query(query_embeddings=[query_vector], n_results=5)  # Retrieve top 5 results

        # Extract documents from results
        documents = [result['document'] for result in results['documents']]

        # Use the QA pipeline to generate an answer
        answer = generate_answer(query, documents)

        return jsonify({'answer': answer}), 200
    except Exception as e:
        logging.error(f"Error retrieving and answering: {e}")
        return jsonify({'error': str(e)}), 500

def generate_answer(query, documents):
    context = " ".join(documents)
    result = qa_pipeline(question=query, context=context)
    return result['answer']

if __name__ == '__main__':
    app.run(debug=True, port=5001)


