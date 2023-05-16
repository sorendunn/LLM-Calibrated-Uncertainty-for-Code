import ast
import signal
import astunparse
from multiprocessing import Process, Manager
from .executor_utils import timeout_handler
from typing import List
from .executor_types import ExecuteResult

import multiprocessing

def get_output(func: str, test: str, timeout: int = 5) -> str:
    # assuming this function exists
    pass

def test_func(func: str, test: str, result_dict: dict) -> None:
    try:
        exec(f'{func}\n{test}', globals())
        result_dict['passed'] = True
    except AssertionError:
        output = get_output(func, test)
        result_dict['output'] = output
        result_dict['passed'] = False
    except Exception:
        result_dict['passed'] = False

def py_execute(func: str, tests: List[str], timeout: int = 5) -> ExecuteResult:
    # Combine function code and assert statement
    func_test_list = [f'{func}\n{test}' for test in tests]

    # Run the tests and collect the results
    success_tests = []
    failed_tests = []
    passing_num = 0
    num_tests = len(func_test_list)
    for i in range(num_tests):
        with Manager() as manager:
            result_dict = manager.dict()
            p = multiprocessing.Process(target=test_func, args=(func, tests[i], result_dict))
            p.start()

            p.join(timeout)

            if p.is_alive():
                p.terminate()
                p.join()
                output = get_output(func, tests[i], timeout=timeout)
                failed_tests += [f"{tests[i]} # output: {output}"]
            elif not result_dict.get('passed', False):
                output = result_dict.get('output', 'Unknown')
                failed_tests += [f"{tests[i]} # failed without exception, output: {output}"]
            else:
                success_tests += [tests[i]]
                passing_num += 1

    feedback = "Tested passed:"
    for test in success_tests:
        feedback += f"\n{test}"
    feedback += "\n\nTests failed:"
    for test in failed_tests:
        feedback += f"\n{test}"
        
    return ExecuteResult(passing_num, feedback)


# def py_execute(func: str, tests: List[str], timeout: int = 5) -> ExecuteResult:
#     # Combine function code and assert statement
#     func_test_list = [f'{func}\n{test}' for test in tests]

#     # Run the tests and collect the results
#     success_tests = []
#     failed_tests = []
#     passing_num = 0
#     num_tests = len(func_test_list)
#     for i in range(num_tests):
#         try:
#             # Set the alarm
#             signal.signal(signal.SIGALRM, timeout_handler)
#             signal.alarm(timeout)

#             # Run the test and disable the alarm
#             exec(func_test_list[i], globals())
#             signal.alarm(0)

#             success_tests += [tests[i]]
#             passing_num += 1
#         except Exception:
#             output = get_output(func, tests[i], timeout=timeout)
#             failed_tests += [f"{tests[i]} # output: {output}"]
#             is_passing = False

#     feedback = "Tested passed:"
#     for test in success_tests:
#         feedback += f"\n{test}"
#     feedback += "\n\nTests failed:"
#     for test in failed_tests:
#         feedback += f"\n{test}"
        
#     return ExecuteResult(passing_num, feedback)

# def num_execute(func: str, tests: List[str], timeout: int = 5) -> ExecuteResult:
#     # Combine function code and assert statement
#     func_test_list = [f'{func}\n{test}' for test in tests]

#     # Run the tests and collect the results
#     success_tests = []
#     failed_tests = []
#     passing_num = 0
#     num_tests = len(func_test_list)
#     for i in range(num_tests):
#         try:
#             # Set the alarm
#             signal.signal(signal.SIGALRM, timeout_handler)
#             signal.alarm(timeout)

#             # Run the test and disable the alarm
#             exec(func_test_list[i], globals())
#             signal.alarm(0)

#             success_tests += [tests[i]]
#             passing_num += 1
#         except Exception:
#             output = get_output(func, tests[i], timeout=timeout)
#             failed_tests += [f"{tests[i]} # output: {output}"]

#     feedback = "Tested passed:"
#     for test in success_tests:
#         feedback += f"\n{test}"
#     feedback += "\n\nTests failed:"
#     for test in failed_tests:
#         feedback += f"\n{test}"
        
#     return ExecuteResult(passing_num, feedback)

# def py_evaluate(name: str, func: str, test: str, timeout: int = 5) -> bool:
#     """
#     Evaluates the implementation on Human-Eval Python.

#     probably should be written in a dataset-agnostic way but not now
#     """
#     code = f"""{func}

# {test}

# check({name})
# """
#     try:
#         # Set the alarm
#         signal.signal(signal.SIGALRM, timeout_handler)
#         signal.alarm(timeout)

#         # Run the test and disable the alarm
#         exec(code, globals())
#         signal.alarm(0)

#         return True
#     except Exception:
#         return False

# def get_call_str(assert_statement: str) -> str:
#     call_str = ast.parse(assert_statement).body[0].test.left # type: ignore
#     return astunparse.unparse(call_str).strip()

# def get_output(func: str, assert_statement: str, timeout: int = 5) -> str:
#     try:
#         func_call = get_call_str(assert_statement)
#         exec(func, globals())

#         # set the alarm
#         signal.signal(signal.SIGALRM, timeout_handler)
#         signal.alarm(timeout)
#         # Run the test and disable the alarm
#         output = eval(func_call)
#         signal.alarm(0)
#         return output
#     except TimeoutError:
#         return "TIMEOUT"
#     except Exception as e:
#         return str(type(e).__name__)

import multiprocessing
import ast
import astunparse

def run_code(code: str, result_dict: dict) -> bool:
    try:
        exec(code, globals())
        result_dict['passed'] = True
    except Exception:
        result_dict['passed'] = False

def py_evaluate(name: str, func: str, test: str, timeout: int = 5) -> bool:
    code = f"""{func}

{test}

check({name})
"""
    with Manager() as manager:
        result_dict = manager.dict()
        p = multiprocessing.Process(target=run_code, args=(code, result_dict))
        p.start()

        p.join(timeout)

        if p.is_alive():
            p.terminate()
            p.join()
            return False

        return result_dict.get('passed', False)

def get_call_str(assert_statement: str) -> str:
    call_str = ast.parse(assert_statement).body[0].test.left # type: ignore
    return astunparse.unparse(call_str).strip()

def eval_func(func: str, func_call: str, result_dict: dict):
    try:
        exec(func, globals())
        result_dict['output'] = str(eval(func_call))
    except AssertionError:
        result_dict['output'] = "AssertionError"
    except Exception as e:
        result_dict['output'] = str(type(e).__name__)


def get_output(func: str, assert_statement: str, timeout: int = 5) -> str:
    try:
        func_call = get_call_str(assert_statement)
        with Manager() as manager:
            result_dict = manager.dict()
            p = Process(target=eval_func, args=(func, func_call, result_dict))
            p.start()
            p.join(timeout)

            if p.is_alive():
                p.terminate()
                p.join()
                if result_dict.get('output') == "AssertionError":
                    return "AssertionError"
                else:
                    return "TIMEOUT"
            
            return result_dict.get('output', '')
    except Exception as e:
        return str(type(e).__name__)


if __name__ == "__main__":
    pass
    # Test the function
    # func = "def add(a, b):\n    while True:\n        x = 1\n    return a + b"
    # tests = ["assert add(1, 2) == 3", "assert add(1, 2) == 4"]
    # print(execute_with_feedback(func, tests, timeout=1))
