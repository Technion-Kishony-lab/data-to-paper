

import pandas as pd
import numpy as np

# Load the data
data = pd.read_csv("meconium_nicu_dataset_preprocessed_short.csv")

# Open a new text file in writing mode
with open("data_exploration.txt", "w") as outfile:

    # Measure of the scale of our data
    outfile.write("# Data Size:\n")
    outfile.write(f"Number of rows: {data.shape[0]}\n")
    outfile.write(f"Number of columns: {data.shape[1]}\n\n")

    # Missing Values: count of missing, unknown or undefined values
    outfile.write("# Missing Values\n")
    missing = data.isnull().sum()
    outfile.write(f"{missing}\n\n")

    # Summary statistics
    outfile.write("# Summary Statistics of Key Variables\n")
    key_variables = ['AGE', 'GRAVIDA', 'PARA', 'GestationalAge', 'BirthWeight', 'APGAR1', 'APGAR5', 'AntibioticsDuration', 'LengthStay', 'SNAPPE_II_SCORE']
    summary_stats = data[key_variables].describe()
    outfile.write(f"{summary_stats}\n\n")

    # Categorical Variables: list of categorical variables and their most common values
    outfile.write("# Categorical Variables\n")
    categorical_variables = data.select_dtypes(include='object')
    for column in categorical_variables:
        outfile.write(f"\nMost common categories for {column} (category: count):\n{categorical_variables[column].value_counts()}\n\n")

    # Calculations that skip missing values.
    outfile.write("\n# Calculated Averages for Some Variables\n")
    ProlongedRupture_avg = data["ProlongedRupture"].dropna().mean()
    outfile.write(f"Average of 'ProlongedRupture': {ProlongedRupture_avg}\n")

    Chorioamnionitis_avg = data["Chorioamnionitis"].dropna().mean()
    outfile.write(f"Average of 'Chorioamnionitis': {Chorioamnionitis_avg}\n")

    SNAPPE_II_SCORE_avg = data["SNAPPE_II_SCORE"].dropna().mean()
    outfile.write(f"Average of 'SNAPPE_II_SCORE': {SNAPPE_II_SCORE_avg}\n\n")

    # Check special numeric values representing missing or undefined data
    outfile.write("\n# Special Numeric Values:\n")
    special_values = ['EndotrachealSuction', 'CardiopulmonaryResuscitation']
    for var in special_values:
      special_counts = (data[var] == 0).sum()
      outfile.write(f"Special numeric values (zeros representing missing or undefined data) in variable '{var}': {special_counts}\n")

    outfile.write("\n# Data Summary:\n")
    outfile.write("This dataset provides information about the therapies and clinical outcomes of non-vigorous newborns before and after a change in Neonatal Resuscitation Program (NRP) guidelines occurred in 2015.\n")

