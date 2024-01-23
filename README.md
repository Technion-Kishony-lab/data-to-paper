![data-to-paper-logo](https://github.com/Technion-Kishony-lab/data-to-paper/assets/65530510/4af63803-f0b2-40c2-974d-61bd5dd11c49)

# data-to-paper: a platform for automating scientific research

**data-to-paper** is a framework for systematically navigating the power of AI to perform complete end-to-end 
scientific research, starting from raw data and concluding with comprehensive, transparent, and verifiable 
scientific papers.

Towards this goal, **data-to-paper** systematically channels information and multiple interacting 
LLM and rule-based agents through the conventional scientific path, from annotated data, through creating 
research hypotheses, writing data analysis code, and interpreting the results in light of prior literature,
and ultimately writing to a complete research paper.

This process is aimed at producing transparent and verifiable manuscripts that provide not only an end result, 
but also a detailed account of the research methodologies.

### Examples

We run **data-to-paper** on several datasets:

* "Health Indicators"
branch: `diabetes`

* "Social Network"
branch: `congress_social_network`

* "Treatment Policy"
branch: `nicu`

* "Treatment Optimization"
branch: `tube_levels`


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
3. This can be also done for the other example branches, by changing the branch name and adapting the path to the project folder accordingly.

### Contributing
We invite people to try out **data-to-paper** with their own data and are eager for feedback and suggestions.

We also invite people to help develop the **data-to-paper** framework.


### Important notes

**Disclaimer.** By using this software, you agree to assume all risks associated with its use, including but not limited 
to data loss, system failure, or any other issues that may arise, especially, but not limited to, the
consequences of running of LLM created code on your local machine. The developers of this project 
do not accept any responsibility or liability for any losses, damages, or other consequences that may occur as 
a result of using this software. You are solely responsible for any decisions and actions taken based on the information 
provided by **data-to-paper**.

**Compliance.** As an autonomous experiment, **data-to-paper** may generate content or take actions that are not 
in line with real-world practices, ethical standards, or legal requirements. It is your responsibility 
to ensure that any actions or decisions made based on the output of this software comply with all applicable 
laws, regulations, and ethical standards. The developers and contributors of this project shall not be 
held responsible for any consequences arising from using this software. However, the **data-to-paper** framework 
implements the process in an overseeable manner, allowing to review and if needed abort it at any API call. 
Further, data-to-paper manuscripts are watermarked for transparency as AI-created. Users should not remove this watermark.
For further information, concerning accountability and ethical considerations regarding generative AI
in research, please see [living guidelines](https://www.nature.com/articles/d41586-023-03266-1). 

**Token Usage.** Please note that the use of most language models through external APIs, especially GPT4, 
can be expensive due to its token usage. By utilizing this project, you acknowledge that you are responsible for monitoring 
and managing your own token usage and the associated costs. It is highly recommended to check your API 
usage regularly and set up any necessary limits or alerts to prevent unexpected charges.

