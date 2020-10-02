"""
module to run measurement check
split out because its called by multiple tests
"""

def result_check(compare_type, min_allow, max_allow, value):

    # check pass / fail result
    if compare_type == 'range':

        result = 'pass' if min_allow <= value <= max_allow else 'fail'

    elif compare_type == 'max':

        result = 'pass' if value <= max_allow else 'fail'

    elif compare_type == 'min':

        result = 'pass' if value >= min_allow else 'fail'

    return result