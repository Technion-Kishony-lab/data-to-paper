# flake8: noqa

data_description = """
(1) DIAGNOSES_ICD.csv: a text file containing clinical diagnostic codes for each patient. 
Each line indicates a diagnostic event where a given patient was diagnosed with a specific clinical diagnostic. 

The file has 4 columns: 
#1 row ID (row_id)
#2 Subject ID (subject_id)
#3 Hospital admission ID (hadm_id)
#4 a sequential number of the diagnostic for each subject (seq_num)
#5 The diagnostic ICD9 code, formatted without dots (icd9_code)

Here for example is the head of the file:
```  
ROW_ID, SUBJECT_ID, HADM_ID, SEQ_NUM, ICD9_CODE
1297,109,172335,1,"40301"
1298,109,172335,2,"486"
1299,109,172335,3,"58281"
```

(2) PATIENTS.csv: a text file containing patient demographics. 
Each line indicates a patient. 

The file has 7 columns, the important ones for us are the second and third columns that provide the patient id (SUBJECT_ID)
and the gender (GENDER).

Here for example is the head of the file:
```
ROW_ID, SUBJECT_ID, GENDER, DOB, DOD, DOD_HOSP, DOD_SSN, EXPIRE_FLAG
631,668,"F",2096-08-18 00:00:00,2183-07-10 00:00:00,2183-07-10 00:00:00,2183-07-10 00:00:00,1
632,669,"M",2121-10-20 00:00:00,2182-07-31 00:00:00,2182-07-31 00:00:00,2182-07-31 00:00:00,1
633,670,"M",2080-09-30 00:00:00,2161-02-15 00:00:00,2161-02-15 00:00:00,2161-02-22 00:00:00,1
```

```

"""

goal_description = """
I am interested identifying diagnostic codes that have different "clinical meaning" for males vs females.  
In particular, I would like to find codes that have gender-dependent context (GDC codes), namely diagnostic codes that 
are used in different clinical context in men versus women. 
For example, a code X is a GDC code if it tends to appear in proximity to code Y in female and in proximity to a different code Z in males.  
Note that a code can be GDC, despite being used in similar frequencies in males and in females.
"""
