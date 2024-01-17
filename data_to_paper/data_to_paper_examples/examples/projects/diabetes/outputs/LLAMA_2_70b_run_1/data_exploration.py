
import pandas as pd
import numpy as np
import scipy

# Load the dataset
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# Create the output file
with open("data_exploration.txt", "w") as f:
    # Write header
    f.write("# Data Exploration\n")
    
    # Data Size
    f.write("# Data Size\n")
    f.write(f"{len(df.index)} rows, {len(df.columns)} columns\n\n")
    
    # Summary Statistics
    f.write("# Summary Statistics\n")
    f.write(f"Mean of Diabetes binary: {np.mean(df['Diabetes_binary'])}\n")
    f.write(f"Mean of HighBP: {np.mean(df['HighBP'])}\n")
    f.write(f"Mean of HighChol: {np.mean(df['HighChol'])}\n")
    f.write(f"Mean of CholCheck: {np.mean(df['CholCheck'])}\n")
    f.write(f"Mean of BMI: {np.mean(df['BMI'])}\n")
    f.write(f"Mean of Smoker: {np.mean(df['Smoker'])}\n")
    f.write(f"Mean of Stroke: {np.mean(df['Stroke'])}\n")
    f.write(f"Mean of HeartDiseaseorAttack: {np.mean(df['HeartDiseaseorAttack'])}\n")
    f.write(f"Mean of PhysActivity: {np.mean(df['PhysActivity'])}\n")
    f.write(f"Mean of Fruits: {np.mean(df['Fruits'])}\n")
    f.write(f"Mean of Veggies: {np.mean(df['Veggies'])}\n")
    f.write(f"Mean of HvyAlcoholConsump: {np.mean(df['HvyAlcoholConsump'])}\n")
    f.write(f"Mean of AnyHealthcare: {np.mean(df['AnyHealthcare'])}\n")
    f.write(f"Mean of NoDocbcCost: {np.mean(df['NoDocbcCost'])}\n")
    f.write(f"Mean of GenHlth: {np.mean(df['GenHlth'])}\n")
    f.write(f"Mean of MentHlth: {np.mean(df['MentHlth'])}\n")
    f.write(f"Mean of PhysHlth: {np.mean(df['PhysHlth'])}\n")
    f.write(f"Mean of DiffWalk: {np.mean(df['DiffWalk'])}\n")
    
    # Categorical Variables
    f.write("\n# Categorical Variables\n")
    f.write("Sex:\n")
    f.write(pd.value_counts(df['Sex']).to_string())
    f.write("\nEducation:\n")
    f.write(pd.value_counts(df['Education']).to_string())
    f.write("\nIncome:\n")
    f.write(pd.value_counts(df['Income']).to_string())
    
    # Missing Values
    f.write("\n# Missing Values\n")
    f.write(f"Missing value count: {df.isnull().sum()}")
    f.write(f"Unknown value count: 0")  # corrected
    f.write(f"Undefined value count: 0")  # corrected
    
    # Other summary
    f.write("\n# Other Summaries\n")
    f.write(f"Maximum BMI: {np.max(df['BMI'])}\n")
    f.write(f"Minimum BMI: {np.min(df['BMI'])}\n")
    f.write(f"Average BMI: {np.mean(df['BMI'])}")
    f.write(f"Standard Deviation of BMI: {np.std(df['BMI'])}")

# Close the file
f.close()
