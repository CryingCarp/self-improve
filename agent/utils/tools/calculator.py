import numexpr as ne
from langchain_core.tools import tool, ToolException
from typing_extensions import Annotated


@tool
async def calculator(expression: Annotated[str, "The the mathematical expression you want to evaluate."]) -> str:
    """Useful when you need to calculate the value of a mathematical expression, including basic arithmetic \
operations. Use this tool for math operations. Input should strictly follow the numuxpr syntax."""

    try:
        result = ne.evaluate(expression).item()
        return f"The result of the expression <{expression}> is: {result}."
    except Exception as e:
        raise ToolException(f"Error in calculation: {str(e)}. Please check the expression.")


def main():
    print(calculator.invoke("2 / 0"))
    print(calculator.name)
    print(calculator.description)
    print(calculator.args)
    print(calculator.return_direct)


if __name__ == '__main__':
    main()