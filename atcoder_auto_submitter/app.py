# Copyright 2021 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import re
import os
import json
from time import sleep
from tempfile import NamedTemporaryFile, TemporaryDirectory
from pathlib import Path
from dotenv import load_dotenv
from atcodertools.common.logging import logger_io, logger
from atcodertools.codegen.template_engine import render
from onlinejudge_command.main import get_parser as oj_get_parser, run_program as oj_run_program
import requests
from atcoder_auto_submitter.atcoder import get_prompt, get_template

load_dotenv(dotenv_path=Path.home() / '.config/atcoder-auto-submitter/.env')
OPENAI_TOKEN = os.getenv('OPENAI_TOKEN')

dirname = Path(__file__).parent

def get_completions(prompt, token, testcases, completion_endpoint, completion_parameter):
  data = {
      **completion_parameter,
      "prompt": prompt,
      "n": testcases,
      "stop": ["\n\n\n"],
      "stream": True,
  }

  headers = {
      'Authorization': f'Bearer {token}',
      "OpenAI-Intent": "copilot-ghost",
      "Content-Type": "application/json",
      "Accept": "application/json",
  }

  logger.info('Getting completion from OpenAI Codex...')
  # TODO: Process as stream
  with requests.post(completion_endpoint, json=data, headers=headers) as req:
    response_data = req.text
  logger.info('Successfully retrieved completion data from OpenAI Codex.')

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

  logger.info(f'Successfully extracted {len(outputs)} candidates from completion.')

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


def submit_code(code, execution_log, candidates, choice, contest, problem_id):
  with open(dirname / 'template.py.jinja') as f:
    template = f.read()
  execution_log = re.sub(r"'+", "'", execution_log)

  submission = render(template, code=code, execution_log=execution_log,
                      candidates=candidates, choice=choice)

  with NamedTemporaryFile() as f:
    filename = f.name
    f.write(submission.encode())

    args = ['submit', f'https://atcoder.jp/contests/{contest}/tasks/{contest}_{problem_id}',
            filename, '--wait', '0', '--yes', '--language', 'python']

    parser = oj_get_parser()
    parsed = parser.parse_args(args=args)
    return oj_run_program(parsed, parser=parser)


def download_tests(contest, problem_id):
  url = f'https://atcoder.jp/contests/{contest}/tasks/{contest}_{problem_id}'

  testdir = TemporaryDirectory()
  args = ['download', url, '--directory', testdir.name]

  parser = oj_get_parser()
  while True:
    logger.info('Downloading test cases...')
    exit_code = oj_run_program(parser.parse_args(args=args), parser=parser)
    if exit_code == 0:
      break
    logger.info('Test case extraction failed. Trying after 0.5s...')
    sleep(0.5)

  logger.info('Test cases downloaded.')

  return testdir


def verify_code(code, execution_log, candidates, choice, testdir):
  with open(dirname / 'template.py') as f:
    template = f.read()
  execution_log = re.sub(r"'+", "'", execution_log)

  submission = render(template, code=code, execution_log=execution_log,
                      candidates=candidates, choice=choice)

  with NamedTemporaryFile() as f:
    filename = f.name
    f.write(submission.encode())

    args = ['test', '--command', f'python {filename}',
            '--directory', testdir.name, '--mle', '50', '--tle', '1']

    parser = oj_get_parser()
    logger.info(f'Verifying candidate {choice}...')
    exit_code = oj_run_program(parser.parse_args(args=args), parser=parser)

  logger.info(f'Verification finished. exit code = {exit_code}')
  return exit_code


def run_without_test(problem_id,
                     contest_id, testcases, completion_endpoint, completion_parameter, language,
                     translate):
  if OPENAI_TOKEN is None:
    logger.critical('OPENAI_TOKEN is not set')
    exit(1)

  logger.info(f'job started (contest = {contest_id}, problem id = {problem_id})')
  en_statement_lines, intro_lines, solve_function_definition, outro_lines = get_template(
      contest_id, problem_id, language, translate)
  prompt, notag_prompt = get_prompt(en_statement_lines, intro_lines, solve_function_definition)

  results = get_completions(prompt, OPENAI_TOKEN, testcases,
                            completion_endpoint, completion_parameter)
  fingerprints = set()
  all_candidates = []
  candidates = []

  logger.info(f'Generating function and fingerprints...')
  for i, result in enumerate(results):
    func = get_function(solve_function_definition, result)
    fingerprint = get_fingerprint(func)
    all_candidates.append(func)
    if fingerprint not in fingerprints and len(func) < 800:
      candidates.append((i, result))
      fingerprints.add(fingerprint)

  chosen_candidates = candidates[0:1]

  execution_log = logger_io.getvalue()

  for choice, result in chosen_candidates:
    outro = ''.join(outro_lines)
    if 'print' not in result:
      outro = re.sub(r'^(\s*)(solve\(.*\))$', r'\1print(\2)', outro, flags=re.M)
    additional_libraries = ['math', 're', 'bisect', 'collections', 'heapq',
                            'itertools', 'functools', 'fractions', 'numpy as np', 'numpy']
    header = ''.join(map(lambda l: f'import {l}\n', additional_libraries))
    code = header + notag_prompt + result + outro

    while True:
      exit_code = submit_code(code, execution_log, all_candidates, choice, contest_id, problem_id)
      if exit_code == 0:
        break
      logger.info('submission failed. Trying after 0.5s...')
      sleep(0.5)

    logger.info('submission succeeded.')


def run_with_test(problem_id,
                  contest_id, testcases, completion_endpoint, completion_parameter, language,
                  translate):
  if OPENAI_TOKEN is None:
    logger.critical('OPENAI_TOKEN is not set')
    exit(1)

  logger.info(f'job started (contest = {contest_id}, problem id = {problem_id})')
  en_statement_lines, intro_lines, solve_function_definition, outro_lines = get_template(
      contest_id, problem_id, language, translate)
  prompt, notag_prompt = get_prompt(en_statement_lines, intro_lines, solve_function_definition)

  while True:
    results = get_completions(prompt, OPENAI_TOKEN, testcases,
                              completion_endpoint, completion_parameter)
    fingerprints = set()
    all_candidates = []
    candidates = []

    logger.info(f'Generating function and fingerprints...')
    for i, result in enumerate(results):
      func = get_function(solve_function_definition, result)
      fingerprint = get_fingerprint(func)
      all_candidates.append(func)
      if fingerprint not in fingerprints and len(func) < 800:
        candidates.append((i, result))
        fingerprints.add(fingerprint)

    testdir = download_tests(contest_id, problem_id)

    for choice, result in candidates:
      outro = ''.join(outro_lines)
      if 'print' not in result:
        outro = re.sub(r'^(\s*)(solve\(.*\))$', r'\1print(\2)', outro, flags=re.M)
      additional_libraries = ['math', 're', 'bisect', 'collections', 'heapq',
                              'itertools', 'functools', 'fractions', 'numpy as np', 'numpy']
      header = ''.join(map(lambda l: f'import {l}\n', additional_libraries))
      code = header + notag_prompt + result + outro

      execution_log = logger_io.getvalue()
      exit_code = verify_code(code, execution_log, all_candidates, choice, testdir)
      if exit_code != 0:
        logger.info('Test didn\'t pass. Trying another candidate...')
        continue

      logger.info('Test passed. Submitting the code...')

      while True:
        execution_log = logger_io.getvalue()
        exit_code = submit_code(code, execution_log, all_candidates, choice, contest_id, problem_id)
        if exit_code == 0:
          break
        logger.info('Submission failed. Trying after 0.5s...')
        sleep(0.5)
      logger.info('Submission succeeded.')
      testdir.cleanup()
      return 0
