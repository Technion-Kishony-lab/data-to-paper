## Install data_to_paper

### Install on your local machine

1. Install anaconda (follow instructions at [Anaconda Installation](https://docs.anaconda.com/anaconda/install/)).
2. Clone the repo, run `git clone https://github.com/Technion-Kishony-lab/data-to-paper`.
3. Create a conda environment, run `conda create -n data-to-paper python=3.9`.
4. Activate the newly created environment, run `conda activate data-to-paper`.
5. Enter the repo root folder, run `cd data-to-paper`.
6. Install the required packages, run `pip install -r requirements.txt`.
7. Install the app and further required packages, run `pip install -e data_to_paper`.
8. Install pandoc (follow instructions at [Pandoc Installation](https://pandoc.org/installing.html)).
9. Install all the required packages for compiling LaTeX:

   - **On Ubuntu**:
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

### Install using Docker
The Docker container is a self-contained environment that includes all the required dependencies to run the app.
It is simple to install and run, but we do not recommend using it as it currently does not support the GUI app.

1. Install Docker (follow instructions at https://docs.docker.com/engine/install/) and make sure docker server runs on your computer
2. Clone the repo, run `git clone https://github.com/Technion-Kishony-lab/data-to-paper`
3. Enter the repo root folder `cd data-to-paper`
4. Make sure the docker service is running on the machine by running `sudo service docker start`
5. Build the docker container by running `docker build --pull --rm -f "Dockerfile" -t datatopaper "."`

You now have the container with the repo available for run/dev

### Add environment variables for API keys

You need to define the following environment variables in your system:
- OPENAI_API_KEY
- SEMANTIC_SCHOLAR_API_KEY
- DEEPINFRA_API_KEY (optional)

To set up the keys on your system, see 
[openai instructions](https://help.openai.com/en/articles/5112595-best-practices-for-api-key-safety)

To test if the keys are set up correctly, run
`python data_to_paper/data_to_paper/scripts/check_api_keys.py`
