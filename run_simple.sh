#!/bin/bash
python main.py \
  --run_name "simple_scratch" \
  --root_dir "root" \
  --dataset_path ./human-eval/data/HumanEval.jsonl.gz \
  --strategy "simple" \
  --language "py" \
  --model "gpt-3.5-turbo" \
  --max_iters "1" \
  --verbose
