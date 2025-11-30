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
st.set_page_config(
    page_title="PyScholar AI", 
    page_icon="🎓", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 5. CUSTOM CSS FOR BEAUTIFICATION ---
def inject_custom_css():
    st.markdown("""
    <style>
        /* Hide Streamlit Branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        /* Custom Title Style */
        .title-container {
            text-align: center;
            padding: 20px;
            background: linear-gradient(90deg, #4b6cb7 0%, #182848 100%);
            border-radius: 10px;
            margin-bottom: 20px;
            color: white;
        }
        .title-text {
            font-size: 40px;
            font-weight: bold;
            margin: 0;
        }
        .subtitle-text {
            font-size: 18px;
            font-style: italic;
            margin-top: 5px;
            opacity: 0.9;
        }
        
        /* Chat Message Styling Enhancements */
        .stChatMessage {
            padding: 10px;
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

def main():
    # Apply CSS
    inject_custom_css()
    
    # Initialize Database
    init_db()

    # Get LLM
    try:
        chat_model = get_chatgroq_model()
    except Exception as e:
        st.error(f"Error loading Model: {e}. Check your API keys in models/llm.py")
        st.stop()

    # --- SIDEBAR NAVIGATION ---
    with st.sidebar:
        st.image("https://cdn-icons-png.flaticon.com/512/4712/4712035.png", width=80) # Placeholder Logo
        st.title("PyScholar AI")
        st.markdown("---")
        
        page = st.radio("📍 Navigation", ["Chat Assistant", "Admin Dashboard", "Help & Guide"])
        
        st.markdown("---")
        st.subheader("📚 Knowledge Base")
        uploaded_file = st.file_uploader("Upload Mentorship PDF", type="pdf", help="Upload a guide for the bot to read.")
        
        if uploaded_file:
            if "vectorstore" not in st.session_state:
                with st.spinner("Processing Knowledge Base..."):
                    st.session_state.vectorstore = process_pdf(uploaded_file)
                st.success("✅ Knowledge Base Ready!")
            else:
                st.info("📂 PDF Loaded Active")

        st.markdown("---")
        if st.button("🗑️ Reset Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.booking_in_progress = False
            st.session_state.confirming = False
            st.session_state.extracted_details = {} 
            st.session_state.last_reset_index = 0
            st.rerun()

    # --- PAGE 1: CHAT INTERFACE ---
    if page == "Chat Assistant":
        # Custom Header
        st.markdown("""
        <div class="title-container">
            <p class="title-text">🎓 PyScholar AI</p>
            <p class="subtitle-text">Your Intelligent Data Science Mentorship Guide</p>
        </div>
        """, unsafe_allow_html=True)

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

        # Welcome Message if Empty
        if not st.session_state.messages:
            st.info("👋 **Hello!** I can help you book mentorship sessions or answer questions about the course. Upload a PDF to get started!")

        # Display Chat History
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Handle User Input
        if prompt := st.chat_input("Ask a question or book a session..."):
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
                                st.balloons() # 🎉 Fun effect on success
                            else:
                                response_text = f"❌ Error saving booking: {bid}"
                            
                            # Reset
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

                    # B. NORMAL FLOW
                    else:
                        if st.session_state.booking_in_progress:
                            intent = "BOOKING"
                        else:
                            intent = determine_intent(prompt, chat_model)
                        
                        # --- BOOKING FLOW ---
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

                        # --- RAG / GENERAL QUERY ---
                        else:
                            if "vectorstore" in st.session_state:
                                retriever = st.session_state.vectorstore.as_retriever(search_kwargs={"k": 3})
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
    elif page == "Help & Guide":
        st.header("📝 User Guide")
        st.markdown("""
        ### How to use PyScholar AI
        
        1. **🤖 Chatting:** Just type naturally! You can say "Hi" or ask questions.
        2. **📚 Knowledge Base:** - Upload a PDF in the sidebar.
           - Ask questions like *"What is covered in Week 1?"* or *"Who are the mentors?"*
        3. **📅 Booking a Session:**
           - Say *"I want to book a mentorship session"*
           - The bot will ask for your Name, Email, Phone, and Date.
           - Once confirmed, you will receive an email!
        
        ### Troubleshooting
        - If the bot gets stuck, click **"Reset Conversation"** in the sidebar.
        """)

if __name__ == "__main__":
    main()
