import RAG_Chat as RAG
import streamlit as st
import pandas as pd
import helper_func
import hashlib
import time
import credential_testing
import subprocess

if __name__ == "__main__":
    # Retrieve hashed password 
    pw = st.secrets.hashed_pw
    
    # Initialize log in status
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
        st.session_state.matricle_number = ""
    if "finished_logging" not in st.session_state:
        st.session_state.finished_logging = False
        st.session_state.finished_questionaire = False
        st.session_state.load_questionaire = True

    if st.session_state.finished_questionaire:
        st.title("Final Informations")
        st.markdown("""
        ### To receive VP-Hours for participating send an E-Mail, with your VP-Document attached to it, to felboehm@uni-osnabrueck.de. **Include your UUID in the body of the mail, as otherwise it can not be matched to your data and you will not receive VP-Hours**
        """)
        st.write("Your UUID: " + st.session_state.matricle_number)

    if st.session_state.finished_logging and st.session_state.load_questionaire:
        st.title("Questionnaire")
        questions = [
                "Are you a bachelor or master student?",
                "Which Semester are you in?",
                "Did the bot respond to your questions so that you were satisfied by the answers?",
                "Did the bot respond to your questions in a fitting manner?",
                "Did you notice any discrepancies?",
                "Do you feel like the bot helped you plan your courses for the next semester?",
                "Would you use the bot in order to search for courses if it was implemented in StudIP?",
                "If you could only choose one of the two: StudIP search or RAG search, which one would you choose for course searches and why?"
               ]
        responses = {}
        for question in questions:
            if question ==  "Are you a bachelor or master student?":
                responses[question] = st.selectbox(question, ["Bachelor", "Master", "Other"])
            elif question == "Which Semester are you in?":
                responses[question] = st.number_input(question, min_value=1, max_value=20)
            elif question == "Did the bot respond to your questions so that you were satisfied by the answers?":
                responses[question] = st.text_input(question)
            elif question == "Did the bot respond to your questions in a fitting manner?":
                responses[question] = st.text_input(question)
            elif question == "Did you notice any discrepancies?":
                responses[question] = st.text_input(question)
            elif question == "Do you feel like the bot helped you plan your courses for the next semester?":
                responses[question] = st.text_input(question)
            elif question == "Would you use the bot in order to search for courses if it was implemented in StudIP?":
                responses[question] = st.text_input(question)
            elif question == "If you could only choose one of the two: StudIP search or RAG search, which one would you choose for course searches and why?":
                responses[question] = st.text_input(question)
        
        all_filled = all(responses[question] != "" for question in questions)
        finish_button = st.button("Finish up Experiment", disabled=not all_filled)

        if finish_button:
            responses_df = pd.DataFrame(responses, index=[0])
            responses_df.to_json(st.session_state.path_to_write + "_Log_Questionaire", orient="records")
            st.session_state.loc_list.append(st.session_state.path_to_write + "_Log_Questionaire")
            credential_testing.upload_json_to_drive(st.session_state.loc_list)
            st.session_state.finished_questionaire = True
            st.session_state.load_questionaire = False
            st.rerun()

    # If not logged in ask for password
    if not st.session_state.logged_in:
        st.title("Log In")
        st.markdown("""
        ### All the information displayed by the chat bot is given without any guarantee that this is correct information. The underlying course information was exported on the 10th of January, 2025 and courses may still be subject to change.
                    """)
        st.session_state.matricle_number = st.text_input("Enter a unique identifier! It has to be at least 6 characters long.", max_chars=8)
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
                st.error("Correct Password, but you forgot your matriculation number. Please enter it so that you can receive your VP-hours")
            else:
                st.error("Incorrect Password. Please refer to the E-Mail sent to retrieve the password")
    
    # If logged in load application interface
    if st.session_state.logged_in and not st.session_state.finished_logging:
        st.title("RAG for Course Search, using Cognitive Science Courses of the University Osnabrück")
        st.markdown("""
        ### How to use: Enter your questions into the chat below and play around with it. 
        ### **Note that all chats are logged, so only enter information you feel comfortable with!**

        ### When you finished interacting with the chatbot press the stop button. It will take you to the next page.
                    """)
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
            st.session_state.path_to_write = f"../.logs/{st.session_state.matricle_number}_{timestamp}"
            df_json.to_json(st.session_state.path_to_write + "_Log_Messages", orient="records")
            query_json.to_json(st.session_state.path_to_write + "_Log_Query", orient="records")
            runtime_json.to_json(st.session_state.path_to_write + "_Log_Runtime", orient="columns")
            st.session_state.loc_list = [st.session_state.path_to_write + "_Log_Messages", st.session_state.path_to_write + "_Log_Query", st.session_state.path_to_write + "_Log_Runtime"]
            #credential_testing.upload_json_to_drive(loc_list)

            #st.write("Finished Logging. Have a nice day!")
            st.session_state.finished_logging = True
            st.rerun()

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
