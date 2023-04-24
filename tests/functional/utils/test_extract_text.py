from scientistgpt.utils import extract_text_between_tags

text_1 = 'hello, here is a list [1, 2, 3, [4], 5] of numbers and lists'
text_2 = '\\title{\\textbf{this is some title in bold}} \n' \
         '\\start{abstract} this is also the abstract \\end{abstract}'
text_3 = '\\section{Introduction} \n' \
            'this is the introduction \n' \


def test_extract_text_between_tags():
    assert extract_text_between_tags(text_1, '[', ']') == '1, 2, 3, [4], 5'
    assert extract_text_between_tags(text_1, '[', ']', leave_tags=True) == '[1, 2, 3, [4], 5]'
    assert extract_text_between_tags(text_2, '\\title{', '}') == '\\textbf{this is some title in bold}'
    assert extract_text_between_tags(text_2, '\\title{', '}', leave_tags=True) == '\\title{\\textbf{this is some title in bold}}'
    assert extract_text_between_tags(text_2, '\\start{abstract}', '\\end{abstract}') == ' this is also the abstract '


def test_extract_text_between_tags_open_ended():
    assert extract_text_between_tags(text_1, '[', None) == '1, 2, 3, [4], 5] of numbers and lists'
    assert extract_text_between_tags(text_1, '[', None, leave_tags=True) == '[1, 2, 3, [4], 5] of numbers and lists'
    assert extract_text_between_tags(text_3, '\\section{Introduction}', None) == ' \nthis is the introduction \n' \
