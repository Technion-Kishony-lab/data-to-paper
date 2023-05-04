from g3pt.utils.revise_text import translate_second_person_to_first_person


def test_translate_second_person_to_first_person():
    text = \
        "You are a helpful scientist. Your job is to write a paper. You will only write the paper if " \
        " follow the directions given to you."
    assert translate_second_person_to_first_person(text) == \
           "I am a helpful scientist. My job is to write a paper. I will only write the paper if " \
           " follow the directions given to me."
