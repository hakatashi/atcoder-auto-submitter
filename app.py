from dotenv import load_dotenv
import schedule
import re
from time import sleep
import os
from atcodertools.common.logging import logger_io, logger
from atcodertools.codegen.template_engine import render
from onlinejudge_command.main import get_parser as oj_get_parser, run_program as oj_run_program
import requests
import json
from atcoder import get_prompt, get_template

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

with requests.get('https://api.github.com/copilot_internal/token', headers={'Authorization': f'token {GITHUB_TOKEN}'}) as req:
  data = req.json()
  token = data['token']

print(f'{token = }')

def get_completions(prompt, token, n):
  data = {
    "prompt": prompt,
    "max_tokens": 500,
    "temperature": 0.3,
    "top_p": 1,
    "n": n,
    "logprobs": 2,
    "stop": ["\n\n\n"],
    "stream": True,
  }

  headers = {
    'Authorization': f'Bearer {token}',
    "Openai-Organization": "github-copilot",
    "OpenAI-Intent": "copilot-ghost",
    "Content-Type": "application/json",
    "Accept": "application/json",
  }

  # COPILOT_COMPLETION = 'https://copilot.githubassets.com/v1/engines/github-multi-stochbpe-cushman-pii/completions'
  COPILOT_COMPLETION = 'https://copilot.githubassets.com/v1/engines/github-py-stochbpe-cushman-pii/completions'

  logger.info('Getting completion from GitHub Copilot...')
  with requests.post(COPILOT_COMPLETION, json=data, headers=headers) as req:
    response_data = req.text
  logger.info('Successfully retrieved completion data from GitHub Copilot.')

  outputs = {}

  for line in response_data.splitlines():
    if len(line) == 0:
      continue
    json_data = line.removeprefix('data: ')
    if json_data == '[DONE]':
      continue

    data = json.loads(json_data)
    choices = data['choices'] or []

    for choice in choices:
      if choice['index'] not in outputs:
        outputs[choice['index']] = ''

      outputs[choice['index']] += choice['text']

  logger.info(f'Successfully extracted {len(outputs)} outputs from completion.')

  return list(outputs.values())

def get_function(solve_function_definition, output):
  lines = output.splitlines()
  ret = [solve_function_definition.strip()]

  for line in lines:
    if len(ret) == 1 and line == '':
      continue
    if len(line) > 0 and line[0] != ' ' and line[0] != '\t':
      break
    ret.append(line.rstrip())

  return '\n'.join(ret)

def get_fingerprint(func):
  func = re.sub(r'#.+$', '', func, flags=re.M)
  func = re.sub(r'[\s()]', '', func)
  return func

def submit_code(code, execution_log, candidates, choice, contest, problem_index):
  problem = chr(ord('a') + problem_index)

  with open('template.py') as f:
    template = f.read()
  execution_log = re.sub(r"'+", "'", execution_log)

  submission = render(template, code=code, execution_log=execution_log, candidates=candidates, choice=choice)
  filename = f'submission{choice}.py'
  with open(filename, 'w') as f:
    f.write(submission)

  args = ['submit', f'https://atcoder.jp/contests/{contest}/tasks/{contest}_{problem}',
    filename, '--wait', '0', '--yes']

  parser = oj_get_parser()
  parsed = parser.parse_args(args=args)
  oj_run_program(parsed, parser=parser)

problem_index = 0

def job():
  global problem_index
  contest = 'abc209'

  logger.info('job started')
  en_statement_lines, intro_lines, solve_function_definition, outro_lines = get_template(contest, problem_index)
  prompt, notag_prompt = get_prompt(en_statement_lines, intro_lines, solve_function_definition)
  print(prompt)

  results = get_completions(prompt, token, 5)
  fingerprints = set()
  all_candidates = []
  candidates = []

  for i, result in enumerate(results):
    logger.info(f'Generating function and fingerprint from result {i + 1}...')
    func = get_function(solve_function_definition, result)
    fingerprint = get_fingerprint(func)
    all_candidates.append(func)
    if fingerprint not in fingerprints and len(func) < 800:
      candidates.append((i, result))
      fingerprints.add(fingerprint)

  if len(candidates) <= 1:
    logger.info(f'Too few candidates. Retrieving more data...')
    results = get_completions(prompt, token, 15)

    for i, result in enumerate(results):
      logger.info(f'Generating function and fingerprint from result {i + 1}...')
      func = get_function(solve_function_definition, result)
      fingerprint = get_fingerprint(func)
      all_candidates.append(func)
      if fingerprint not in fingerprints and len(func) < 800:
        candidates.append((i + 5, result))
        fingerprints.add(fingerprint)

  chosen_candidates = candidates[0:2]

  execution_log = logger_io.getvalue()

  for choice, result in chosen_candidates:
    outro = ''.join(outro_lines)
    if 'print' not in result:
      outro = re.sub(r'^(\s*)(solve\(.*\))$', r'\1print(\2)', outro, flags=re.M)
    additional_libraries = ['math', 're', 'bisect', 'collections', 'heapq', 'itertools', 'functools', 'fractions', 'numpy as np', 'numpy']
    header = ''.join(map(lambda l: f'import {l}\n', additional_libraries))
    code = header + notag_prompt + result + outro
    submit_code(code, execution_log, all_candidates, choice, contest, problem_index)
    logger.info('Waiting 5 seconds for another submission...')
    sleep(4)
  
  problem_index += 1

schedule.every().day.at("21:00").do(job)
schedule.every().day.at("21:01").do(job)
schedule.every().day.at("21:02").do(job)

while True:
  schedule.run_pending()
  sleep(0.1)

