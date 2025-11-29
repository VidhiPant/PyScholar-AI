import os
# --- 1. CRITICAL FIX FOR KERAS/TRANSFORMERS CONFLICT ---
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
os.environ["TF_USE_LEGACY_KERAS"] = "1"

import streamlit as st
import sys
import pandas as pd

# --- 2. PATH SETUP ---
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- 3. IMPORTS ---
from models.llm import get_chatgroq_model
from db.database import init_db
from app.chat_logic import determine_intent
from app.booking_flow import extract_booking_details
from app.rag_pipeline import process_pdf
from app.tools import save_booking_to_db, send_confirmation_email
try:
    from app.admin_dashboard import show_dashboard
except ImportError:
    show_dashboard = None

# --- 4. PAGE CONFIG ---
st.set_page_config(page_title="AI Mentorship Assistant", page_icon="🤖", layout="wide")

def main():
    # Initialize Database on first run
    init_db()

    # Get LLM
    try:
        chat_model = get_chatgroq_model()
    except Exception as e:
        st.error(f"Error loading Model: {e}. Check your API keys in models/llm.py")
        st.stop()

    # --- SIDEBAR NAVIGATION & UPLOAD ---
    with st.sidebar:
        st.title("Navigation")
        page = st.radio("Go to:", ["Chat", "Admin Dashboard", "Instructions"])
        
        st.divider()
        st.subheader("📚 RAG Knowledge Base")
        uploaded_file = st.file_uploader("Upload PDF (Mentorship/Services)", type="pdf")
        
        if uploaded_file:
            if "vectorstore" not in st.session_state:
                with st.spinner("Processing PDF..."):
                    st.session_state.vectorstore = process_pdf(uploaded_file)
                st.success("PDF Knowledge Base Loaded!")
            else:
                st.info("PDF is loaded and ready.")

        if st.button("Clear Chat History"):
            st.session_state.messages = []
            st.session_state.booking_in_progress = False
            st.session_state.confirming = False
            st.session_state.extracted_details = {} 
            st.session_state.last_reset_index = 0
            st.rerun()

    # --- PAGE 1: CHAT INTERFACE ---
    if page == "Chat":
        st.header("💬 PyScholar AI")

        # Initialize Session State
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "booking_in_progress" not in st.session_state:
            st.session_state.booking_in_progress = False
        if "confirming" not in st.session_state:
            st.session_state.confirming = False
        if "extracted_details" not in st.session_state:
            st.session_state.extracted_details = {}
        if "last_reset_index" not in st.session_state:
            st.session_state.last_reset_index = 0

        # Display Chat History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Handle User Input
        if prompt := st.chat_input("Type your message..."):
            st.session_state.messages.append({"role": "user", "content": prompt})
            with st.chat_message("user"):
                st.markdown(prompt)

            response_text = ""
            
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    
                    # A. CHECK FOR BOOKING CONFIRMATION
                    if st.session_state.confirming:
                        if prompt.lower() in ["yes", "y", "confirm", "ok", "sure"]:
                            # Execute Booking
                            details = st.session_state.extracted_details
                            success, bid = save_booking_to_db(
                                details['name'], details['email'], details['phone'],
                                details['booking_type'], details['date'], details['time']
                            )
                            if success:
                                send_confirmation_email(details['email'], details['name'], str(details))
                                response_text = f"✅ **Booking Confirmed!**\n\n**Booking ID:** #{bid}\nI have sent a confirmation email to {details['email']}."
                            else:
                                response_text = f"❌ Error saving booking: {bid}"
                            
                            # Reset states
                            st.session_state.booking_in_progress = False
                            st.session_state.confirming = False
                            st.session_state.extracted_details = {}
                            st.session_state.last_reset_index = len(st.session_state.messages) + 1
                        
                        elif prompt.lower() in ["no", "cancel", "stop"]:
                            response_text = "🚫 Booking cancelled. How else can I help you?"
                            st.session_state.booking_in_progress = False
                            st.session_state.confirming = False
                            st.session_state.extracted_details = {}
                            st.session_state.last_reset_index = len(st.session_state.messages) + 1
                        
                        else:
                            response_text = "Please type 'Yes' to confirm the booking or 'No' to cancel."

                    # B. NORMAL FLOW (INTENT DETECTION)
                    else:
                        if st.session_state.booking_in_progress:
                            intent = "BOOKING"
                        else:
                            intent = determine_intent(prompt, chat_model)
                        
                        # --- BRANCH 1: BOOKING FLOW ---
                        if intent == "BOOKING":
                            st.session_state.booking_in_progress = True
                            
                            relevant_msgs = st.session_state.messages[st.session_state.last_reset_index:]
                            current_details = extract_booking_details(relevant_msgs, chat_model)
                            
                            if current_details:
                                for key, value in current_details.items():
                                    if value and key != 'missing_fields':
                                        st.session_state.extracted_details[key] = value

                            saved = st.session_state.extracted_details
                            missing = []
                            if not saved.get('name'): missing.append("Name")
                            if not saved.get('email'): missing.append("Email")
                            if not saved.get('phone'): missing.append("Phone")
                            if not saved.get('booking_type'): missing.append("Booking Type")
                            if not saved.get('date'): missing.append("Date")
                            if not saved.get('time'): missing.append("Time")
                            
                            if missing:
                                response_text = f"I can help you book. I just need a few details. Could you please provide your **{missing[0]}**?"
                            else:
                                st.session_state.confirming = True
                                response_text = (
                                    f"📋 **Please Confirm Your Booking Details:**\n\n"
                                    f"👤 **Name:** {saved['name']}\n"
                                    f"📧 **Email:** {saved['email']}\n"
                                    f"📱 **Phone:** {saved['phone']}\n"
                                    f"🎓 **Type:** {saved['booking_type']}\n"
                                    f"📅 **Date:** {saved['date']} at {saved['time']}\n\n"
                                    f"**Is this correct? (Yes/No)**"
                                )

                        # --- BRANCH 2: RAG / GENERAL QUERY (UPDATED IMPORTS) ---
                        else:
                            if "vectorstore" in st.session_state:
                                retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 3})
                                # FIXED IMPORTS HERE
                                from langchain_core.runnables import RunnablePassthrough
                                from langchain_core.prompts import PromptTemplate
                                from langchain_core.output_parsers import StrOutputParser

                                template = """Answer the question based only on the following context:
                                {context}

                                Question: {question}
                                """
                                rag_prompt = PromptTemplate.from_template(template)
                                
                                rag_chain = (
                                    {"context": retriever, "question": RunnablePassthrough()}
                                    | rag_prompt
                                    | chat_model
                                    | StrOutputParser()
                                )
                                response_text = rag_chain.invoke(prompt)
                            else:
                                from langchain_core.messages import HumanMessage, SystemMessage
                                msgs = [SystemMessage(content="You are a helpful assistant.")] + [HumanMessage(content=m["content"]) for m in st.session_state.messages if m["role"] == "user"]
                                response_text = chat_model.invoke(msgs).content

                st.markdown(response_text)
                st.session_state.messages.append({"role": "assistant", "content": response_text})

    # --- PAGE 2: ADMIN DASHBOARD ---
    elif page == "Admin Dashboard":
        if show_dashboard:
            show_dashboard()
        else:
            st.error("Admin Dashboard file not found.")

    # --- PAGE 3: INSTRUCTIONS ---
    elif page == "Instructions":
        st.header("📝 Instructions")
        st.markdown("""
        1. **Upload a PDF:** Use the sidebar to upload a document.
        2. **Ask Questions:** Ask about the content of the PDF.
        3. **Book a Session:** Type "I want to book a session".
        4. **Admin Panel:** Check the 'Admin Dashboard' tab.
        """)

if __name__ == "__main__":
    main()