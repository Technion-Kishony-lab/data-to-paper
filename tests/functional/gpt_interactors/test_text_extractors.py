from scientistgpt.conversation.conversation import OPENAI_SERVER_CALLER
from scientistgpt.gpt_interactors.text_extractors import TextExtractorGPT


@OPENAI_SERVER_CALLER.record_or_replay()
def test_text_extractor():
    extracted_text = TextExtractorGPT(
        text='I love data science.\nI love machine learning.\nI start enjoying chatgpt.',
        description_of_text_to_extract='the second sentence',
    ).extract_text()
    assert 'I love machine learning' in extracted_text
    assert 'data science' not in extracted_text
    assert 'enjoying' not in extracted_text
