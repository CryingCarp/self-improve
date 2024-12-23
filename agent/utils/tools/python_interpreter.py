import asyncio
import re

import func_timeout
from langchain_core.tools import tool
from typing_extensions import Annotated


@tool()
async def python_interpreter(
    code_string: Annotated[str, "The code string you want to execute, enclosed with '```python' and '```' to indicate the code block "
                                "and store the final answer in the variable <answer>."],
) -> str:
    """This tool will return the code execution result and final value of the variable <answer>. Input should be pure python code string. \
The input should be enclosed with "```python" and "```" to indicate the code block. For example: \n```python\nanswer = "123"\n```\n \
It should be noting that the execution environment contains "sympy"、"math"、"numexpr" libraries. You could use these libraries to \
complete math problems or numerical operations. Since this tool only execute the code string, and you will never get the result of the \
final answer unless you put the final answer into the variable <answer>. For example, at the last line of the code string, you should \
assign the final answer to the variable <answer> like this: "answer = 123". The final value of the variable <answer> will be returned."""
    
    assert isinstance(code_string, str), "The code_string should be a string."
    matches = re.findall(r"```python(.*?)```", code_string, re.DOTALL)
    if not matches:
        return "The code string should be enclosed with '```python' and '```' to indicate the code block."
    else:
        answer, report = func_timeout.func_timeout(timeout=3, func=execute, args=(matches[0], "answer"))
    if answer is None:
        return f"The final answer should be stored in the variable <answer>."
    return f"{report}\nThe final value of the variable <answer> is: {answer}."


def execute(code_string: str, variable: str = "answer") -> tuple:
    """
    Execute the code string and return the final value of the variable <answer>.
    
    Args:
        code_string: The code string you want to execute.
        variable: The variable name you want to get the value. Default to "answer".
        
    Returns:
        tuple: The final value of the variable <answer> and the execution report.
    """
    try:
        local_vars = {}
        exec(code_string, {}, local_vars)
        if variable is None:  # default to get the value of the variable 'answer'
            answer = local_vars
        else:
            answer = local_vars.get(variable, None)
        return answer, "Done"
    except Exception as e:  # jump wrong case
        return None, repr(e)


async def _async_test_safe_execute():
    code_string_2 = "```python\ntotal_cost_2x4 = 10 * 7066651\nanswer = total_cost_2x4```"
    result = await python_interpreter.ainvoke({"code_string": code_string_2})
    print(result)


async def main():
    await _async_test_safe_execute()
    print(python_interpreter.name)
    print(python_interpreter.description)
    print(python_interpreter.args)
    print(python_interpreter.return_direct)


if __name__ == "__main__":
    asyncio.run(main())
