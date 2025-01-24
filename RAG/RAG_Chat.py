import numpy as np
from openai import OpenAI
import sqlite3
import pandas as pd
import re
import sqlparse
import time

class RAG_Model:
    """
    Represents a Model capable of using OpenAI GPT models to do Retrieval Augmented Generation on a SQL DB in orded to retrieve Courses from the Universty Osnabrück

    Attributes:
        openAIKey (string): The OpenAI API Key which the model will use to gain access to the API
    """

    def __init__(self, openAIKey, database_structure, example_content_retrieval, system_content_retrieval, system_content_generation, database_path):
        """
        Initialize a instance of the RAG_Model
        
        Args:
            openAIKey (string): The OpenAI API Key which the model will use to gain access to the API
        """

        self.client = OpenAI(api_key=openAIKey)
        self.database_structure = database_structure
        self.example_content_retrieval = example_content_retrieval
        self.system_content_retrieval = system_content_retrieval
        self.system_content_generation = system_content_generation
        self.conn = sqlite3.connect(database_path)
        self.model = "gpt-4o-mini"
        self.example_content = "No example content has been generated yet"
        self.query_list = []

    def __is_valid_sql(self, query):
        """
        Parses a string to check if it is a valid query

        Args:
            query (string): The query which is to be parsed

        Returns: 
            boolean: Wether ot not the query is valid
        """
        try:
            sqlparse.parse(query)
            return True
        except Exception as e:
            print(f"SQL Syntax Error {e}")
            return False

    def __process_input(self, prompt):
        """
        Makes a decision on wether the input requires a query or not, based on the context of the conversation.

        Args:
            prompt (list of strings): A list of input and output strings the model and user have generated, provides context to the model

        Returns:
            string: The decision in form of a string
        """
        completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role":"system", "content":"It is your Task to make the decision, if the latest prompt is a request, that based on the context should be turned into a query, or something different. Consider the given database structure. If you are asked to find something it is likely a Query request. However, if there are no courses related to the topic, that is asked about, you need to return query. It is a binary decision, so only a query or not a query. If you deem it to be a something which requires a query return the message 'Query', else return 'Proceed'. You are a model which is supposed to search over a database, which includes courses of the University Osnabrück."},
                    {"role":"assistant", "content": self.database_structure},
                    *prompt
                    ]
                )
        #print(completion.choices[0].message.content)
        return completion.choices[0].message.content

    def __retrieval(self, prompt, validity=" "):
        """
        Retrieves possible courses which fit the criteria from the underlying database

        Args:
            prompt (string): The prompt out of which the course retrieval conditions are created

        Returns:
            string: The SQL query to be used for retrieval
        """

        def check_for_ects(query_string):
            pattern = r'ects'
            return bool(re.search(pattern, query_string, re.IGNORECASE))

        def contains_select(statement):
            pattern = r'\bSELECT\b'
            return bool(re.search(pattern, statement))

        course_abbreviations = "Here is a list of common abbreviations for Cognitive Science modules: AI = Artificial Intelligence, NS = Neuroscience, NI = Neuroinformatics, INF = Informatics/Computer Science, MAT = Mathematics, MCS = Methods of Cognitive Science, CL = Computational Linguistics, PHIL = Philosophy, CNP = Cognitive Neuro Psychology. "
       # summarization = self.__summarize(prompt)
       # context = self.__pick_context(prompt)
        is_valid = False
        while is_valid == False:
            completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role":"system", "content": self.system_content_retrieval},
                        {"role":"assistant", "content": self.example_content_retrieval},
                        {"role":"assistant", "content": self.database_structure},
                        {"role":"assistant", "content": course_abbreviations},
                        {"role":"assistant", "content": validity},
                        # *prompt
                        # {"role":"assistant", "content": summarization},
                        prompt
                        # {"role":"assistant","content": context}
                        ],
                    temperature=0
                    #top_p=0.2
                    )
            ans_string = completion.choices[0].message.content
            #print(ans_string)
            stripped_str = re.sub(r";(?![^;]*$)", "UNION ", ans_string)
            #stripped_str = stripped_str + ";"

            if self.__is_valid_sql(stripped_str) and not check_for_ects(stripped_str) and contains_select(stripped_str):
                is_valid = True
                self.query_list.append(stripped_str)
            elif not is_valid and validity != " ":
                print("Failsafe for SQL Query Generation")
                self.query_list.append("SELECT * FROM SommerSemester2025")
                return  "SELECT * FROM SommerSemester2025"
            else:
                print("Trying again for SQL Query Generation")
                validity = stripped_str +  ": This prompt does not work on the current DB structure, try again"

        return stripped_str

    def __exemplify(self, series):
        """
        Turns the series into a concatenated string of format "{name}:{value}", for all elements in the series

        Args:
            series (pandas series): The series, which is to be turned into a string

        Returns:
            string: The concatenated string
        """
        example = ""
        for name in series.index.tolist():
            value = series[name]
            example = example + f"{name}:{value}"
        return example

    def __create_example_list(self, example_df):
        """
        Calls exemplify on all rows of a dataframe

        Args:
            example_df (dataframe): The dataframe which is to be turned into examples

        Returns:
            string: a single string with each exemplified row of the dataframe joined by a newline character 
        """
        example_content_list = []
        for i in range(len(example_df)):
            example_content_list.append(self.__exemplify(example_df.loc[i]))
        return "\n".join(example_content_list)
    
    def __generation(self, prompt, example_content_exemplified="No Example Courses handed over"):
        """
        Generates the output to print out based on prompt and given retrieved content

        Args:
            example_content_exemplified (string): The retrieved content which the answer will be based on
            prompt (string): The prompt out of which the example content was generated

        Returns:
            string: The answer which the underlying GPT model generated
        """
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_content_generation},
                {"role": "assistant", "content": self.database_structure},
                {"role": "assistant", "content": example_content_exemplified},
                *prompt
                ],
            stream = True,
            temperature=0.1
            )
        
        return completion
    

    def RAG(self, prompt):
        """
        Runs the RAG process on the passed prompt

        Args:
            prompt (Union[string, list of strings]): The prompts generated by the user and messages of the model, to give context to the model

        Returns:
            string: The answer of the model to the passed prompt
            list of dicts: Dicts of the times it took to execute this function call
        """
        list_prompt = [{"role": m["role"], "content": m["content"]}for m in prompt]
        if len(list_prompt) <= 0:
            return "Hello, how can I help you?", None
        else:
            times_this_iter = []
            start_time = time.time()
            decision = self.__process_input(list_prompt)
            end_time = time.time()
            times_this_iter.append({"time_for_decision_process": end_time - start_time})
            if decision.lower() == "query": 
                start_time = time.time()
                query = self.__retrieval(list_prompt[-1])
                end_time = time.time()
                times_this_iter.append({"time_to_create_query": end_time - start_time})

                df = pd.read_sql_query(query, self.conn)
                self.example_content = self.__create_example_list(df)
                generated_text = self.__generation(list_prompt, self.example_content)
                return generated_text, times_this_iter
            else:
                generated_text = self.__generation(list_prompt, self.example_content)
                return generated_text, times_this_iter
