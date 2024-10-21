# remove comment and empty lines in code
from typing import Union


def remove_comment(code):
	code = code.split("\n")
	code = [line for line in code if not line.startswith("#")]
	code = [line for line in code if line.strip() != ""]
	return "\n".join(code)


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
			ans = round(ans * 1e5) / 1e5
		except Exception:
			ans = str(ans)
	return ans


def finqa_equal(prediction: Union[bool, float, str],
                reference: Union[float, str],
                include_percentage: bool = True,
                is_close: float = False) -> bool:
	if prediction is None:
		return False
	elif type(prediction) == bool:
		# bool questions
		if prediction:
			return reference == 'yes'
		else:
			return reference == 'no'
	elif type(reference) == str or type(prediction) == str:
		# string questions
		return prediction == reference
	else:
		# number questions
		if include_percentage:
			gt_result = [reference / 100, reference, reference * 100]
		else:
			gt_result = [reference]
		for item in gt_result:
			try:
				if is_close:
					if isclose(item, prediction, rel_tol=0.001):
						return True
				precision = min(get_precision(prediction), get_precision(item))
				if round(prediction, precision) == round(item, precision):
					return True
			except Exception:
				continue
		return False
