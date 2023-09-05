import re


def round_floats(text, target_precision=4, source_precision=10, pad_with_spaces=True):
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
        formatted_str = f'{value:.{target_precision}g}'

        # pad with spaces to match the length of the original string
        if pad_with_spaces and len(formatted_str) < len(num_str):
            formatted_str = formatted_str.ljust(len(num_str))
        return formatted_str

    # This regex matches any floating point number or number in scientific notation
    pattern = r'[-+]?[0-9]*\.[0-9]+([eE][-+]?[0-9]+)?'
    return re.sub(pattern, replacer, text)
