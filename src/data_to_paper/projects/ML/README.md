# ML Treatment Optimization Example Dataset

A dataset of pediatric patients, which received mechanical ventilation after undergoing surgery, including an x-ray-based determination of the optimal tracheal tube intubation depth and a set of personalized patient attributes to be used in machine learning and formula-based models to predict this optimal depth.

### Source
Dataset and research goal are based on:

**Shim J, Ryu K, Lee SH, Cho E,Lee S, Ahn JH (2021)** <br>
"Machine learning model for predicting the optimal depth of tracheal tube insertion in pediatric patients: A retrospective cohort study",
*PLoS One 2021 * 16(9): [e0257069](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0257069)

### Example data-to-paper manuscript
Here is an [example paper](https://github.com/rkishony/data-to-paper-supplementary/blob/main/Supplementary%20Data-chained%20Manuscripts/Supplementary%20Data-chained%20Manuscript%20D.pdf) created by data-to paper.

### How to run
We defined three levels of difficulty for the research question for this paper.  
1. **easy**: Compare two ML methods for predicting optimal intubation depth  
2. **medium**: Compare one ML method and one formula-based method for predicting optimal intubation depth  
3. **hard**: Compare 4 ML methods with 3 formula-based methods for predicting optimal intubation depth  

They can be run through:  
`python run.py ML_easy`  
`python run.py ML_medium`  
`python run.py ML_hard`
