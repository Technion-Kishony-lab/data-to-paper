
import pandas as pd

# Read the dataset
df = pd.read_csv('diabetes_binary_health_indicators_BRFSS2015.csv')

# Open the output file
output_file = open('data_exploration.txt', 'w')

# Data Size
output_file.write("# Data Size\n")
output_file.write("Number of rows: {}\n".format(df.shape[0]))
output_file.write("Number of columns: {}\n\n".format(df.shape[1]))

# Summary Statistics
output_file.write("# Summary Statistics\n")
output_file.write(df.describe().to_string() + "\n\n")

# Categorical Variables
output_file.write("# Categorical Variables\n")
categorical_vars = ['Diabetes_binary', 'HighBP', 'HighChol', 'CholCheck', 'Smoker',
                    'Stroke', 'HeartDiseaseorAttack', 'PhysActivity', 'Fruits',
                    'Veggies', 'HvyAlcoholConsump', 'AnyHealthcare', 'NoDocbcCost',
                    'GenHlth', 'DiffWalk', 'Sex', 'Age', 'Education', 'Income']

for var in categorical_vars:
    output_file.write("Most common values for variable '{}':\n".format(var))
    output_file.write(df[var].value_counts().head().to_string() + "\n\n")

# Missing Values
output_file.write("# Missing Values\n")
output_file.write("Counts of missing values:\n")
output_file.write(df.isnull().sum().to_string() + "\n\n")

# Close the output file
output_file.close()
