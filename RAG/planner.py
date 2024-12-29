import pandas as pd
import streamlit as st
import sqlite3

# Defining days and time slots
days = ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"]
times = [f"{hour}:00" for hour in range(8, 20)]

# Setting config to "wide" to fix alignment issue
st.set_page_config(layout="wide")

#Get column for selectbox
conn = sqlite3.connect(st.secrets["rag_params"]["database_path"])
numbers = pd.read_sql_query("SELECT veranstaltungsnummer FROM SommerSemester2023", conn)
numbers = numbers.to_numpy()
# print(numbers.shape)

# Create DataFrame to store events
schedule = pd.DataFrame(index = times, columns = days)

def display_planner():
    container = st.container(border=True)
    st.title("Weekly Schedule")

    cols = st.columns(len(days), gap="medium") # Create columns for each day
    # Loop through each day and create input fields
    for idx, day in enumerate(days):
        with cols[idx]:
            st.header(day)
            for time in times:
                time_key = f"{day}_{time}"
                event = st.selectbox(f"{time}",["Unoccupied", *numbers], key=time_key)
                schedule.at[time, day] = event

# Run application
if __name__ == "__main__":
    display_planner()

    
