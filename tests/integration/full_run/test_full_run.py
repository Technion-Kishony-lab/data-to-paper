
import shutil
from pathlib import Path

from data_to_paper.base_steps.run_all_steps import set_project_and_run
from data_to_paper.research_types.toy_example.steps_runner import ToyStepsRunner

CURRENT_DIR = Path(__file__).parent
project_directory = CURRENT_DIR / 'project' / 'prime_numbers'
correct_output_directory = CURRENT_DIR / 'correct_files'


def compare_files(file1: Path, file2: Path):
    with open(file1, 'r', encoding='utf-8') as f1:
        content1 = f1.read()
    with open(file2, 'r', encoding='utf-8') as f2:
        content2 = f2.read()
    assert content1 == content2


def test_toy_example(tmpdir):
    output_directory = Path(tmpdir)
    # copy openai_responses.txt from correct_output_directory to output_directory
    shutil.copy(correct_output_directory / "response_recordings.json", output_directory)
    set_project_and_run(ToyStepsRunner, project_directory, output_directory)
    files = ['paper.tex']
    for file in files:
        compare_files(output_directory / file, correct_output_directory / file)
        # Overriding the correct output files with the new files
        # shutil.copy(output_directory / file, correct_output_directory / file)
