## data-to-paper: AI-driven research from data to human-verifiable research papers

<picture>
<img src="https://github.com/Technion-Kishony-lab/data-to-paper/blob/main/data_to_paper_icon.gif" width="350" align="right">
</picture>

[*data-to-paper*](https://arxiv.org/abs/2404.17605) is a framework for systematically navigating the power of AI to perform complete end-to-end 
scientific research, starting from raw data and concluding with comprehensive, transparent, and human-verifiable 
scientific papers ([example](https://t.co/iz44TDZZHb)).

Towards this goal, *data-to-paper* systematically guides interacting 
LLM and rule-based agents through the conventional scientific path, from annotated data, through creating 
research hypotheses, conducting literature search, writing and debugging data analysis code, 
interpreting the results, and ultimately the step-by-step writing of a complete research paper.

The *data-to-paper* framework is created as a research project to understand the 
capacities and limitations of LLM-driven scientific research, and to develop ways of harnessing LLM to accelerate 
research while maintaining, and even enhancing, key scientific values, such as transparency, traceability and verifiability, 
and while allowing scientist to oversee and direct the process 
[see also: [living guidelines](https://www.nature.com/articles/d41586-023-03266-1)].

[![License: MIT](https://img.shields.io/badge/License-MIT-brightgreen.svg)](https://opensource.org/licenses/MIT)

https://github.com/Technion-Kishony-lab/data-to-paper/assets/31969897/0f3acf7a-a775-43bd-a79c-6877f780f2d4


### Reference
The **data-to-paper** framework is described in the following pre-print:
 - Tal Ifargan, Lukas Hafner, Maor Kern, Ori Alcalay and Roy Kishony, 
"Autonomous LLM-driven research from data to human-verifiable research papers", 
[arXiv:2404.17605](https://arxiv.org/abs/2404.17605)

### Key features
* **Field agnostic**. We strive to make the framework as general as possible, so that it can be used across different 
fields of research.
* **Open-goal or fixed-goal research.** *data-to-paper* can be used to autonomously raise and test 
a hypothesis, or to test a specific pre-defined user-provided hypothesis.
* **Data-chained manuscripts**. The process creates transparent and verifiable manuscripts, where results, 
methodology and data are programmatically linked 
(all numeric values can be click-traced back to the code lines that created them).
* **Coding guardrails.** Standard statistical packages are overridden with multiple guardrails to minimize
common LLM coding errors.
* **Human-in-the-loop.** A GUI app allows the user to oversee the process, and to intervene 
at each research step.
* **Record & Replay**. The entire process is recorded, including all LLM responses, Human feedback, and 
literature search retrievals, allowing for transparent replay.

### Installation
See [INSTALL.md](INSTALL.md) for installation instructions.

### How to run
1. Install data-to-paper ([INSTALL](INSTALL.md)).
2. Run data-to-paper:
      `python data_to_paper/data_to_paper/run/run.py`
3. This will open a startup dialog that will allow you to specify your own project, 
or to reproduce example projects (`data-to-paper/projects`) 
4. Click "Start" to start the run, with human overseeing and feedback.
5. At the end of the process, a pdf of the manuscript will be created in the project folder.

### GUI app demo

https://github.com/Technion-Kishony-lab/data-to-paper/assets/65530510/878865a7-45b4-496c-a62f-71d0003ce44b

### Examples

We ran **data-to-paper** on the following test cases:

* **Health Indicators (open goal).** A clean unweighted subset of 
CDC’s Behavioral Risk Factor Surveillance System (BRFSS) 2015 annual dataset 
  ([Kaggle](https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset)). Here is an [example Paper](https://github.com/rkishony/data-to-paper-supplementary/blob/main/Supplementary%20Data-chained%20Manuscripts/Supplementary%20Data-chained%20Manuscript%20A.pdf) created by data-to paper.

Try out: `python run.py diabetes`


* **Social Network (open goal).** A directed graph of Twitter interactions among the 117th Congress members
  ([Fink et al](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10493874/)). Here is an [example Paper](https://github.com/rkishony/data-to-paper-supplementary/blob/main/Supplementary%20Data-chained%20Manuscripts/Supplementary%20Data-chained%20Manuscript%20B.pdf) created by data-to paper.

Try out: `python run.py social_network`


* **Treatment Policy (fixed-goal).** A dataset on treatment and outcomes of non-vigorous infants admitted to the Neonatal Intensive Care Unit (NICU), before and after a change to treatment guidelines was implemented
  ([Saint-Fleur et al](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0289945)). Here is an [example Paper](https://github.com/rkishony/data-to-paper-supplementary/blob/main/Supplementary%20Data-chained%20Manuscripts/Supplementary%20Data-chained%20Manuscript%20C.pdf) created by data-to paper.

Try out: `python run.py npr_nicu`

* **Treatment Optimization (fixed-goal).** A dataset of pediatric patients, which received mechanical ventilation after undergoing surgery, including an x-ray-based determination of the optimal tracheal tube intubation depth and a set of personalized patient attributes to be used in machine learning and formula-based models to predict this optimal depth
  ([Shim et al](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0257069)). Here is an [example Paper](https://github.com/rkishony/data-to-paper-supplementary/blob/main/Supplementary%20Data-chained%20Manuscripts/Supplementary%20Data-chained%20Manuscript%20D.pdf) created by data-to paper.

We defined three levels of difficulty for the research question for this paper.  
1. **easy**: Compare two ML methods for predicting optimal intubation depth  
Try out: `python run.py ML_easy`  
  
2. **medium**: Compare one ML method and one formula-based method for predicting optimal intubation depth  
Try out: `python run.py ML_medium`  
 
3. **hard**: Compare 4 ML methods with 3 formula-based methods for predicting optimal intubation depth  
Try out: `python run.py ML_hard`

### Contributing
We invite people to try out **data-to-paper** with their own data and are eager for feedback and suggestions.
It is currently designed for relatively simple research goals and simple datasets, where 
we want to raise and test a statistical hypothesis.

We also invite people to help develop and extend the **data-to-paper** framework in science or other fields.


### Important notes

**Disclaimer.** By using this software, you agree to assume all risks associated with its use, including but not limited 
to data loss, system failure, or any other issues that may arise, especially, but not limited to, the
consequences of running of LLM created code on your local machine. The developers of this project 
do not accept any responsibility or liability for any losses, damages, or other consequences that may occur as 
a result of using this software. 

**Accountability.** You are solely responsible for the entire content of 
created manuscripts including their rigour, quality, ethics and any other aspect. 
The process should be overseen and directed by a human-in-the-loop and created manuscripts should be carefully vetted 
by a domain expert. 
The process is NOT error-proof and human intervention is _necessary_ to ensure accuracy and the quality of the results. 

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

### Related projects

Here are some other cool multi-agent related projects:
- [LangChain](https://github.com/langchain-ai/langchain)
- [AutoGen](https://microsoft.github.io/autogen/)
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)
- [MetaGPT](https://github.com/geekan/MetaGPT)

And also this curated list of [awesome-agents](https://github.com/kyrolabs/awesome-agents).

