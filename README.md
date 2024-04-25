# data-to-paper: a platform for automating scientific research

*data-to-paper* is a framework for systematically navigating the power of AI to perform complete end-to-end 
scientific research, starting from raw data and concluding with comprehensive, transparent, and human-verifiable 
scientific papers.

Towards this goal, *data-to-paper* systematically channels information and multiple interacting 
LLM and rule-based agents through the conventional scientific path, from annotated data, through creating 
research hypotheses, writing data analysis code, and interpreting the results in light of prior literature,
and ultimately the step-by-step writing of a complete research paper.

### Key features
* **Open-goal or fixed goal research.** *data-to-paper* can be used to autonomously raise and test 
an hypothesis, or to test a specific pre-defined user-defined hypothesis.
* **Data-chained manuscripts**. The process creates transparent and verifiable manuscripts, where results, 
methodology and data are programmatically linked (all numeric values can be traced back to the data, simply by clicking). 
* **Human-in-the-loop.** A dedicated GUI app allows the user to oversee the process, and to intervene 
at each research step.


### Examples

We ran **data-to-paper** on the following test cases:

* **Health Indicators (open goal).** A clean unweighted subset of CDC’s Behavioral Risk Factor Surveillance System (BRFSS) 2015 annual dataset 
  ([Kaggle](https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset)).
 
  Branch: `examples/diabetes`


* **Social Network (open goal).** A directed graph of Twitter interactions among the 117th Congress members
  ([Fink et al](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10493874/)).

  Branch: `examples/congress_social_network`


* **Treatment Policy (fixed-goal).** A dataset on treatment and outcomes of non-vigorous infants admitted to the Neonatal Intensive Care Unit (NICU), before and after a change to treatment guidelines was implemented
  ([Saint-Fleur et al](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0289945)).

  Branch: `examples/nicu`


* **Treatment Optimization (fixed-goal).** A dataset of pediatric patients, which received mechanical ventilation after undergoing surgery, including an x-ray-based determination of the optimal tracheal tube intubation depth and a set of personalized patient attributes to be used in machine learning and formula-based models to predict this optimal depth
  ([Shim et al](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0257069)).

  Branch: `examples/tube_levels`

### Installation
See [INSTALL.md](INSTALL.md) for installation instructions.

### How to run
1. Follow the installation instructions in [INSTALL.md](INSTALL.md).
2. We suggest starting with running the 5 recorded examples in the example branch `diabetes` (on the docker you have created in stage 1):
   1. ```docker run --rm -it  datatopaper```   # run the docker image
   2. ```git switch -f examples/diabetes```   # checkout the diabetes branch
   3. ```cd data_to_paper/data_to_paper_examples/examples/projects/diabetes/```   # change directory to the diabetes project
   4. ```python diabetes.py```   # run the project
   This will run all the 5 examples in the diabetes project one after the other, presenting the conversations for each example in the terminal, outputting the generated codes, logs, tex file and paper to the `outputs/<example_name>` folder.
3. This can also be done for the other example branches, by changing the branch name and adapting the path to the project folder accordingly.
4. You can similarly introduce and run with other datasets. 
   We advise that the quality of produced papers depend on providing clear, accurate, formal 
   descriptions of the data (see the provided examples for reference). 

### Contributing
We invite people to try out **data-to-paper** with their own data and are eager for feedback and suggestions.

We also invite people to help develop the **data-to-paper** framework.

### Reference
The **data-to-paper** framework is described in the following pre-print:
 - Tal Ifargan, Lukas Hafner, Maor Kern, Ori Alcalay and Roy Kishony, 
"Autonomous LLM-driven research from data to human-verifiable research papers", arXiv:XXX

### Important notes

**Purpose** The **data-to-paper** framework is created as a research project to understand the 
capacities and limitations of LLM-driven scientific research, and to explore ways of creating AI-driven
scientific research that is fully transparent, verifiable and overseable by humans.

**Disclaimer.** By using this software, you agree to assume all risks associated with its use, including but not limited 
to data loss, system failure, or any other issues that may arise, especially, but not limited to, the
consequences of running of LLM created code on your local machine. The developers of this project 
do not accept any responsibility or liability for any losses, damages, or other consequences that may occur as 
a result of using this software. 

**Accountability.** You are solely responsible for the entire content, rigour, quality and ethics of 
created manuscripts. 
The process should be overseen by a human-in-the-loop and created manuscripts should be carefully vetted 
by a domain expert. 
The process is NOT error-proof and human intervention is _necessary_ to ensure the quality of the results. 
For further information, concerning accountability and ethical considerations regarding generative AI
in research, please also consult with [living guidelines](https://www.nature.com/articles/d41586-023-03266-1). 

**Compliance.** It is your responsibility to ensure that any actions or decisions made based on the output of this 
software comply with all applicable laws, regulations, and ethical standards. 
The developers and contributors of this project shall not be held responsible for any consequences arising from 
using this software. Further, data-to-paper manuscripts are watermarked for transparency as AI-created. 
Users should not remove this watermark.

**Token Usage.** Please note that the use of most language models through external APIs, especially GPT4, 
can be expensive due to its token usage. By utilizing this project, you acknowledge that you are 
responsible for monitoring and managing your own token usage and the associated costs. 
It is highly recommended to check your API usage regularly and set up any necessary limits or alerts to 
prevent unexpected charges.

