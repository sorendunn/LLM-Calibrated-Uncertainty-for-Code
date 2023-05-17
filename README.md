# LLM-Calibrated-Uncertainty-for-Code

 Repository for "Achieving Calibrated Uncertainty for Code Generation with Large Language Models."

- **calibration_plots.ipynb** - Code to create calibration plots for the finished runs
- **README.md**
- **reflexion.py** - Main code overseeing generation of functions and internal test cases. Works both for reflexion and without using reflexion
- **run_gen_5.sh** - Code to specify parameters for run. In these examples I generated 5 functions for each prompt
- **run_validate.sh** - Specify the run to validate when running validate_py_results.py
- **subset_human_eval.ipynb** - Code to generate subsets of HumanEval for training/testing
- **uncertainty_utils.py** - Helper functions for calibration_plots.ipynb
- **utils.py** - jsonl utils
- **validate_py_results.py** - Calculate the percent accuracy from the run specified in run_validate.sh (taking the generation with the best performance on internal test cases as the final answer for each prompt)
- **executors/** - functions to extract and execute the code from the language model responses. Improved from the "Mastering HumanEval Repository" to run faster with multiprocessing
- **generators/**  - functions to query language model
- **human-eval/** - the humaneval dataset and code to generate it

Feel free to reach out if you have any questions about the code or would be interested in collaborating on future work of this sort.

Acknowledgements: The base code for this repository is based off of "Mastering HumanEval with Reflexion" (https://github.com/GammaTauAI/reflexion-human-eval/tree/main).
