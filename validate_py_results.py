import sys
import time
import json
import multiprocessing
from utils import read_jsonl
from utils import write_jsonl

assert len(sys.argv) == 2, "Please provide a log file"
LOG_PATH = sys.argv[1]

def red_text(text: str) -> str:
    return f"\033[91m{text}\033[0m"

def green_text(text: str) -> str:
    return f"\033[92m{text}\033[0m"

def count_test_cases(test_str: str) -> int:
    # dumb way to do this but works
    return test_str.count("assert")


# Original Validation
# def validate_py_results(log_path: str):
#     if not log_path.endswith(".jsonl"):
#         raise ValueError("Please provide a valid log file")
#     data = read_jsonl(log_path)
#     num_success = 0
#     for i, item in enumerate(data):
#         # if item["is_solved"][-1]:
#         func_impl = item["prompt"] + item["solution"][-1]
#         code = f'{func_impl}\n\n{item["test"]}\n\ncheck({item["entry_point"]})'
#         num_tests = count_test_cases(item["test"])
#         start_time = time.time()
#         try:
#             exec(code, globals())
#             elapsed_time = time.time() - start_time
#             if elapsed_time > 10:
#                 raise TimeoutError("Execution timed out")
#             green_text_out = green_text(f"passes {num_tests}/{num_tests} test cases")
#             print(f"Test {i}: {green_text_out}")
#             num_success += 1
#         except TimeoutError:
#             print(f"Test {i}: Execution timed out")
#         except Exception:
#             red_text_out = red_text(f"failed (exception)!")
#             print(f"Test {i}: {red_text_out}")
#     # else:
#     #     red_text_out = red_text(f"failed!")
#     #     print(f"Test {i}: {red_text_out}")
#     print(f"Summary: {num_success}/{len(data)} tests passed")
#     print(f"Acc: {round(num_success/len(data), 2)} tests passed")

# Validation by taking the code that performed the best on the internal tests
# also edit timeout so it actually works using multiprocessing
def validate_py_results(log_path: str):
    if not log_path.endswith(".jsonl"):
        raise ValueError("Please provide a valid log file")
    data = read_jsonl(log_path)
    num_success = 0
    for i, item in enumerate(data):
        # find the index of the solution with maximum "num_internal_completion_passing"
        max_index = max(range(len(item["num_internal_completion_passing"])), 
                        key=lambda index: item["num_internal_completion_passing"][index][0])
        func_impl = item["prompt"] + item["solution"][max_index]
        code = f'{func_impl}\n\n{item["test"]}\n\ncheck({item["entry_point"]})'
        num_tests = count_test_cases(item["test"])
        
        # Create queue to receive exception info
        queue = multiprocessing.Queue()

        def worker(q):
            try:
                exec(code, globals())
            except Exception as e:
                q.put(e)

        p = multiprocessing.Process(target=worker, args=(queue,))
        p.start()
        p.join(timeout=10)

        if p.is_alive():
            p.terminate()
            p.join()
            print(f"Test {i}: Execution timed out")
        else:
            error = queue.get() if not queue.empty() else None
            if error is None:
                green_text_out = green_text(f"passes {num_tests}/{num_tests} test cases")
                print(f"Test {i}: {green_text_out}")
                num_success += 1
            else:
                red_text_out = red_text(f"failed (exception)!")
                print(f"Test {i}: {red_text_out}")

    print(f"Summary: {num_success}/{len(data)} tests passed")
    print(f"Acc: {round(num_success/len(data), 2)} tests passed")

if __name__ == "__main__":
    validate_py_results(LOG_PATH)
