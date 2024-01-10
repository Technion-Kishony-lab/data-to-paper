
import pandas as pd
import numpy as np

# Read the data
data = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

with open("data_exploration.txt", "w") as file:
    ## Data Size
    file.write("# Data Size\n")
    file.write("This section provides information on the scale of our data.\n")
    file.write(f"Number of Rows: {data.shape[0]}\n")
    file.write(f"Number of Columns: {data.shape[1]}\n\n")

    # Summary Statistics
    file.write("# Summary Statistics\n")
    file.write("This section provides descriptive statistics on the key numerical variables in our data.\n")
    file.write(data.describe().to_string()+"\n\n")

    # Categorical Variables
    file.write("# Categorical Variables\n")
    file.write("This section details the number of unique categories and the most frequently occurring categories for each categorical variable.\n")
    categorical_columns = data.select_dtypes(include=['object']).columns
    for column in categorical_columns:
        file.write(f"{column} has {data[column].nunique()} unique categories. The most often category is: {data[column].mode().values[0]}\n\n")

    ## Missing Values
    file.write("# Missing Values\n")
    file.write("This section details the count of missing and undefined values for each variable.\n")
    file.write(data.isnull().sum().to_string()+"\n\n")

    # Check for specific values that are placeholders for unknown/undefined
    file.write("# Special Numeric Values\n")
    file.write("This section counts special numeric values standing for unknown or undefined in the data.\n")
    special_values = (data == 9999).astype(int).sum()
    file.write(special_values.to_string()+"\n\n")

    ## Specific Variable Averages
    file.write("# Specific Variable Averages\n")
    file.write("This section provides the averages/means of selective numerical variables.\n") 
    file.write("Average/mean of ProlongedRupture (omitting NA values): " + str(data['ProlongedRupture'].dropna().mean()) + "\n") # calculation with neglecting NA values
    file.write("Average/mean of Chorioamnionitis (omitting NA values): " + str(data['Chorioamnionitis'].dropna().mean()) + "\n") # calculation with neglecting NA values
    file.write("Average/mean of SNAPPE_II_SCORE: " + str(data['SNAPPE_II_SCORE'].mean()) + "\n")

file.close()
