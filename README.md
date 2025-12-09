# PyScholar AI - Data Science Mentorship Assistant (https://pyscholar-ai-y43pmvbruvmqfp8h4mfvuv.streamlit.app/)

PyScholar AI is an intelligent mentorship booking assistant designed for Data Science students. It helps users schedule mock interviews, code reviews, and career guidance sessions while answering domain-specific questions using RAG (Retrieval-Augmented Generation).

## Features
- ** AI Chatbot:** powered by Llama-3 (via Groq) for natural conversations.
- ** RAG Knowledge Base:** Upload PDFs (e.g., mentorship guides) to get answers instantly.
- ** Smart Booking System:** Context-aware booking flow that remembers user details across the conversation.
- ** Email Notifications:** Sends real confirmation emails using SMTP.
- ** Admin Dashboard:** View, filter, and manage bookings securely.

## Tech Stack
- **Frontend:** Streamlit
- **LLM:** Llama-3-70b (Groq API)
- **Database:** SQLite
- **Orchestration:** LangChain
- **Embeddings:** HuggingFace (Sentence Transformers)

## Project Structure

Here are the complete solutions for Option A (GitHub & Deployment) and Option B (README Content).

## Tech Stack
- **Frontend:** Streamlit
- **LLM:** Llama-3-70b (Groq API)
- **Database:** SQLite
- **Orchestration:** LangChain
- **Embeddings:** HuggingFace (Sentence Transformers)

## Project Structure
project_root/ ├── app/ │ ├── main.py # Main application entry point │ ├── chat_logic.py # Intent classification logic │ ├── booking_flow.py # Slot filling & state management │ ├── rag_pipeline.py # PDF ingestion & vector store │ ├── tools.py # Database & Email utilities │ └── admin_dashboard.py # Admin UI ├── db/ │ └── bookings.db # SQLite Database ├── requirements.txt # Dependencies └── README.md # Documentation

## Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <YOUR_REPO_LINK>
   cd AI_UseCase


## ⚙️ Setup & Installation

1. **Clone the repository:**
   ```bash
   git clone <YOUR_REPO_LINK>
   cd AI_UseCase

### **Option A: GitHub & Deployment Steps**

Follow these steps exactly to deploy your app without leaking your passwords.

#### **Phase 1: Prepare for GitHub (Safety First)**
Before uploading, we must tell Git to **ignore** your password file so hackers don't see it.

1.  **Create a `.gitignore` file:**
    * In your `AI_UseCase` folder, create a new file named `.gitignore` (no extension).
    * Paste this inside:
        ```text
        .streamlit/secrets.toml
        __pycache__/
        *.pyc
        db/bookings.db
        venv/
        .env
        ```

2.  **Verify `requirements.txt`:**
    * Ensure your `requirements.txt` has these exact libraries (Streamlit Cloud needs them):
        ```text
        streamlit
        langchain
        langchain-groq
        langchain-community
        langchain-huggingface
        faiss-cpu
        pypdf
        sentence-transformers
        tf-keras
        ```

#### **Phase 2: Push to GitHub**
1.  Log in to [GitHub.com](https://github.com) and create a **New Repository**. Name it `PyScholar-AI`.
2.  Open your **VS Code Terminal** (inside `AI_UseCase`) and run these commands one by one:
    ```bash
    git init
    git add .
    git commit -m "Initial commit - PyScholar AI"
    git branch -M main
    git remote add origin https://github.com/YOUR_USERNAME/PyScholar-AI.git
    git push -u origin main
    ```
    *(Replace `YOUR_USERNAME` with your actual GitHub username).*

#### **Phase 3: Deploy to Streamlit Cloud**
This is the final step to get your public URL[cite: 219].

1.  Go to **[share.streamlit.io](https://share.streamlit.io/)**.
2.  Click **"New app"**.
3.  Select your GitHub repository (`PyScholar-AI`).
4.  **Main file path:** Enter `app/main.py`.
5.  **Click "Advanced Settings"** (This is critical!).
6.  Paste your secrets here exactly as they were in your local file:
    ```toml
    [email]
    sender_email = "YOUR_BOT_EMAIL@gmail.com"
    app_password = "YOUR_16_DIGIT_CODE"
    ```
    *(Also add your Groq API Key if you haven't hardcoded it).*

7.  Click **"Deploy"**.
