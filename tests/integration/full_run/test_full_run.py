import os
from pathlib import Path

from data_to_paper.base_steps.run_all_steps import set_project_and_run
from data_to_paper.research_types.toy_example.steps_runner import ToyStepsRunner

CURRENT_DIR = Path(__file__).parent
project_directory = CURRENT_DIR / 'project' / 'prime_numbers'
correct_output_directory = CURRENT_DIR / 'correct_files'

def compare_files(file1: Path, file2: Path):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        assert f1.read() == f2.read()


def test_toy_example(tmpdir):
    output_directory = Path(tmpdir)
    # copy openai_responses.txt from correct_output_directory to output_directory
    os.system(f'cp {correct_output_directory / "openai_responses.txt"} {output_directory}')
    set_project_and_run(ToyStepsRunner, project_directory, output_directory)
    files = ['paper.tex']
    for file in files:
        compare_files(output_directory / file, correct_output_directory / file)
