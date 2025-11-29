from langchain_core.prompts import ChatPromptTemplate

def determine_intent(user_input, llm):
    """
    Decides if the user wants to 'book' something or just 'query' information.
    """
    prompt = ChatPromptTemplate.from_template(
        """
        Classify the user's intent based on the latest message.
        User Message: "{input}"
        
        Respond with EXACTLY one word: "BOOKING" or "QUERY".
        If they say "hi", "hello", or ask about services, classify as "QUERY".
        If they mention scheduling, dates, or explicitly say "book", classify as "BOOKING".
        """
    )
    chain = prompt | llm
    response = chain.invoke({"input": user_input})
    return response.content.strip().upper()