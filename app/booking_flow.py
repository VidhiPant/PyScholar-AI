from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

# Define the structure we want the LLM to return
class BookingState(BaseModel):
    name: str = Field(description="Customer name, or null if missing")
    email: str = Field(description="Customer email, or null if missing")
    phone: str = Field(description="Customer phone, or null if missing")
    booking_type: str = Field(description="Type of service (e.g., Mock Interview), or null if missing")
    date: str = Field(description="Preferred date (YYYY-MM-DD), or null if missing")
    time: str = Field(description="Preferred time, or null if missing")
    missing_fields: list = Field(description="List of fields that are still missing")

def extract_booking_details(chat_history, llm):
    # This prompt asks the LLM to look at history and extract JSON
    parser = JsonOutputParser(pydantic_object=BookingState)
    
    prompt = PromptTemplate(
        template="""
        You are a booking assistant. Analyze the conversation history and extract the following booking details:
        Name, Email, Phone, Booking Type, Date, Time.
        
        Current Conversation History:
        {history}
        
        Return a JSON object with the extracted fields. If a field is not mentioned, set it to null.
        Also list which fields are strictly missing from the requirements.
        
        {format_instructions}
        """,
        input_variables=["history"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )
    
    chain = prompt | llm | parser
    
    # Convert list of messages to string for the prompt
    history_str = "\n".join([f"{msg['role']}: {msg['content']}" for msg in chat_history])
    
    try:
        result = chain.invoke({"history": history_str})
        return result
    except Exception as e:
        return None