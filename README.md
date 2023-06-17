
# data-to-paper: a platform for automating data-science research

**data-to-paper** is a framework for systematically navigating the power of AI to perform complete end-to-end 
data-science research, starting from raw data and concluding with comprehensive, reproducible, and correct 
scientific papers.

Towards this goal, **data-to-paper** creates interactions among a set of ChatGPT and algorithmic agents that take on 
different roles, such as "scientist", "reviewer", "coder", "debugger", and "literature searcher". 
These agents are algorithmically guided through the canonical sequence of research stages, including question choice, 
data exploration, iterative generations of data analysis code, drawing conclusions, and writing a scientific paper.

This process is aimed at producing transparent and reproducible manuscripts that provide not only an end result, 
but also a detailed account of the research methodologies.

### Example
We have let **data-to-paper** analyze the large CDC Diabetes Health Indicators Dataset. 
Check out one of the papers it produced (example paper). 


### Installation
See [INSTALL.md](INSTALL.md) for installation instructions.

### How to run
We suggest starting with running the recorded example `diabetes.py`

### Contributing
We invite people to try out **data-to-paper** with their own data and are eager for feedback and suggestions.

We also invite people to help develop the **data-to-paper** framework.


### Disclaimers

**Disclaimer.** data-to-paper is an experimental application and is provided "as-is" without any warranty, express or implied. 
By using this software, you agree to assume all risks associated with its use, including but not limited 
to data loss, system failure, or any other issues that may arise, especially, but not limited to, the
consequences of running of ChatGPT created code on your local machine. The developers of this project 
do not accept any responsibility or liability for any losses, damages, or other consequences that may occur as 
a result of using this software. You are solely responsible for any decisions and actions taken based on the information 
provided by data_to_paper.

**Compliance.** As an autonomous experiment, data-to-paper may generate content or take actions that are not 
in line with real-world practices, ethical standards, or legal requirements. It is your responsibility 
to ensure that any actions or decisions made based on the output of this software comply with all applicable 
laws, regulations, and ethical standards. The developers and contributors of this project shall not be 
held responsible for any consequences arising from using this software.

**Token Usage.** Please note that the use of OpenAI language models, especially GPT4, can be expensive 
due to its token usage. By utilizing this project, you acknowledge that you are responsible for monitoring 
and managing your own token usage and the associated costs. It is highly recommended to check your OpenAI API 
usage regularly and set up any necessary limits or alerts to prevent unexpected charges.

