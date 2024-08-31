You need to first decompose the problem into multiple steps. Then for each step, you need to inspect each tool's description and the input requirements to judge whether you need to call a tool to complete current step. Identify all the candidate tools you may need to use and the corresponding tool input text based on the user's current step. Always remmeber that there may be multiple tools that can be used to complete a step! So if there are more than one tool that can be used, your response should contain multiple tools and their inputs. Make sure that the current step is completed before moving to the next step. You have access to the following tools:

{tools_description}

--------------------------------

Use the following format:

Question: 
the input question you must answer

To answer the question, I need to complete the tasks step by step.

Step 1: 
the first step I need to consider

Thought: 
Based on the provided tools and the input question, I should use the following tools to complete current step.

ToolList: 
[tool1, tool2, ...] (the tools in the list should be the ones provided earlier)

InputList:

tool1: 
input text

tool2: 
input text

ResultList: 

tool1: 
result

tool2:
result

Conclusion:
the conclusion of previous information

...(this Thought/Step/ToolList/InputList/ResultList could repeat N times until get the final answer)

Thought: 
Based on previous information, I now complete current step. Let's move to the next step.

Step 2: 
the second step I need to consider

Thought: 
Based on the provided tools and the input question, I don't need any tools to complete the current step.

ToolList: []

InputList:
None

ResultList: 
None

Conclusion: 
the conclusion of previous information

...(same as the previous process)

Thought: 
Now I know the final answer of the original question.

Final answer: 
the final answer