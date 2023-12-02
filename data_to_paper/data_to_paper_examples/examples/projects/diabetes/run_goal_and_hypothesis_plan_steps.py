# This runs the code for the writing and debugging experiment
# It should call the `diabetes_data_exploration.py` script with the following parameters:
# - `--model_engine` (`GPT35_TURBO`, `GPT4`, `LLAMA_2_7b`, `LLAMA_2_70b`, `CODELLAMA`)
# - `--output_folder` (the folder where the results should be saved, it should follow the pattern `<model_engine>_run_<run_number>`)
# import os
# import signal
# from subprocess import Popen
# from tqdm import trange
#
# def run_command(command, output_folder):
#     """Function to run a command and redirect its output to suppress or log."""
#     with open(f'/home/talifargan/git_projects/data-to-paper/data_to_paper/data_to_paper_examples/examples/projects/'
#               f'diabetes/outputs/{output_folder}_terminal_output.txt', 'w') as f:
#         process = Popen(command, shell=True, stdout=f, stderr=f, preexec_fn=os.setsid)
#     return process
#
# def main():
#     processes = []
#     try:
#         for model_engine in ["GPT35_TURBO", "LLAMA_2_70b"]:
#             print("_" * 80)
#             print(f"Now evaluating {model_engine}")
#             for run_number in trange(1, 11):
#                 output_folder = f"{model_engine}_goal_and_plan_{run_number}"
#                 command = f"python diabetes_goal_and_plan.py --model_engine {model_engine} --output_folder {output_folder}"
#                 processes.append(run_command(command, output_folder))
#
#         # Wait for all processes to complete
#         for process in processes:
#             process.wait()
#
#     except KeyboardInterrupt:
#         print("\nInterrupted by user, terminating all runs...")
#         for process in processes:
#             os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Send the SIGTERM signal to the process group
#
# if __name__ == '__main__':
#     main()

import os
import signal
from subprocess import Popen
from tqdm import trange

def run_command(command, output_folder):
    """Function to run a command and redirect its output to suppress or log."""
    with open(f'/home/talifargan/git_projects/data-to-paper/data_to_paper/data_to_paper_examples/examples/projects/'
              f'diabetes/outputs/{output_folder}_terminal_output.txt', 'w') as f:
        process = Popen(command, shell=True, stdout=f, stderr=f, preexec_fn=os.setsid)
        process.wait()  # Wait for the process to complete
    return process

def main():
    try:
        for model_engine in ["LLAMA_2_70b"]:
            print("_" * 80)
            print(f"Now evaluating {model_engine}")
            for run_number in trange(2, 3):
                output_folder = f"{model_engine}_goal_and_plan_{run_number}"
                command = f"python diabetes_goal_and_plan.py --model_engine {model_engine} --output_folder {output_folder}"
                run_command(command, output_folder)

    except KeyboardInterrupt:
        print("\nInterrupted by user, terminating all runs...")

if __name__ == '__main__':
    main()
