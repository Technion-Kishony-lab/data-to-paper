# flake8: noqa
from typing import List

from scientistgpt.data_file_description import DataFileDescription
from scientistgpt.utils import dedent_triple_quote_str


data_file_descriptions: List[DataFileDescription] = [
    DataFileDescription(
        file_path='DIAGNOSES_ICD.csv',
        description=dedent_triple_quote_str("""
            a csv file containing clinical diagnostic codes for each patient. 
            Each line indicates a diagnostic event where a given patient was diagnosed with a specific clinical diagnostic. 
            
            The file has 4 columns: 
            #1 row ID (row_id)
            #2 Subject ID (subject_id)
            #3 Hospital admission ID (hadm_id)
            #4 a sequential number of the diagnostic for each subject (seq_num)
            #5 The diagnostic ICD9 code, formatted without dots (icd9_code)
            """)),

    DataFileDescription(
        file_path='PATIENTS.csv',
        description=dedent_triple_quote_str("""
            a csv file containing patient demographics. 
            Each line indicates a patient. 
            
            The file has 7 columns, the important ones for us are the second and third columns that provide the patient id (SUBJECT_ID)
            and the gender (GENDER).
            """)),
]


research_goal = """
I am interested identifying diagnostic codes that have different "clinical meaning" for males vs females.  
In particular, I would like to find codes that have gender-dependent context (GDC codes), namely diagnostic codes that 
are used in different clinical context in men versus women. 
For example, a code X is a GDC code if it tends to appear in proximity to code Y in female and in proximity to a different code Z in males.  
Note that a code can be GDC, despite being used in similar frequencies in males and in females.
"""

simpler_research_goal = """
I am interested identifying diagnostic codes that are gender biased, namely that are man-enriched or woman-enriched.  
"""
