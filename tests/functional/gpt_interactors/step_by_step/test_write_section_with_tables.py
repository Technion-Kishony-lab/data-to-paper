from _pytest.fixtures import fixture

from scientistgpt.conversation.conversation import OPENAI_SERVER_CALLER
from scientistgpt.gpt_interactors.citation_adding.call_crossref import CROSSREF_SERVER_CALLER
from scientistgpt.gpt_interactors.step_by_step.reviewers import PaperSectionWithTablesReviewGPT
from scientistgpt.gpt_interactors.types import Products
from scientistgpt.run_gpt_code.code_runner import CodeAndOutput

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
    return Products(
        research_goal="Find fastest recursive algorithm for calculating Fibonacci sequence, calculate the 20 first "
                      "terms.",
        results_summary="The 20 first terms of the Fibonacci sequence are: 0, 1, 1, 2, 3, 5, 8, 13, 21, 34, "
                        "55, 89, 144, 233, 377, 610, 987, 1597, 2584, 4181.",
        paper_sections={'title': r"\\title{Fast recursive Fibonacci sequence algorithm} ",
                        'abstract': r"\\begin{abstract} The algorithm uses recursion to calculate the "
                                    r"fibonacci sequence. It is the fastest known.\\end{abstract}",
                        'results': r"\\section{Results}\nThe fastest algorithm known uses recursion in python. "
                                   r"The 20 first term was first calculated in the paper by \\cite{Fibonacci}."},
        code_and_output=CodeAndOutput(code=CODE, output=OUTPUT, output_file='output.txt'),
    )


@OPENAI_SERVER_CALLER.record_or_replay()
@CROSSREF_SERVER_CALLER.record_or_replay()
def test_table_gpt(products):
    for section_name in SECTIONS_TO_ADD_TABLES_TO:
        products.paper_sections_with_tables[section_name] = \
            PaperSectionWithTablesReviewGPT(products=products, section_name=section_name).get_section()

    # check that we get the output with additional tables
    assert "\\begin{table}" in products.paper_sections_with_tables['results']
