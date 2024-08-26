import re
from typing_extensions import Union

def normalize_answer(answer: Union[str, None]):
    answer = str(answer)
    # number
    answer = answer.replace(",", "")
    digits = re.findall(r"-?\d+\.?\d*", answer)
    answer = digits[-1] if len(digits) > 0 else None
    return floatify_ans(answer)

def floatify_ans(ans):
    """gsm8k"""
    if ans is None:
        return None
    elif type(ans) == dict:
        ans = list(ans.values())[0]
    elif type(ans) == bool:
        ans = ans
    elif type(ans) in [list, tuple]:
        if not ans:
            return None
        else:
            try:
                ans = float(ans[0])
            except Exception:
                ans = str(ans[0])
    else:
        try:
            ans = float(ans)
            ans = round_with_error(ans)
        except Exception:
            ans = str(ans)
    return ans

def round_with_error(x):
    return round(x * 1e5) / 1e5