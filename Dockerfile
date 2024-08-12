FROM python:3.9

# Set the working directory in the container
WORKDIR /usr/src/app/data-to-paper

# Copy the current directory contents into the container at /usr/src/app
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN cd ./data_to_paper && pip install -e .

# Install LaTeX and necessary packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    texlive-latex-base \
    texlive-latex-extra \
    texlive-fonts-recommended \
    vim \
    nano \
    pandoc \
&& rm -rf /var/lib/apt/lists/*

# Set the default command to open a bash shell
CMD ["bash"]