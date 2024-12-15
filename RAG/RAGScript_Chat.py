import RAG_Chat as RAG
import streamlit as st

if __name__ == "__main__":
    # Retrieve secrets
    api_key = st.secrets.openAIKey
    rag_db_struc = st.secrets["rag_params"]["database_structure"]
    example_content_retrieval = st.secrets["rag_params"]["example_content_retrieval"]
    system_content_retr = st.secrets["rag_params"]["system_content_retrieval"]
    system_content_gen = st.secrets["rag_params"]["system_content_generation"]
    database_path = st.secrets["rag_params"]["database_path"]

    # Initialize model
    model = RAG.RAG_Model(api_key, rag_db_struc, example_content_retrieval, system_content_retr, system_content_gen, database_path)

    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display chat messages from history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    # Accept user input
    if prompt := st.chat_input("What is up!"):
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})
        # Display user message in chat message container
        with st.chat_message("user"):
            st.markdown(prompt)
    
    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response = model.RAG(st.session_state.messages)
        st.write(response)
    st.session_state.messages.append({"role": "assistant", "content": response})

    #  Print the output
    #st.write(model.RAG(st.text_input("Prompt")))
