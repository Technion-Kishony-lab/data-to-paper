# flake8: noqa

data_description = """
(1) DIAGNOSES_ICD.csv: a text file containing clinical diagnostic codes for each patient. 
Each line indicates a diagnostic event where a given patient was diagnosed with a specific clinical diagnostic. 

The file has 4 columns: 
#1 row ID (row_id)
#2 Subject ID (subject_id)
#3 Hospital admission ID (hadm_id)
#4 a sequential number of the diagnostic for each subject (seq_num)
#5 The diagnostic ICD9 code (icd9_code)

Here for example is the head of the file:
```  
row_id,subject_id,hadm_id,seq_num,icd9_code
112344,10006,142345,1,99591
112345,10006,142345,2,99662
112346,10006,142345,3,5672
```

(2) PATIENTS.csv: a text file containing patient demographics. 
Each line indicates a patient. 

The file has 7 columns, the important ones for us are the second third columns that provide the patient id (patient_id)
and the gender.

Here for example is the head of the file:
```
row_id,subject_id,gender,dob,dod,dod_hosp,dod_ssn,expire_flag
9467,10006,F,2094-03-05 00:00:00,2165-08-12 00:00:00,2165-08-12 00:00:00,2165-08-12 00:00:00,1
9472,10011,F,2090-06-05 00:00:00,2126-08-28 00:00:00,2126-08-28 00:00:00,,1
9474,10013,F,2038-09-03 00:00:00,2125-10-07 00:00:00,2125-10-07 00:00:00,2125-10-07 00:00:00,1
```
"""

goal_description = """
I am interested identifying diagnostic codes that have different "clinical meaning" for males vs females.  
In particular, I would like to find codes that have gender-dependent context (GDC codes), namely diagnostic codes that 
are used in different clinical context in men versus women. 
For example, a code X is a GDC code if it tends to appear in proximity to code Y in female and in proximity
 to a different code Z in males. 
Note that a code can be GDC, despite being used in similar frequencies in males and in females. 
"""
