import os
import pickle
import pandas as pd

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUTS_DIR = os.path.join(MODULE_DIR, "outputs")

if __name__ == '__main__':
    df = pd.DataFrame()
    for model_engine in ["CODELLAMA", "GPT4", "GPT35_TURBO", "LLAMA_2_7b", "LLAMA_2_70b"]:
        for i in range(1, 11):
            df.loc[model_engine, f'debug_attempt{i}'] = None
            run_name = '{}_run_{:01d}'.format(model_engine, i)
            run_dir = os.path.join(OUTPUTS_DIR, run_name)
            if os.path.exists(run_dir):
                debug_attempts_file = os.path.join(run_dir, "writing_and_debugging_attempts.pkl")
                if os.path.exists(debug_attempts_file):
                    with open(debug_attempts_file, 'rb') as f:
                        debug_attempts = pickle.load(f)
                    df.loc[model_engine, f'debug_attempt{i}'] = debug_attempts[1]
    df.to_csv(os.path.join(MODULE_DIR, "writing_and_debugging_attempts.csv"))
    print(df)

