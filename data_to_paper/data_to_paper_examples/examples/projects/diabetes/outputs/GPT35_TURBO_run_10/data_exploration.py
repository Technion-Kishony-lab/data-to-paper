
import pandas as pd

# Read the dataset
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Create an empty string to store the output summary
summary = ""

# Data Size
summary += "# Data Size\n"
summary += f"Number of Rows: {len(df)}\n"
summary += f"Number of Columns: {len(df.columns)}\n\n"

# Summary Statistics
summary += "# Summary Statistics\n"
summary += df.describe().to_string() + "\n\n"

# Categorical Variables
summary += "# Categorical Variables\n"
categorical_vars = ["Diabetes_binary", "HighBP", "HighChol", "CholCheck", "Smoker", "Stroke", "HeartDiseaseorAttack",
                    "PhysActivity", "Fruits", "Veggies", "HvyAlcoholConsump", "AnyHealthcare", "NoDocbcCost",
                    "Sex", "Age", "Education", "Income"]

for var in categorical_vars:
    summary += f"{var}:\n"
    summary += df[var].value_counts().to_string() + "\n\n"

# Missing Values
summary += "# Missing Values\n"
summary += f"Total Missing Values: {df.isnull().sum().sum()}\n\n"

# Save the summary to a file
with open("data_exploration.txt", "w") as file:
    file.write(summary)
