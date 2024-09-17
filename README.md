## Backward-traceable AI-driven Research

<picture>
<img src="https://github.com/Technion-Kishony-lab/data-to-paper/blob/main/assets/data_to_paper_icon.gif" width="350" 
align="right">
</picture>

[![License: MIT](https://img.shields.io/badge/License-MIT-brightgreen.svg)](https://opensource.org/licenses/MIT)

**data-to-paper** is an automation framework that systematically navigates interacting AI agents through a **complete end-to-end scientific research**, 
starting from *raw data* alone and concluding with *transparent, backward-traceable, 
human-verifiable scientific papers* 
(<a href="https://github.com/Technion-Kishony-lab/data-to-paper/blob/main/assets/ExampleManuscriptFigures.pdf" target="_blank">Example AI-created paper</a>, 
[Copilot App DEMO](https://youtu.be/vrsxgX67n6I)).

<picture>
<img src="https://github.com/Technion-Kishony-lab/data-to-paper/blob/main/assets/AI-Human-agents.png" width="300" 
align="left">
</picture>

### Try it out

```commandline
pip install data-to-paper
```
then run: `data-to-paper`

See [INSTALL](INSTALL.md) for dependencies.
<br clear="left"/>

<picture>
<img src="https://github.com/Technion-Kishony-lab/data-to-paper/blob/main/assets/page_flipping.gif" width="400" align="right">
</picture>

### Key features

* **End-to-end field-agnostic research.** The process navigates through the entire scientific path, 
from data exploration, literature search and ideation, through data analysis and interpretation, 
to the step-by-step writing of a complete research papers.
* **Traceable "data-chained" manuscripts**. Tracing informtion flow, *data-to-paper* creates backward-traceable and verifiable manuscripts,
where any numeric values can be click-traced all the way up to the specific code lines that created them
([data-chaining DEMO](https://youtu.be/HUkJcMXd9x0)).

* **Autopilot or Copilot.** The platform can run fully autonomously, or can be human-guided through the [Copilot App](https://youtu.be/vrsxgX67n6I), allowing users to:

  - Oversee, Inspect and Guide the research

  - Set research goals, or let the AI autonomously raise and test hypotheses

  - Provide review, or invoke on-demand AI-reviews

  - Rewind the process to prior steps

  - Record and replay runs

  -	Track API costs
* **Coding guardrails.** Standard statistical packages are overridden with multiple guardrails 
to minimize common LLM coding errors.



<picture>
<img src="https://github.com/Technion-Kishony-lab/data-to-paper/blob/main/assets/research-steps-horizontal.png" width=100% 
align="left">
</picture>
<br><br>

https://github.com/Technion-Kishony-lab/data-to-paper/assets/31969897/0f3acf7a-a775-43bd-a79c-6877f780f2d4

  
### Motivation: Building a new standard for Transparent, Traceable, and Verifiable AI-driven Research
The *data-to-paper* framework is created as a research project to understand the 
capacities and limitations of LLM-driven scientific research, and to develop ways of harnessing LLM to accelerate 
research while maintaining, and even enhancing, the key scientific values, such as transparency, traceability and verifiability, 
and while allowing scientist to oversee and direct the process
(see also: [living guidelines](https://www.nature.com/articles/d41586-023-03266-1)).

### Implementation
Towards this goal, *data-to-paper* systematically guides **interacting LLM and rule-based agents** 
through the conventional scientific path, from annotated data, through creating 
research hypotheses, conducting literature search, writing and debugging data analysis code, 
interpreting the results, and ultimately the step-by-step writing of a complete research paper.


### Reference
The **data-to-paper** framework is described in the following pre-print:
 - Tal Ifargan, Lukas Hafner, Maor Kern, Ori Alcalay and Roy Kishony, 
"Autonomous LLM-driven research from data to human-verifiable research papers", 
[arXiv:2404.17605](https://arxiv.org/abs/2404.17605)


### Examples

We ran **data-to-paper** on the following test cases:

* **Health Indicators (open goal).** A clean unweighted subset of 
CDC’s Behavioral Risk Factor Surveillance System (BRFSS) 2015 annual dataset 
  ([Kaggle](https://www.kaggle.com/datasets/alexteboul/diabetes-health-indicators-dataset)). Here is an [example Paper](https://github.com/rkishony/data-to-paper-supplementary/blob/3704b0508192ff1f68b33be2ef282249f10f1254/Supplementary%20Data-chained%20Manuscripts/Supplementary%20Data-chained%20Manuscript%20A.pdf) created by data-to paper.

Try out: 
```shell
data-to-paper diabetes
```


* **Social Network (open goal).** A directed graph of Twitter interactions among the 117th Congress members
  ([Fink et al](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC10493874/)). Here is an [example Paper](https://github.com/rkishony/data-to-paper-supplementary/blob/3704b0508192ff1f68b33be2ef282249f10f1254/Supplementary%20Data-chained%20Manuscripts/Supplementary%20Data-chained%20Manuscript%20B.pdf) created by data-to paper.

Try out:
```shell
data-to-paper social_network
```

* **Treatment Policy (fixed-goal).** A dataset on treatment and outcomes of non-vigorous infants admitted to the Neonatal Intensive Care Unit (NICU), before and after a change to treatment guidelines was implemented
  ([Saint-Fleur et al](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0289945)). Here is an [example Paper](https://github.com/rkishony/data-to-paper-supplementary/blob/3704b0508192ff1f68b33be2ef282249f10f1254/Supplementary%20Data-chained%20Manuscripts/Supplementary%20Data-chained%20Manuscript%20C.pdf) created by data-to paper.

Try out: 
```shell
data-to-paper npr_nicu
```
* **Treatment Optimization (fixed-goal).** A dataset of pediatric patients, which received mechanical ventilation after undergoing surgery, including an x-ray-based determination of the optimal tracheal tube intubation depth and a set of personalized patient attributes to be used in machine learning and formula-based models to predict this optimal depth
  ([Shim et al](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0257069)). Here is an [example Paper](https://github.com/rkishony/data-to-paper-supplementary/blob/3704b0508192ff1f68b33be2ef282249f10f1254/Supplementary%20Data-chained%20Manuscripts/Supplementary%20Data-chained%20Manuscript%20D.pdf) created by data-to paper.

We defined three levels of difficulty for the research question for this paper.  
1. **easy**: Compare two ML methods for predicting optimal intubation depth  
Try out: 
```shell
data-to-paper ML_easy
```  
  
2. **medium**: Compare one ML method and one formula-based method for predicting optimal intubation depth  
Try out: 
```shell
data-to-paper ML_medium
```  
 
3. **hard**: Compare 4 ML methods with 3 formula-based methods for predicting optimal intubation depth  
Try out:
```shell
data-to-paper ML_hard
```

### Contributing
We invite people to try out **data-to-paper** with their own data and are eager **for feedback and suggestions**.
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
- [SakanaAI](https://github.com/SakanaAI/AI-Scientist)
- [PaperQ2A](https://github.com/Future-House/paper-qa)
- [LangChain](https://github.com/langchain-ai/langchain)
- [AutoGen](https://microsoft.github.io/autogen/)
- [AutoGPT](https://github.com/Significant-Gravitas/AutoGPT)
- [MetaGPT](https://github.com/geekan/MetaGPT)

And also this curated list of [awesome-agents](https://github.com/kyrolabs/awesome-agents).
