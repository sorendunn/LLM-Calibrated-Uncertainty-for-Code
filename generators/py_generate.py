from .generator_utils import gpt_chat, gpt_completion

from typing import Optional, List

PY_SIMPLE_COMPLETION_INSTRUCTION = "# Write the body of this function only."
PY_REFLEXION_COMPLETION_INSTRUCTION = "You are PythonGPT. You will be given your past function implementation, a series of unit tests, and a hint to change the implementation appropriately. Apply the changes below by writing the body of this function only.\n\n-----"
PY_SELF_REFLECTION_COMPLETION_INSTRUCTION = "You are PythonGPT. You will be given a function implementation and a series of unit tests. Your goal is to write a few sentences to explain why your implementation is wrong as indicated by the tests. You will need this as a hint when you try again later. Only provide the few sentence description in your answer, not the implementation.\n\n-----"
PY_SIMPLE_CHAT_INSTRUCTION = "You are PythonGPT. You will be given a function signature and docstring. You should fill in the following text of the missing function body. For example, the first line of the completion should have 4 spaces for the indendation so that it fits syntactically with the preceding signature."
PY_REFLEXION_CHAT_INSTRUCTION = "You are PythonGPT. You will be given your past function implementation, a series of unit tests, and a hint to change the implementation appropriately. Apply the changes below by writing the body of this function only. You should fill in the following text of the missing function body. For example, the first line of the completion should have 4 spaces for the indendation so that it fits syntactically with the preceding signature."
PY_SELF_REFLECTION_CHAT_INSTRUCTION = "You are PythonGPT. You will be given a function implementation and a series of unit tests. Your goal is to write a few sentences to explain why your implementation is wrong as indicated by the tests. You will need this as a hint when you try again later. Only provide the few sentence description in your answer, not the implementation."

PY_GET_FUNC_INSTRUCTIONS = "You are PythonGPT. You will be given a mathematics word problem.  Write a general python function named compute_result with a docstring to solve this sort of problem."
PY_GET_SET_PROBLEM_INSTRUCTIONS = "You are PythonGPT. You will be given a mathematics word problem and a python function which can be used to solve that problem. Return a function called 'set_problem_instructions' that takes no parameters and returns the answer to the word problem as a float using the given function"

PY_TEST_GENERATION_FEW_SHOT = """For example:

func signature:
def has_close_elements(numbers: List[float], threshold: float) -> bool:
    \"\"\" Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    \"\"\"

unit tests:
assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3) == True
assert has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05) == False
assert has_close_elements([1.0, 2.0, 5.9, 4.0, 5.0], 0.95) == True
assert has_close_elements([1.0, 2.0, 5.9, 4.0, 5.0], 0.8) == False
assert has_close_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1) == True
assert has_close_elements([1.1, 2.2, 3.1, 4.1, 5.1], 1.0) == True
assert has_close_elements([1.1, 2.2, 3.1, 4.1, 5.1], 0.5) == False"""

PY_TEST_GENERATION_COMPLETION_INSTRUCTION = f"""You are PythonGPT, an AI coding assistant that can write unique, diverse, and intuitive unit tests for functions given the signature and docstring.

{PY_TEST_GENERATION_FEW_SHOT}"""

PY_TEST_GENERATION_CHAT_INSTRUCTION = """You are CodexGPT, an AI coding assistant that can write unique, diverse, and intuitive unit tests for functions given the signature and docstring."""

def py_generate_self_reflection(func: str, feedback: str, model: str) -> str:
    if model == "gpt-4" or model == "gpt-3.5-turbo":
        reflection = gpt_chat(model, PY_SELF_REFLECTION_CHAT_INSTRUCTION, f'{func}\n\n{feedback}\n\nExplanation:')
    else:
        reflection = gpt_completion(model, f'{PY_SELF_REFLECTION_COMPLETION_INSTRUCTION}\n{func}\n\n{feedback}\n\nExplanation:')
    return reflection # type: ignore

def py_generate_func_impl(
        func_sig: str,
        model: str,
        strategy: str,
        prev_func_impl: Optional[str] = None,
        feedback: Optional[str] = None,
        self_reflection: Optional[str] = None
    ) -> str:
    if strategy != "reflexion" and strategy != "simple":
        raise ValueError(f"Invalid strategy: given `{strategy}` but expected one of `reflexion` or `simple`")
    if strategy == "reflexion" and (prev_func_impl is None or feedback is None or self_reflection is None):
        raise ValueError(f"Invalid arguments: given `strategy=reflexion` but `prev_func_impl`, `feedback`, or `self_reflection` is None")

    if model == "gpt-4" or model == "gpt-3.5-turbo":
        if strategy == "reflexion":
            message = f"previous implementation:\n{prev_func_impl}\n\nunit tests:\n{feedback}\n\nhint:\n{self_reflection}\n\n# improved implementation\n{func_sig}"
            func_body = gpt_chat(model, PY_REFLEXION_CHAT_INSTRUCTION, message, temperature = 1.0)
            # print(func_body)
        else:
            func_body = gpt_chat(model, PY_SIMPLE_CHAT_INSTRUCTION if strategy == "simple" else PY_REFLEXION_CHAT_INSTRUCTION, func_sig)
    else:
        if strategy == "reflexion":
            prompt = f"{PY_REFLEXION_COMPLETION_INSTRUCTION}\n{prev_func_impl}\n\nunit tests:\n{feedback}\n\nhint:\n{self_reflection}\n\n# improved implementation\n{func_sig}"
            func_body = gpt_completion(model, prompt)
        else:
            prompt = f"{PY_SIMPLE_COMPLETION_INSTRUCTION}\n{func_sig}"
            func_body = gpt_completion(model, prompt)
    return func_sig + func_body # type: ignore

def py_generate_internal_tests(func_sig: str, model: str, committee_size: int=1) -> List[str]:
    def parse_tests(tests: str) -> List[str]:
        return [test.strip() for test in tests.splitlines() if "assert" in test]
    """
    Generates tests for a function using a refinement technique with the number
    of specified commmittee members.
    """
    if model == "gpt-4" or model == "gpt-3.5-turbo":
        message = f'{PY_TEST_GENERATION_FEW_SHOT}\n\nfunc signature:\n{func_sig}\nunit tests:'
        output = gpt_chat(model, PY_TEST_GENERATION_CHAT_INSTRUCTION, message)
        # print(output)
    else:
        prompt = f'{PY_TEST_GENERATION_COMPLETION_INSTRUCTION}\n\nfunc signature:\n{func_sig}\nunit tests:'
        output = gpt_completion(model, prompt)
    cur_tests: List[str] = parse_tests(output) # type: ignore

    # TODO: NOT SUPPORTED YET
    # someone implement this
    # cur_refinement_num = 0
    # while cur_refinement_num < committee_size:
        # # TODO: implement
        # cur_tests = ... # type: ignore

        # cur_refinement_num += 1

    return cur_tests

# def get_target_function(func_sig: str, model: str,) -> str:
    
#     # First get an implementation of the function
#     function_text = f'{PY_TEST_GENERATION_FEW_SHOT}\n\nfunc signature:\n{func_sig}\nunit tests:'
#     function = gpt_chat(model, PY_GET_FUNC_INSTRUCTIONS, function_text)
    
#     # Next get the internal of set_problem_values
#     set_problem_values = f'{PY_TEST_GENERATION_FEW_SHOT}\n\nfunc signature:\n{func_sig}\nunit tests:'
#     set_problem_values = gpt_chat(model, PY_GET_SET_PROBLEM_INSTRUCTIONS, set_problem_values_text)
    
#     # append the two and return
#     return function + set_problem_values