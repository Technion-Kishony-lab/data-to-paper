import os

from scientistgpt.gpt_interactors.paper_writing.base_paper_writing import PaperWritingGPT


class TestPaperWritingGPT(PaperWritingGPT):
    def _pre_populate_conversation(self):
        pass

    def _get_paper_sections(self):
        for section_name in self.paper_section_names:
            self.paper_sections[section_name] = f'content of {section_name}'


def test_paper_writing_gpt(tmpdir):
    paper_writing_gpt = TestPaperWritingGPT()
    os.chdir(tmpdir)
    paper_writing_gpt.write_paper()
    assert 'content of title' in paper_writing_gpt.latex_paper
    assert os.path.exists(paper_writing_gpt.latex_filename)
    assert os.path.exists(paper_writing_gpt.pdf_filename)
