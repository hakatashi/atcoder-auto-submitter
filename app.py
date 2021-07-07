from dotenv import load_dotenv
import os
import requests
import json
from textwrap import dedent

load_dotenv()

GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')

with requests.get('https://api.github.com/copilot_internal/token', headers={'Authorization': f'token {GITHUB_TOKEN}'}) as req:
  data = req.json()
  token = data['token']

def get_completions(prompt, token):
  data = {
    "prompt": prompt,
    "max_tokens": 1000,
    "temperature": 0.3,
    "top_p": 1,
    "n": 8,
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

  with requests.post(COPILOT_COMPLETION, json=data, headers=headers) as req:
    response_data = req.text

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

  results = []
  for text in outputs.values():
    results.append(text)

  return results

results = get_completions(dedent('''
  / Language: python
  // Path: solve.py
  # A condominium AtCoder has N floors, called the 1-st floor through the N-th floor. Each floor has K rooms, called the 1-st room through the K-th room.
  # Here, both N and K are one-digit integers, and the j-th room on the i-th floor has the room number "i0j". For example, the 2-nd room on the 1-st floor has the room number 102.
  # Takahashi, the manager, got interested in the sum of the room numbers of all rooms in the condominium, where each room number is seen as a three-digit integer. Find this sum.
  def solve(N: int, K: int):
''').strip(), token)
print(results)
