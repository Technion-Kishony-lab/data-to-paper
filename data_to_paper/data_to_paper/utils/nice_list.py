from typing import Union, Tuple, Optional

StrOrTupleStr = Union[str, Tuple[str, str]]


def nicely_join(words: list, wrap_with: StrOrTupleStr = '',
                prefix: StrOrTupleStr = '', suffix: StrOrTupleStr = '',
                separator: str = ', ', last_separator: Optional[str] = None, empty_str: str = ''):
    """
    Concatenate a list of words with commas and an 'and' at the end.

    wrap_with: if str: wrap each word with the provided string. if tuple: wrap each word with the first string
    on the left and the second string on the right.

    prefix: if str: add the provided string before the concatenated words. if tuple the first string is for singular
    and the second string is for plural.

    suffix: if str: add the provided string after the concatenated words. if tuple the first string is for singular
    and the second string is for plural.
    """

    def format_noun(noun: StrOrTupleStr, num: int):
        if isinstance(noun, str):
            pass
        elif isinstance(noun, tuple):
            if num_words == 1:
                noun = noun[0]
            else:
                noun = noun[1]
        else:
            raise ValueError(f'prefix must be either str or tuple, not {type(prefix)}')
        if '{}' in noun:
            noun = noun.format(num)
        if '[s]' in noun:
            noun = noun.replace('[s]', 's' if num_words > 1 else '')
        return noun

    # wrap each word with the provided string:
    if isinstance(wrap_with, str):
        words = [wrap_with + str(word) + wrap_with for word in words]
    elif isinstance(wrap_with, tuple):
        words = [wrap_with[0] + str(word) + wrap_with[1] for word in words]
    elif wrap_with is not None:
        raise ValueError(f'wrap_with must be either str or tuple, not {type(wrap_with)}')

    num_words = len(words)

    # concatenate the words:
    last_separator = last_separator or separator
    if num_words == 0:
        return empty_str
    elif num_words == 1:
        s = words[0]
    elif num_words == 2:
        s = words[0] + last_separator + words[1]
    else:
        s = separator.join(words[:-1]) + last_separator + words[-1]

    return format_noun(prefix, num_words) + s + format_noun(suffix, num_words)


class NiceList(list):
    """
    A list that can be printed nicely.
    """
    def __init__(self, *args, wrap_with: StrOrTupleStr = '', prefix: StrOrTupleStr = '',
                 suffix: StrOrTupleStr = '', separator: str = ', ', last_separator: Optional[str] = None,
                 empty_str: str = ''):
        super().__init__(*args)
        self.wrap_with = wrap_with
        self.prefix = prefix
        self.suffix = suffix
        self.separator = separator
        self.last_separator = last_separator
        self.empty_str = empty_str

    def __str__(self):
        return nicely_join(self, self.wrap_with, self.prefix, self.suffix, self.separator, self.last_separator,
                           )

    def __repr__(self):
        return str(self)


class NiceDict(dict):
    """
    A dict that is printed with a new line for each key.
    For example:
    {'key1': value1, 'key2': value2}
    is printed as:
    {
    'key1': value1,
    'key2': value2,
    }
    """
    def __init__(self, *args, format_numerics_and_iterables: Optional[callable] = None):
        super().__init__(*args)
        self.format_numerics_and_iterables = format_numerics_and_iterables or repr

    def __str__(self):
        if len(self) == 0:
            return '{}'
        return '{\n' + '\n'.join([f'    {repr(key)}: {self.format_numerics_and_iterables(value)},'
                                  for key, value in self.items()]) + '\n}'

    def __repr__(self):
        return str(self)
