### Install data_to_paper

1. Install Docker (follow instructions at https://docs.docker.com/engine/install/) and make sure docker server runs on your computer

2. Clone the repo, run `git clone https://github.com/Technion-Kishony-lab/data-to-paper`

3. Enter the repo root folder `cd data-to-paper`

4. Make sure the docker service is running on the machine by running `sudo service docker start`

5. Build the docker container by running `docker build --pull --rm -f "Dockerfile" -t datatopaper "."`

You now have the container with the repo available for run/dev
