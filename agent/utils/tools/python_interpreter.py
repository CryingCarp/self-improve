import func_timeout
from langchain_core.tools import tool, ToolException
from typing_extensions import Annotated


@tool()
def python_interpreter(
    code_string: Annotated[str, "The code string you want to execute."],
    variable: Annotated[str, "The value of the variable you want to get after the code execution."]
) -> str:
    """Useful when you need to execute a code and get the value of the variables. Use this tool for code execution.\
This tool will return the code execution result and final value of the variable you want to get."""
    try:
        report, answer = func_timeout.func_timeout(timeout=3, func=execute, args=(code_string, variable))
        return f"{report}\nThe final value of the variable <{variable}> is: {answer}."
    except Exception as e:
        raise ToolException(f"Error in code execution: {str(e)}.\nPlease check the code.")


def execute(code_string: str, variable: str = "answer") -> tuple:
    try:
        exec(code_string)
        locals_ = locals()
        if variable is None:  # default to get the value of the variable 'answer'
            return "Code executed successfully.", locals_.get("answer", None)
        else:
            return "Code executed successfully.", locals_.get(variable, None)
    except Exception as e:  # jump wrong case
        raise e


def _test_safe_execute():
    code_string_2 = """budget = 1000
food = 0.3
accommodation = 0.15
entertainment = 0.25
coursework_materials = 1 - food - accommodation - entertainment
answer = budget * coursework_materials
"""

    result = python_interpreter.invoke({"code_string": code_string_2, "variable": "answer"})
    print(result)


def main():
    _test_safe_execute()
    print(python_interpreter.name)
    print(python_interpreter.description)
    print(python_interpreter.args)
    print(python_interpreter.return_direct)


if __name__ == "__main__":
    main()
