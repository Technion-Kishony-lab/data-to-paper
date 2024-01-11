
import pandas as pd

def explore_data(df):
    with open('data_exploration.txt', 'w') as f:
        # Data Size
        f.write("# Data Size\n")
        f.write(f"Number of rows: {df.shape[0]}\n")
        f.write(f"Number of columns: {df.shape[1]}\n\n")

        # Summary Statistics
        f.write("# Summary Statistics\n")
        f.write(df.describe().to_string() + "\n\n")

        # Categorical Variable
        f.write("# Categorical Variables\n")
        f.write(df['sex'].value_counts().to_string() + "\n\n")

        # Missing Values
        f.write("# Missing Values\n")
        f.write(df.isnull().sum().to_string() + "\n\n")

def load_and_explore_data(file):
    df = pd.read_csv(file)
    explore_data(df)

load_and_explore_data('tracheal_tube_insertion.csv')
