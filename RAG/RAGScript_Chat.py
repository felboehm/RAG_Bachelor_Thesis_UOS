import RAG_Chat as RAG
import streamlit as st
import pandas as pd
import helper_func
import hashlib
import time

if __name__ == "__main__":
    # Retrieve hashed password 
    pw = st.secrets.hashed_pw
    
    # Initialize log in status
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.matricle_number = ""

    # If not logged in ask for password
    if not st.session_state.logged_in:
        st.title("Log In")
        st.session_state.matricle_number = st.text_input("Enter your matricle number! If you do not have one you cannot recieve VP-hours. If you still want to participate just enter at least 6 digits", max_chars=8)
        # Handling user input to compare it against stored hash
        if user_pw := st.text_input("Enter the password: ", type="password"):
            # Make MD5 representation of the string and encode it back into a string for checking against hash
            user_pw = hashlib.md5(user_pw.encode()).hexdigest()
            # Logic to check if entered password is correct
            if user_pw == pw and helper_func.check_matricle_number(st.session_state.matricle_number):
                st.session_state.logged_in = True
                st.success("Correct Password! Welcome to the application")
                # Rerun to remove old elements
                st.rerun()
            elif user_pw == pw and not helper_func.check_matricle_number(st.session_state.matricle_number):
                st.error("Correct Password, but you forgot your matriculation number. Please enter it so that you can recieve your VP-hours")
            else:
                st.error("Incorrect Password. Please refer to the E-Mail sent to retrieve the password")
                
    # If logged in load application interface
    if st.session_state.logged_in:
        st.title("RAG for Course Search, using Cognitive Science Courses of the University Osnabrück")
        # Retrieve secrets
        api_key = st.secrets.openAIKey
        rag_db_struc = st.secrets["rag_params"]["database_structure"]
        example_content_retrieval = st.secrets["rag_params"]["example_content_retrieval"]
        system_content_retr = st.secrets["rag_params"]["system_content_retrieval"]
        system_content_gen = st.secrets["rag_params"]["system_content_generation"]
        database_path = st.secrets["rag_params"]["database_path"]

        # Initialize model
        if "model" not in st.session_state:
           st.session_state.model = RAG.RAG_Model(api_key, rag_db_struc, example_content_retrieval, system_content_retr, system_content_gen, database_path)
           #print("Model initialized")

        # Initialize chat history
        if "messages" not in st.session_state:
            st.session_state.messages = []
            #print("Chat initialized")

        # Initialize runtime log
        if "runtime_log" not in st.session_state:
            st.session_state.runtime_log = []

        # Logic helper for correct RAG call
        if "first_run" not in st.session_state:
            st.session_state.first_run = True

        # Write down all that has been happening in this session
        if st.button("Stop"):
            st.write("Logging...")
            cleaned_chat = helper_func.process_chat(st.session_state.messages)
            cleaned_queries = helper_func.process_list(st.session_state.model.query_list)

            df_json = pd.DataFrame(cleaned_chat)
            query_json = pd.DataFrame(cleaned_queries)
            runtime_json = pd.DataFrame(st.session_state.runtime_log)
            timestamp = time.strftime("%d_%m_%Y__%H_%M_%S")
            df_json.to_json(f"../.logs/{st.session_state.matricle_number}_{timestamp}_Log_Messages", orient="records")
            query_json.to_json(f"../.logs/{st.session_state.matricle_number}_{timestamp}_Log_Query", orient="records")
            runtime_json.to_json(f"../.logs/{st.session_state.matricle_number}_{timestamp}_Log_Runtime", orient="columns")


            st.write("Finished Logging. Have a nice day!")

            exit()

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
            response, runtimes = st.session_state.model.RAG(st.session_state.messages)
            full_response = ""
            if st.session_state.first_run == True:
                full_response = response
                st.session_state.first_run = False
                st.write(response)
            else:
                starttime = time.time()
                full_response = st.write_stream(response)
                runtimes.append({"time_to_create_content": time.time() - starttime})
                st.session_state.runtime_log.append({f"runtimes_for_call_{int(len(st.session_state.messages) / 2)}": runtimes})
            st.session_state.messages.append({"role": "assistant", "content": full_response})

                #  Print the output
                #st.write(model.RAG(st.text_input("Prompt")))
