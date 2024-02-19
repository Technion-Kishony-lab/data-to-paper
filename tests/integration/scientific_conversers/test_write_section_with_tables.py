from _pytest.fixtures import fixture

from data_to_paper.research_types.scientific_research.scientific_products import ScientificProducts

from data_to_paper.code_and_output_files.code_and_output import CodeAndOutput

SECTIONS_TO_ADD_TABLES_TO = ['results']
CODE = """
def fast_recursive_fibonacci(n):
    if n <= 1:
        return n
    else:
        return fast_recursive_fibonacci(n - 1) + fast_recursive_fibonacci(n - 2)

results = []
for i in range(20):
    results.append(fast_recursive_fibonacci(i))
with open('output.txt', 'w') as f:
    f.write(', '.join([str(x) for x in results]))
"""
OUTPUT = "0, 1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181."


@fixture
def products():
    return ScientificProducts(
        research_goal="Find fastest recursive algorithm for calculating Fibonacci sequence, calculate the 20 first "
                      "terms.",
        cited_paper_sections_and_citations={
            'title': (r"\\title{Fast recursive Fibonacci sequence algorithm} ", set()),
            'abstract': (r"\\begin{abstract} The algorithm uses recursion to calculate the "
                         r"fibonacci sequence. It is the fastest known.\\end{abstract}", set()),
            'results': (r"\\section{Results}\nThe fastest algorithm known uses recursion in python. "
                        r"The 20 first term was first calculated in the paper by \\cite{Fibonacci}.", set())},
        codes_and_outputs={'data_analysis': CodeAndOutput(code=CODE, output=OUTPUT, output_file='output.txt')},
    )
