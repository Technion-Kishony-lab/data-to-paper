
import pandas as pd

# Specify the path to the "TimeToInfection.csv" and "Symptoms.csv" datasets.
time_to_infection_filepath = "TimeToInfection.csv"
symptoms_filepath = "Symptoms.csv"

# Load the datasets into pandas DataFrames.
time_to_infection_df = pd.read_csv(time_to_infection_filepath)
symptoms_df = pd.read_csv(symptoms_filepath)

# Create a summary of the data.
summary = open("data_exploration.txt", "w")

# Data Size
summary.write("# Data Size\n")
summary.write(f"TimeToInfection.csv: {time_to_infection_df.shape[0]} rows, {time_to_infection_df.shape[1]} columns\n")
summary.write(f"Symptoms.csv: {symptoms_df.shape[0]} rows, {symptoms_df.shape[1]} columns\n\n")

# Summary Statistics
summary.write("# Summary Statistics\n")
summary.write(f"{time_to_infection_df.describe(include='all')}\n\n")
summary.write(f"{symptoms_df.describe(include='all')}\n\n")

# Categorical Variables
summary.write("# Categorical Variables (Top 5 categories including unvaccinated represented as '')\n")
for column in time_to_infection_df.select_dtypes(include=['object', 'category']).columns:
    summary.write(f"{column}: {time_to_infection_df[column].value_counts(dropna=False).nlargest(5).to_string()}\n")
for column in symptoms_df.select_dtypes(include=['object', 'category']).columns:
    summary.write(f"{column}: {symptoms_df[column].value_counts(dropna=False).nlargest(5).to_string()}\n")
summary.write("\n")

# Missing Values
summary.write("# Missing Values\n")
summary.write(f"TimeToInfection.csv: {time_to_infection_df.isnull().sum().to_string()}\n\n")
summary.write(f"Symptoms.csv: {symptoms_df.isnull().sum().to_string()}\n")

# Interval Lengths
summary.write("# Interval Lengths\n")
time_to_infection_df['interval_length'] = time_to_infection_df['day_interval_stop'] - time_to_infection_df['day_interval_start']
summary.write(f"Interval length statistics: {time_to_infection_df['interval_length'].describe().to_string()}\n")

# Close the file
summary.close()
