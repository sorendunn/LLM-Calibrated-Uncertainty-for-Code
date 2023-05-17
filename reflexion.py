from utils import write_jsonl, parse_body
from executors import py_evaluate, py_execute
from generators import py_generate_func_impl, py_generate_self_reflection, py_generate_internal_tests
from typing import Dict
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from typing import List

# Test to make reflexion code run in parallel
def run_reflexion(
        dataset: List[dict],
        model: str,
        language: str,
        max_iters: int,
        num_gen: int,
        log_path: str,
        verbose: bool
    ) -> None:
    # should handle more languages later
    # someone do this but arrange it better
    print("starting to run reflexion")
    evaluate = None
    execute = None
    self_reflection_generator = None
    func_impl_generator = None
    internal_test_generator = None
    if language == "python" or language == "py":
        evaluate = py_evaluate
        execute = py_execute
        self_reflection_generator = py_generate_self_reflection
        func_impl_generator = py_generate_func_impl
        internal_test_generator = py_generate_internal_tests
    else:
        raise NotImplementedError(f"language {language} not supported")

    assert not evaluate is None
    assert not execute is None
    assert not self_reflection_generator is None
    assert not func_impl_generator is None
    assert not internal_test_generator is None

    num_items = len(dataset)
    num_success = 0
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = {executor.submit(process_item, i, item, model, language, max_iters, num_gen, evaluate, execute, self_reflection_generator, func_impl_generator, internal_test_generator, log_path): item for i, item in enumerate(dataset)}
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            try:
                data = future.result()
            except Exception as exc:
                print('generated an exception:')
            else:
                print("else statement")

def process_item(i, item, model, language, max_iters, num_gen, evaluate, execute, self_reflection_generator, func_impl_generator, internal_test_generator, log_path) -> Dict:
    cur_pass = 0
    is_solved = []
    reflections = []
    cur_func_impl = ""
    num_passing = []
    solutions = []

    prompt = item["prompt"]

    gen_type = "code"

    if gen_type != "code":
        prompt = get_target_function(item["prompt"], model)

    tests_i = internal_test_generator(prompt, model, 1)
    print(tests_i)
    
    # evaluating the real code on the given tests
    #num_real_passing = [execute(item["prompt"]+item["canonical_solution"], tests_i)]
    #print("evaluated real code on tests")

    # Num gen is the number of sample functions to generate for each prompt 
    while cur_pass < num_gen:
        # first attempt
        cur_func_impl = parse_body(func_impl_generator(prompt, model, "simple"))
            
        # check if all internal unit tests pass
        passing_num, cur_feedback = execute(cur_func_impl, tests_i)
        num_passing.append([passing_num,cur_feedback])
        solutions.append(cur_func_impl)
        print("finished checking internal tests")

        is_passing = evaluate(item["entry_point"], cur_func_impl, item["test"], timeout=10)
            
        if is_passing:
            is_solved.append(True)
        else:
            is_solved.append(False)
            
        if passing_num == len(tests_i):
            break

        # use self-reflection to iteratively improve
        cur_iter = 1
        while cur_iter < max_iters:
            # get self-reflection
            reflection = self_reflection_generator(cur_func_impl, cur_feedback, model)
            
            reflections += [reflection]

            # apply self-reflection in the next attempt
            cur_func_impl = parse_body(func_impl_generator(
                func_sig=prompt,
                model=model,
                strategy="reflexion",
                prev_func_impl=cur_func_impl,
                feedback=cur_feedback,
                self_reflection=reflection
            ))

            # add current function body to the list of solutions

            # check if all internal unit tests pass
            passing_num, cur_feedback = execute(cur_func_impl, tests_i)
            num_passing.append([passing_num,cur_feedback])
            solutions.append(cur_func_impl)
            
            is_passing = evaluate(item["entry_point"], cur_func_impl, item["test"], timeout=10)
            if is_passing:
                is_solved.append(True)
            else:
                is_solved.append(False)
                
            if passing_num == len(tests_i):
                break

            cur_iter += 1
        cur_pass += 1

    item["is_solved"] = is_solved
    item["reflections"] = reflections
    item["solution"] = solutions
    item["internal_tests"] = tests_i
    item["num_internal_completion_passing"] = num_passing
    #item["num_real_passing"] = num_real_passing
    write_jsonl(log_path, [item], append=True)

    return item
