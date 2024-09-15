"""
This script allows manually running a GPT-generated code snippet in the correct context.

Paste the code into the `gpt_code` function.
Specify:
- the `code_converser` that created the GPT code.
- the `run_folder` where the code will be run (where the data is stored).
    If not provided, the code will run in the default run_folder (FOLDER_FOR_RUN).
"""
from data_to_paper.env import FOLDER_FOR_RUN
from data_to_paper.research_types.hypothesis_testing.coding.analysis import DataAnalysisCodeProductsGPT
from data_to_paper.run_gpt_code.run_code_in_context import run_code_in_context

# specify the converser that created the gpt code:
code_converser_cls = DataAnalysisCodeProductsGPT

# specify the run folder where the code will be run:
run_folder = FOLDER_FOR_RUN  # will run in the 'temp_run' folder


def gpt_code():
    # COPY HERE THE GPT CODE
    pass


if __name__ == '__main__':
    code_converser = code_converser_cls()
    results = run_code_in_context(gpt_code,
                                  code_converser=code_converser,
                                  run_folder=run_folder)
    _, _, _, exception = results
    print(exception)
