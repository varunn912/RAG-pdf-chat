# Conversational RAG with PDF Upload

This is a portfolio-worthy web application that allows users to upload a PDF document and have a real-time, streaming conversation with its content. It uses a RAG (Retrieval-Augmented Generation) pipeline powered by LangChain and Groq's Llama3 model.

## ✨ Features

-   **Upload & Chat**: Users can upload any PDF and immediately start asking questions.
-   **Real-time Streaming**: The AI's response is streamed token-by-token for a dynamic, conversational feel.
-   **Modern UI**: A clean, professional interface built with Flask, HTML, and CSS.
-   **Vector-Based Retrieval**: Uses Hugging Face embeddings and a Chroma vector store to find the most relevant parts of the document to answer questions.
-   **Secure Configuration**: API keys are kept safe using a `.env` file.

## 🛠️ Tech Stack

-   **Backend**: Flask (Python)
-   **AI/LLM**: Groq (Llama3), LangChain
-   **Document Processing**: PyPDFLoader
-   **Embeddings & Vector Store**: Hugging Face, ChromaDB / FAISS
-   **Frontend**: HTML, CSS, JavaScript (with `fetch` API for streaming)

## 🚀 Getting Started

### 1. Clone the Repository

```bash
git clone [https://github.com/your-username/RAG-Chat-PDF.git](https://github.com/your-username/RAG-Chat-PDF.git)
cd RAG-Chat-PDF
