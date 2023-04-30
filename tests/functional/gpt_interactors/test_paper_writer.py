import os

import pytest

from scientistgpt.conversation.conversation import OPENAI_SERVER_CALLER
from scientistgpt.gpt_interactors.citation_adding.call_crossref import CROSSREF_SERVER_CALLER
from scientistgpt.gpt_interactors.types import Products
from scientistgpt.run_gpt_code.code_runner import CodeAndOutput

# TODO:  adapt this test to the new step-by-step code
@pytest.mark.skip
@CROSSREF_SERVER_CALLER.record_or_replay()
@OPENAI_SERVER_CALLER.record_or_replay()
def test_paper_author_gpt(tmpdir):
    # create a scientific mentor with some random scientific products to test the paper author
    # pre_paper_conversation population
    products = Products(
        data_description='The data is ...',
        research_goal='The goal is ...',
        analysis_plan='1. Load the files\n2. Clean the data\n3. Analyze the data',
        code_and_output=[CodeAndOutput(
            """python
            import pandas as pd
            import numpy as np

            df = pd.read_csv('data.csv')
        """,
            """The results are:
            A: 1
            B: 2
            C: 3
            """)],
        results_summary="The results are:\nA: 1\nB: 2\nC: 3",
        implications="We can conclude that the results are:\nA: 1\nB: 2\nC: 3",
        limitations="We did not consider the following:\nA: 2\nB: 3\nC: 1",
    )
    output_directory = os.path.join(tmpdir.strpath, 'output')
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    author = PaperAuthorGPT(products=products,
                            output_directory=output_directory)
    os.chdir(tmpdir)
    author.write_paper(should_compile_with_bib=False)

    # check the conversation name
    assert author.conversation_manager.conversation_name == 'pre_paper_conversation'

    # check that the paper was created in the output directory
    assert os.path.exists(os.path.join(output_directory, author.latex_filename))
    assert os.path.exists(os.path.join(output_directory, author.pdf_filename))
