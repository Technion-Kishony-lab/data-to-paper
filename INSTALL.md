## Install data_to_paper

### Install on your local machine

1. Install anaconda (follow instructions at [Anaconda Installation](https://docs.anaconda.com/anaconda/install/)).
2. Clone the repo, run `git clone https://github.com/Technion-Kishony-lab/data-to-paper`.
3. Create a conda environment, run `conda create -n data-to-paper python=3.11`.
4. Activate the newly created environment, run `conda activate data-to-paper`.
5. Enter the repo root folder, run `cd data-to-paper`.
6. Install the required packages, run `pip install -r requirements.txt`.
7. Install the app and further required packages, run `cd ./data_to_paper && pip install -e .`.
8. Install all the required packages for compiling LaTeX:

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

Remember to check that all paths are set correctly in your system to access the LaTeX tools from the command line.

### Install using Docker

Note, GUI app is not currently supported in the docker container. If you need to run the GUI app, please install the app on your local machine.

1. Install Docker (follow instructions at https://docs.docker.com/engine/install/) and make sure docker server runs on your computer
2. Clone the repo, run `git clone https://github.com/Technion-Kishony-lab/data-to-paper`
3. Enter the repo root folder `cd data-to-paper`
4. Make sure the docker service is running on the machine by running `sudo service docker start`
5. Build the docker container by running `docker build --pull --rm -f "Dockerfile" -t datatopaper "."`

You now have the container with the repo available for run/dev
