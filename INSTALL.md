## Install data-to-paper

### Install for users
1. pip install the package, run `pip install data-to-paper`.
2. Install dependencies (see below).
3. Add environment variables for API keys (see below).
4. Check dependencies and keys (see below).
5. Run the app, run `data-to-paper`.


### Install for developers

1. Clone the repo, run `git clone https://github.com/Technion-Kishony-lab/data-to-paper`.
2. Create a conda environment, run `conda create -n data-to-paper python=3.11`.
3. Activate the newly created environment, run `conda activate data-to-paper`.
4. Enter the repo root folder, run `cd data-to-paper`.
5. Install the app and further required packages, run `pip install -e .`.
6. Install dependencies (see below).
7. Add environment variables for API keys (see below).
8. Check dependencies and keys (see below).

### Install dependencies
1. Install pandoc (follow instructions at [Pandoc Installation](https://pandoc.org/installing.html)).
2. Install all the required packages for compiling LaTeX:

   - **On debian-based systems**:
     ```
     sudo apt-get update && \
     sudo apt-get install -y --no-install-recommends \
     texlive-latex-base \
     texlive-latex-extra \
     texlive-fonts-recommended
     ```
   - **On MacOS**:
     - Ensure you have Homebrew installed (see [Homebrew Installation](https://brew.sh)).
     - Install MacTeX with the following command:
       ```
       brew install --cask mactex-no-gui
       ```
     - After installation, you may need to add the TeX binaries to your PATH!
   - **On Windows**:
     - Download and install MiKTeX from [MiKTeX Download Page](https://miktex.org/download).
     - During installation, select 'Yes' when asked to install missing packages on-the-fly.
     - After installation, you may need to add the TeX binaries to your PATH!


### Add environment variables for API keys

You need to define the following environment variables in your system:
- OPENAI_API_KEY
- SEMANTIC_SCHOLAR_API_KEY
- DEEPINFRA_API_KEY (optional)

To set up the keys on your system, see 
[openai instructions](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety)


### Check dependencies and keys
To test installation of dependencies and check the API keys, run the following command:
```shell
data-to-paper-chkres
```
