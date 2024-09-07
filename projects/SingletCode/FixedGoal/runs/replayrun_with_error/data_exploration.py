
import pandas as pd

def summarize_data(file_paths, output_file):
    summary = []

    for file_path in file_paths:
        # Load the dataset
        data = pd.read_csv(file_path)
        
        summary.append(f"# Summary of {file_path}\n")
        
        # Data Size
        summary.append("# Data Size\n")
        summary.append(f"Number of Rows: {data.shape[0]}\n")
        summary.append(f"Number of Columns: {data.shape[1]}\n")
        summary.append("\n")
        
        # Summary Statistics
        summary.append("# Summary Statistics\n")
        summary.append(data.describe().to_string())
        summary.append("\n\n")
        
        # Categorical Variables
        summary.append("# Categorical Variables\n")
        categorical_cols = data.select_dtypes(include=['object']).columns
        if len(categorical_cols) > 0:
            for col in categorical_cols:
                summary.append(f"Column: {col}\n")
                most_common_val = data[col].mode()[0]
                summary.append(f"Most Common Value: {most_common_val}\n")
                summary.append("\n")
        else:
            summary.append("# Not Applicable\n")
        summary.append("\n")

        # Missing Values
        summary.append("# Missing Values\n")
        missing_values = data.isnull().sum()
        for col, count in missing_values.items():
            summary.append(f"{col}: {count}\n")
        
        # Check for any special numeric values that stand for unknown/undefined
        special_numeric = data.isin([-1, 9999]).sum()
        if special_numeric.any():
            summary.append("\n# Special Numeric Values Indicating Unknown/Undefined\n")
            for col, count in special_numeric.items():
                if count > 0:
                    summary.append(f"{col}: {count}\n")
        summary.append("\n")

    # Write the summary to the output file
    with open(output_file, "w") as f:
        f.writelines(summary)

# File paths
files = ["barcodedNonBarcoded_AUPRC_AUROC_TNR.csv", "TNR_plotted_formatted.csv"]
output_file = "data_exploration.txt"

# Summarize data for both files
summarize_data(files, output_file)
