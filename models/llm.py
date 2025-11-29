import os
import streamlit as st
from langchain_groq import ChatGroq

def get_chatgroq_model():
    try:
        # TRY to get key from Streamlit Secrets, otherwise use environment variable
        # DO NOT PASTE THE ACTUAL KEY HERE FOR GITHUB
        if "groq_api_key" in st.secrets:
            my_api_key = st.secrets["groq_api_key"]
        else:
            my_api_key = os.getenv("GROQ_API_KEY")

        groq_model = ChatGroq(
            api_key=my_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0
        )
        return groq_model
    except Exception as e:
        raise RuntimeError(f"Failed to initialize Groq model: {str(e)}")