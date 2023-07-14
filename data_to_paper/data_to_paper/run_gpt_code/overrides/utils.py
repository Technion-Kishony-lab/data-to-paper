import re


def round_floats(text, target_precision=4, source_precision=10):
    def replacer(match):
        num_str = match.group(0)
        if 'e' in num_str:
            before_exp, _ = num_str.split('e')
        else:
            before_exp = num_str

        num_digits = len(before_exp) - 1 - before_exp.startswith('-') - before_exp.startswith('+')
        if num_digits < source_precision:
            return num_str

        value = float(num_str)
        return f'{value:.{target_precision}g}'

    # This regex matches any floating point number or number in scientific notation
    pattern = r'[-+]?[0-9]*\.[0-9]+([eE][-+]?[0-9]+)?'
    return re.sub(pattern, replacer, text)
