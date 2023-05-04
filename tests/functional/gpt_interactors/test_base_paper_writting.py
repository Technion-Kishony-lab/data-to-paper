import os

import pytest

from g3pt.conversation.conversation import OPENAI_SERVER_CALLER
from g3pt.gpt_interactors.paper_writing.base_paper_writing import PaperWritingGPT


class TestPaperWritingGPT(PaperWritingGPT):
    def _pre_populate_conversation(self):
        pass

    def _get_paper_sections(self):
        self.paper_sections = {
            'title': r'\title{content of title}',
            'abstract': r'\begin{abstract}content of abstract\end{abstract}',
            'introduction': r'\section{Introduction}{content of introduction}',
            'methods': r'\section{Methods}{content of method}',
            'results': r'\section{Results}{content of results}',
            'discussion': r'\section{Discussion}{content of discussion}',
            'conclusion': r'\section{Conclusion}{content of conclusion}',
        }

    def _add_citations_to_paper(self):
        pass


@pytest.mark.skip
@OPENAI_SERVER_CALLER.record_or_replay()
def test_paper_writing_gpt(tmpdir):
    output_directory = os.path.join(tmpdir.strpath, 'output')
    # create the output directory if it does not exist
    if not os.path.exists(output_directory):
        os.mkdir(output_directory)
    paper_writing_gpt = TestPaperWritingGPT(output_directory=output_directory)

    os.chdir(tmpdir)
    paper_writing_gpt.write_paper(should_compile_with_bib=False)
    assert 'content of title' in paper_writing_gpt.latex_paper
    assert os.path.exists(os.path.join(output_directory, paper_writing_gpt.latex_filename))
    assert os.path.exists(os.path.join(output_directory, paper_writing_gpt.pdf_filename))
