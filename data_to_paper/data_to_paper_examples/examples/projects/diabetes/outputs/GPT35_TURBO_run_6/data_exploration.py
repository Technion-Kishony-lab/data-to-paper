
import pandas as pd

# Load the dataset
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Open the output file
with open('data_exploration.txt', 'w') as f:

    # Data Size
    f.write("# Data Size\n")
    f.write(f"Number of rows: {len(df)}\n")
    f.write(f"Number of columns: {len(df.columns)}\n\n")

    # Summary Statistics
    f.write("# Summary Statistics\n")
    f.write(df.describe().to_string() + "\n\n")

    # Categorical Variables
    f.write("# Categorical Variables\n")
    categorical_vars = ['Diabetes_binary', 'HighBP', 'HighChol', 'CholCheck', 'Smoker', 'Stroke',
                        'HeartDiseaseorAttack', 'PhysActivity', 'Fruits', 'Veggies', 'HvyAlcoholConsump',
                        'AnyHealthcare', 'NoDocbcCost', 'GenHlth', 'DiffWalk', 'Sex', 'Age', 'Education', 'Income']
    for col in categorical_vars:
        value_counts = df[col].astype(str).value_counts()
        f.write(col + "\n")
        f.write(value_counts.to_string() + "\n\n")

    # Missing Values
    f.write("# Missing Values\n")
    f.write(df.isnull().sum().to_string() + "\n\n")

    # Close the output file
    f.close()
    
assert True, "Data exploration summary written to data_exploration.txt"
