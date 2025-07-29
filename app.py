# app.py

import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, Response, jsonify
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_chroma import Chroma
from langchain_community.document_loaders import PyPDFLoader
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from werkzeug.utils import secure_filename
import traceback

# Load environment variables
load_dotenv()
os.environ['HF_TOKEN'] = os.getenv("HF_TOKEN")

# Flask App Initialization
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Global variable to hold the vector store
vector_store = None

@app.route('/')
def index():
    """Renders the main page."""
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    """Handles PDF upload and processing."""
    global vector_store
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            # 1. Load, split, and embed the PDF
            loader = PyPDFLoader(filepath)
            docs = loader.load_and_split()
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            splits = text_splitter.split_documents(docs)
            embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
            
            # 2. Create the vector store
            vector_store = Chroma.from_documents(documents=splits, embedding=embeddings)

            return jsonify({"success": True, "message": f"File '{filename}' processed successfully."})

        except Exception as e:
            traceback.print_exc()
            return jsonify({"error": f"An error occurred: {str(e)}"}), 500
    else:
        return jsonify({"error": "Invalid file type. Please upload a PDF."}), 400

def stream_chat_response(user_query):
    """Streams the RAG chain response."""
    global vector_store
    if not vector_store:
        yield "data: [ERROR] No document has been processed. Please upload a PDF first.\n\n"
        return

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        yield "data: [ERROR] Groq API key not found. Please set it in your .env file.\n\n"
        return
        
    try:
        llm = ChatGroq(groq_api_key=api_key, model_name="Llama3-8b-8192")
        retriever = vector_store.as_retriever()
        
        # Context-aware prompt
        contextualize_q_system_prompt = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""
        contextualize_q_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", contextualize_q_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        history_aware_retriever = create_history_aware_retriever(llm, retriever, contextualize_q_prompt)

        # Answering prompt
        qa_system_prompt = """You are an assistant for question-answering tasks. \
        Use the following pieces of retrieved context to answer the question. \
        If you don't know the answer, just say that you don't know. \
        Use three sentences maximum and keep the answer concise.\n\n{context}"""
        qa_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", qa_system_prompt),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}"),
            ]
        )
        Youtube_chain = create_stuff_documents_chain(llm, qa_prompt)
        rag_chain = create_retrieval_chain(history_aware_retriever, Youtube_chain)

        # Stream the response
        chat_history = []  # In a real app, this would be managed per-session
        for chunk in rag_chain.stream({"input": user_query, "chat_history": chat_history}):
            if "answer" in chunk:
                yield f"data: {chunk['answer'].replace('\n', '<br>')}\n\n"
        
    except Exception as e:
        traceback.print_exc()
        yield f"data: [ERROR] An error occurred while generating the response: {str(e)}\n\n"
    
    yield "data: [END_OF_STREAM]\n\n"

@app.route('/chat', methods=['POST'])
def chat():
    """Handles chat requests and returns a streaming response."""
    data = request.json
    user_query = data.get("query")
    if not user_query:
        return jsonify({"error": "Missing query"}), 400
        
    return Response(stream_chat_response(user_query), mimetype='text/event-stream')

if __name__ == '__main__':
    app.run(debug=True, port=5002)