#!/bin/bash
python main.py \
  --run_name "reflexion_scratch" \
  --root_dir "root" \
  --dataset_path ./human-eval/data/hold_out_HumanEval.jsonl.gz \
  --strategy "reflexion" \
  --language "py" \
  --model "gpt-4" \
  --num_gen "5" \
  --max_iters "1" \
  --verbose
