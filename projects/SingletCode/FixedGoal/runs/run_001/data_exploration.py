
import pandas as pd

# Load the datasets
file1 = "barcodedNonBarcoded_AUPRC_AUROC_TNR.csv"
file2 = "TNR_plotted_formatted.csv"

df1 = pd.read_csv(file1)
df2 = pd.read_csv(file2)

# Create output text file
with open("data_exploration.txt", "w") as file:
    # Data Size
    file.write("# Data Size\n")
    file.write("File 1 - barcodedNonBarcoded_AUPRC_AUROC_TNR.csv:\n")
    file.write(f"Number of Rows: {df1.shape[0]}\n")
    file.write(f"Number of Columns: {df1.shape[1]}\n\n")
    file.write("File 2 - TNR_plotted_formatted.csv:\n")
    file.write(f"Number of Rows: {df2.shape[0]}\n")
    file.write(f"Number of Columns: {df2.shape[1]}\n\n")
    
    # Summary Statistics
    file.write("# Summary Statistics\n")
    file.write("File 1 - barcodedNonBarcoded_AUPRC_AUROC_TNR.csv:\n")
    file.write(str(df1.describe()) + "\n\n")
    file.write("File 2 - TNR_plotted_formatted.csv:\n")
    file.write(str(df2.describe()) + "\n\n")
    
    # Categorical Variables
    file.write("# Categorical Variables\n")
    categorical_vars1 = df1.select_dtypes(include=['object']).columns
    categorical_vars2 = df2.select_dtypes(include=['object']).columns
    
    if not categorical_vars1.empty:
        file.write("File 1 - barcodedNonBarcoded_AUPRC_AUROC_TNR.csv:\n")
        for var in categorical_vars1:
            file.write(f"{var}: Most common value: {df1[var].mode()[0]} (Count: {df1[var].value_counts().max()})\n")
        file.write("\n")
    else:
        file.write("File 1 - barcodedNonBarcoded_AUPRC_AUROC_TNR.csv:\nNot Applicable\n\n")
    
    if not categorical_vars2.empty:
        file.write("File 2 - TNR_plotted_formatted.csv:\n")
        for var in categorical_vars2:
            file.write(f"{var}: Most common value: {df2[var].mode()[0]} (Count: {df2[var].value_counts().max()})\n")
        file.write("\n")
    else:
        file.write("File 2 - TNR_plotted_formatted.csv:\nNot Applicable\n\n")
    
    # Missing Values
    file.write("# Missing Values\n")
    file.write("File 1 - barcodedNonBarcoded_AUPRC_AUROC_TNR.csv:\n")
    missing_values1 = df1.isnull().sum()
    file.write(str(missing_values1[missing_values1 > 0]) + "\n\n")
    
    file.write("File 2 - TNR_plotted_formatted.csv:\n")
    missing_values2 = df2.isnull().sum()
    file.write(str(missing_values2[missing_values2 > 0]) + "\n\n")
    
    # Other Summary (if any)
    # In this case, no additional summaries deemed relevant.
    # file.write("# <title of other summary>\n")
    # file.write("<Add any other summary of the data you deem relevant>\n\n")
