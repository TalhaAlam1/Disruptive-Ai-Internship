import tempfile
import streamlit as st
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain.prompts import ChatPromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter
import os
import requests
from dotenv import load_dotenv
import pandas as pd
from docx import Document

load_dotenv()

# Load the Groq API key from the environment
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# Load the uploaded file
def file_loader(uploaded_file):
    temp = None
    if uploaded_file.name.endswith('.pdf'):
        with tempfile.NamedTemporaryFile(delete=False) as temp_pdf:
            temp_pdf.write(uploaded_file.read())
            loader = PyPDFLoader(file_path=temp_pdf.name)
            temp = loader.load()
            os.remove(temp_pdf.name)
    elif uploaded_file.name.endswith('.docx'):
        with tempfile.NamedTemporaryFile(delete=False) as temp_docx:
            temp_docx.write(uploaded_file.read())
            temp_docx.seek(0)
            doc = Document(temp_docx.name)
            temp = [{'page_content': p.text} for p in doc.paragraphs if p.text.strip()]
            os.remove(temp_docx.name)
    elif uploaded_file.name.endswith('.xlsx'):
        with tempfile.NamedTemporaryFile(delete=False) as temp_excel:
            temp_excel.write(uploaded_file.read())
            temp_excel.seek(0)
            df = pd.read_excel(temp_excel.name)
            temp = [{'page_content': str(row)} for row in df.to_dict(orient='records')]
            os.remove(temp_excel.name)
    return temp

# Groq API function to get embeddings
def get_embeddings(texts):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    response = requests.post("https://api.groq.com/embedding", json={"texts": texts}, headers=headers)
    response.raise_for_status()
    return response.json()

# Groq API function to generate text
def generate_text(prompt):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    response = requests.post("https://api.groq.com/generate", json={"prompt": prompt}, headers=headers)
    response.raise_for_status()
    return response.json()['generated_text']

# Function to push vector data into Groq
def push_vectors_to_groq(vectors):
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    response = requests.post("https://api.groq.com/vectors", json={"vectors": vectors}, headers=headers)
    response.raise_for_status()

# RAG chain for sending the loaded document into the LLM for generating the response
def RAG_chain(document, query):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    if isinstance(document, list):  # for DOCX
        documents = [{'page_content': text} for text in document]
    elif isinstance(document, pd.DataFrame):  # for Excel
        documents = [{'page_content': str(row)} for row in document]
    else:  # for PDF
        documents = document

    splits = text_splitter.split_documents(documents=documents)

    # Generate embeddings and store in Chroma
    embeddings = get_embeddings([doc['page_content'] for doc in splits])
    vectorstore = Chroma.from_embeddings(embeddings, splits, persist_directory='PDF-Chatbot/db')
    
    # Push vector data into Groq
    push_vectors_to_groq(embeddings)

    retriever = vectorstore.as_retriever()

    template = """
    {context}
    From the above context, answer the user query [{question}] in the best possible way.
    """
    prompt = ChatPromptTemplate.from_template(template)

    # LLM response generation
    context = retriever.retrieve(query)
    input_text = prompt.format(context=context, question=query)
    response = generate_text(input_text)

    return response

def PDFChatbot(uploaded_file, query):
    document = file_loader(uploaded_file)
    return RAG_chain(document=document, query=query)

# Main function of the program comprises of basic UI for user interaction
if __name__ == '__main__':
    try:
        st.title("Chatbot 📚")
        uploaded_file = st.file_uploader('Upload PDF, DOCX, or Excel file', type=['pdf', 'docx', 'xlsx'])
        prompt = st.text_input('Enter the question you want to ask to the LLM', placeholder='Enter your prompt here...')
        
        if st.button("Submit"):
            if uploaded_file and prompt:
                result = PDFChatbot(uploaded_file=uploaded_file, query=prompt)
                st.balloons()
                st.write(result)
            else:
                st.warning("Please upload a file and enter a question!")
    except Exception as e:
        st.error(f"An error occurred: {e}")
