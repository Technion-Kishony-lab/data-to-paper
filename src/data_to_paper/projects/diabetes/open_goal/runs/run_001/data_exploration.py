
import pandas as pd

# Load the dataset
data = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Opening the file in write mode
with open("data_exploration.txt", "w") as file:

    # Data Size
    file.write("# Data Size\n")
    file.write(f"Number of rows: {data.shape[0]}\n")
    file.write(f"Number of columns: {data.shape[1]}\n\n")
    
    # Summary Statistics for all variables
    file.write("# Summary Statistics\n")
    summary_statistics = data.describe().to_string(max_rows=10)  # Limit the number of rows displayed
    file.write(summary_statistics + "\n\n")

    # Categorical Variables
    file.write("# Categorical Variables\n")
    categorical_vars = ['Sex', 'Age', 'Education', 'Income']
    for var in categorical_vars:
        file.write(f"{var}:\n")
        value_counts = data[var].value_counts().nlargest(5).to_string()  # Display only the top 5 most common values
        file.write(f"{value_counts}\n\n")
   
    # Missing Values
    file.write("# Missing Values\n")
    # According to the description, there are no missing values in the dataset
    file.write("Not Applicable\n\n")

    # Relevant additional summary: Correlation between variables
    file.write("# Correlation Matrix\n")
    correlation_matrix = data.corr().to_string(max_cols=10)  # Limit the number of columns displayed
    file.write(correlation_matrix + "\n\n")

