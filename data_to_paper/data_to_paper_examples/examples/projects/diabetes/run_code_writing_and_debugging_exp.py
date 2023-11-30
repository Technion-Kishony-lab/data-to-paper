# This runs the code for the writing and debugging experiment
# It should call the `diabetes_data_exploration.py` script with the following parameters:
# - `--model_engine` (`GPT35_TURBO`, `GPT4`, `LLAMA_2_7b`, `LLAMA_2_70b`, `CODELLAMA`)
# - `--output_folder` (the folder where the results should be saved, it should follow the pattern `<model_engine>_run_<run_number>`)
import os
import sys
import signal
from subprocess import Popen
from tqdm import trange

def run_command(command):
    """Function to run a command and redirect its output to suppress or log."""
    with open(os.devnull, 'w') as devnull:  # Replace os.devnull with a file path like 'output.log' to save output
        process = Popen(command, shell=True, stdout=devnull, stderr=devnull, preexec_fn=os.setsid)
    return process

def main():
    processes = []
    try:
        for model_engine in ["GPT4", "GPT35_TURBO", "LLAMA_2_7b", "LLAMA_2_70b", "CODELLAMA"]:
            print("_" * 80)
            print(f"Now evaluating {model_engine}")
            for run_number in trange(1,2):
                output_folder = f"{model_engine}_run_{run_number}"
                command = f"python diabetes_data_exploration.py --model_engine {model_engine} --output_folder {output_folder}"
                processes.append(run_command(command))

        # Wait for all processes to complete
        for process in processes:
            process.wait()

    except KeyboardInterrupt:
        print("\nInterrupted by user, terminating all runs...")
        for process in processes:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)  # Send the SIGTERM signal to the process group

if __name__ == '__main__':
    main()