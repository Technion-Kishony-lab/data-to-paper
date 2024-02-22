
# IMPORT
import pandas as pd
from statsmodels.formula.api import logit
import pickle

# LOAD DATA
df = pd.read_csv("diabetes_binary_health_indicators_BRFSS2015.csv")

# DATASET PREPARATIONS
# No dataset preparations are needed.

# DESCRIPTIVE STATISTICS
## Table 0: "Descriptive statistics of Physical Activity and Chronic Health Conditions stratified by Whether Having Diabetes"
desc_stats = df.groupby('Diabetes_binary').agg({"PhysActivity": "mean", 
                                                "HighBP": "mean",
                                                "HighChol": "mean",
                                                "HeartDiseaseorAttack": "mean"}).reset_index()
desc_stats.set_index('Diabetes_binary', inplace=True)
desc_stats.index.names = ['Diabetes Status (0=No, 1=Yes)']
desc_stats.index = desc_stats.index.map({0: 'No', 1: 'Yes'})  # Change the row index to categorical labels
desc_stats.to_pickle('table_0.pkl')

# PREPROCESSING 
# No preprocessing is needed, because the data is already in a structured format with binary variables and continuous variables are not being used in the analysis

# ANALYSIS
## Table 1: "Association between physical activity and high blood pressure in individuals with diabetes"
model_highBP = logit("HighBP ~ PhysActivity + Age + Sex + BMI + Smoker", data=df[df["Diabetes_binary"]==1]).fit()
summary_df = model_highBP.summary2().tables[1]
df1 = summary_df.loc[['PhysActivity'], :]
df1.to_pickle('table_1.pkl')

## Table 2: "Association between physical activity and high cholesterol in individuals with diabetes"
model_highChol = logit("HighChol ~ PhysActivity + Age + Sex + BMI + Smoker", data=df[df["Diabetes_binary"]==1]).fit()
summary_df = model_highChol.summary2().tables[1]
df2 = summary_df.loc[['PhysActivity'], :]
df2.to_pickle('table_2.pkl')

## Table 3: "Association between physical activity and coronary heart disease in individuals with diabetes"
model_heartDisease = logit("HeartDiseaseorAttack ~ PhysActivity + Age + Sex + BMI + Smoker", data=df[df["Diabetes_binary"]==1]).fit()
summary_df = model_heartDisease.summary2().tables[1]
df3 = summary_df.loc[['PhysActivity'], :]
df3.to_pickle('table_3.pkl')

# SAVE ADDITIONAL RESULTS
additional_results = {
 'Total number of observations': len(df),
 'Accuracy of high blood pressure model': model_highBP.prsquared,
 'Accuracy of high cholesterol model': model_highChol.prsquared,
 'Accuracy of coronary heart disease model': model_heartDisease.prsquared
}

with open('additional_results.pkl', 'wb') as f:
 pickle.dump(additional_results, f)
