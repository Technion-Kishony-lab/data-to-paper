
# Import required packages
import pandas as pd
import numpy as np

# Load datasets
df_time_to_infection = pd.read_csv('TimeToInfection.csv')
df_symptoms = pd.read_csv('Symptoms.csv')

# Creating an output text file to print the summary
with open('data_exploration.txt', 'w') as f:
    # Data Size
    f.write("# Data Size\n")
    f.write(f"Time to Infection Data size: {df_time_to_infection.shape[0]} rows, {df_time_to_infection.shape[1]} columns\n")
    f.write(f"Symptoms Data size: {df_symptoms.shape[0]} rows, {df_symptoms.shape[1]} columns\n\n")

    # Summary Statistics
    f.write("# Summary Statistics\n")
    f.write("Time to Infection Data:\n")
    f.write(str(df_time_to_infection.describe(include='all')) + "\n\n")
    f.write("Symptoms Data:\n")
    f.write(str(df_symptoms.describe(include='all')) + "\n\n")
    
    # Categorical Variables
    f.write("# Categorical Variables\n")
    f.write("Time to Infection Data:\n")
    for col in df_time_to_infection.select_dtypes(include=['object']).columns:
        f.write(f"Most common value on {col}: {df_time_to_infection[col].mode()[0]}\n")
    f.write("Symptoms Data:\n")
    for col in df_symptoms.select_dtypes(include=['object']).columns:
        f.write(f"Most common value on {col}: {df_symptoms[col].mode()[0]}\n")
    f.write("\n")

    # Missing Values
    f.write("# Missing Values\n")
    f.write("Time to Infection Data:\n")
    f.write(str(df_time_to_infection.isnull().sum()) + "\n")
    f.write("Symptoms Data:\n")
    f.write(str(df_symptoms.isnull().sum()) + "\n\n")
    
f.close()
