import numpy as np
from openai import OpenAI
import sqlite3
import pandas as pd
import re

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
        self.context_len = 3
        self.example_content = 0

    def __process_input(self, prompt):
        """
        """
        completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role":"system", "content":"It is your Task to make the decision, if the latest prompt is a request that based on the context should be turned into a query, or something different. Consider the given database structure. If somebody asks you for more information on something already in the conversation history, it is not likely to be a query request. If you are asked to find something it is likely a Query request. However, if there are no courses related to the topic that is asked about we need to query. It is a binary decision, so only a query or not a query. If you deem it to be a something which requires a query return the message 'Query', else return 'Proceed'"},
                    {"role":"assistant", "content": self.database_structure},
                    *prompt
                    ]
                )
        print(completion.choices[0].message.content)
        return completion.choices[0].message.content

    def __summarize(self, prompt):
        """
        """
        completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role":"system", "content": "It is your task to summarize the messages given to you, so that it is easily possible to create a SQL Query out of the information for the given Database structure. Try to mostly use 'WHERE module' as part of your query, unless specified otherwise"},
                    {"role":"assistant", "content": self.database_structure},
                    *prompt
                    ],
                temperature=0
                )

            
        print(completion.choices[0].message.content)
        return completion.choices[0].message.content

    def __pick_context(self, prompt):
        """
        """

        completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role":"system", "content": "It is your task to summarize the messages given to you, so that it is easily possible to create a SQL Query out of the information for the given Database structure."},
                   # {"role":"assistant", "content": self.example_content_retrieval},
                    {"role":"assistant", "content": self.database_structure},
                    *prompt
                    ],
                temperature=0
                )
        print(completion.choices[0].message.content)
        return completion.choices[0].message.content

    def __retrieval(self, prompt):
        """
        Retrieves possible courses which fit the criteria from the underlying database

        Args:
            prompt (string): The prompt out of which the course retrieval conditions are created

        Returns:
            string: The SQL query to be used for retrieval
        """
       # summarization = self.__summarize(prompt)
       # context = self.__pick_context(prompt)
        completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role":"system", "content": self.system_content_retrieval},
                    {"role":"assistant", "content": self.example_content_retrieval},
                    {"role":"assistant", "content": self.database_structure},
                   # *prompt
                   # {"role":"assistant", "content": summarization},
                    prompt
                   # {"role":"assistant","content": context}
                    ],
                temperature=0
                #top_p=0.2
                )
        ans_string = completion.choices[0].message.content
        print(ans_string)
        stripped_str = re.sub(r";(?![^;]*$)", "UNION ", ans_string)
        #stripped_str = stripped_str + ";"
        return stripped_str

        #print(completion.choices[0].message.content)
        #return completion.choices[0].message.content


    def __exemplify(self, series):
        """
        Turns the contents of a single row of a Pandas dataframe into a concatenated string

        Args:
            series (series): The series which is to be turned into a string

        Returns:
            example (string): The values of all series fields concatenated together and joined with the newline character
        """

        titel = series['titel']
        veranstaltungsnummer = series['veranstaltungsnummer']
        status = series['status']
        beschreibung = series['beschreibung']
        ects = series['ects']
        sws = series['sws']
        mode = series['mode']
        shortmode = series['shortmode']
        termine = series['termine']
        dozenten = series['dozenten']
        kuerzel = series['kuerzel']
        module = series['module']
        example = f"Titel:{titel}\n" +  f"veranstaltungsnummer:{veranstaltungsnummer}\n" +  f"status:{status}\n" +  f"beschreibung:{beschreibung}\n" +  f"ects:{ects}\n" + f"sws:{sws}\n" + f"mode:{mode}\n" + f"shortmode:{shortmode}\n" f"termine:{termine}\n" f"dozenten:{dozenten}\n" f"kuerzel:{kuerzel}\n" f"module:{module}\n"
        return example

    def __create_example_list(self, example_df):
        """
        Calls exemplify on all rows of a dataframe

        Args:
            example_df (dataframe): The dataframe which is to be turned into examples

        Returns:
            string: a single string with each element of the list joined by a newline character 
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
          #  stream = True,
            temperature=0.1
            )
        return completion.choices[0].message.content
    
    def RAG(self, prompt):
        """
        The function to call from the outside in order to generate content

        Args:
            prompt (string): The question to ask the model

        Returns:
            string: The output of the __generation function
        """
        list_prompt = [{"role": m["role"], "content": m["content"]}for m in prompt]
        print(len(list_prompt))
        context_window = (0,0)
        if len(list_prompt) <= 0:
            return "Hello, how can I help you?"
        elif len(list_prompt) < self.context_len:
            context_window = (0, len(list_prompt)-1)
            decision = self.__process_input(list_prompt[-2:])
            if decision.lower() == "query":
                df = pd.read_sql_query(self.__retrieval(list_prompt[-2:]), self.conn)
                example_content = self.__create_example_list(df)
                return self.__generation(list_prompt[context_window[0]:context_window[1]], example_content)
            else:
                return self.__generation(list_prompt[context_window[0]:context_window[1]])
        else:
            context_window = (-1-self.context_len, -1)
            decision = self.__process_input(list_prompt[-2:])
            if decision.lower() == "query":
                df = pd.read_sql_query(self.__retrieval(list_prompt[-2:]), self.conn)
                self.example_content = self.__create_example_list(df)
                return self.__generation(list_prompt[context_window[0]:context_window[1]], self.example_content)
            else:
                return self.__generation(list_prompt[context_window[0]:context_window[1]], self.example_content)   
       # example_content = self.__create_example_list(df)
       # print(example_content)
       # return self.__generation(example_content, list_prompt[context_window[0]:context_window[1]])

    def RAG(self, prompt):
        """
        """
        list_prompt = [{"role": m["role"], "content": m["content"]}for m in prompt]
        print(len(list_prompt))
        if len(list_prompt) <= 0:
            return "Hello, how can I help you?"
        else:
            decision = self.__process_input(list_prompt)
            if decision.lower() == "query": 
                df = pd.read_sql_query(self.__retrieval(list_prompt[-1]), self.conn)
                example_content = self.__create_example_list(df)
                return self.__generation(list_prompt, example_content)
            else:
                return self.__generation(list_prompt)
