from scientistgpt.conversation.conversation import OPENAI_SERVER_CALLER
from scientistgpt.gpt_interactors.text_extractors import TextExtractorGPT, extract_analysis_plan_from_response


@OPENAI_SERVER_CALLER.record_or_replay()
def test_text_extractor():
    extracted_text = TextExtractorGPT(
        text='I love data science.\nI love machine learning.\nI start enjoying chatgpt.',
        description_of_text_to_extract='the second sentence',
    ).extract_text()
    assert 'I love machine learning' in extracted_text
    assert 'data science' not in extracted_text
    assert 'enjoying' not in extracted_text


@OPENAI_SERVER_CALLER.record_or_replay()
def test_extract_analysis_plan_from_response():
    response = """
    Here is the analysis plan:

    1. Load the files
    2. Clean the data
    3. Analyze the data
    """
    extracted_text = extract_analysis_plan_from_response(response)
    assert '1. Load the files' in extracted_text
    assert '3. Analyze the data' in extracted_text
    assert 'Here is' not in extracted_text
