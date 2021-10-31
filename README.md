# atcoder-auto-submitter-by-copilot

## Usage

```
$ python main.py --help
usage: main.py [-h] [--run_at HH:MM] [--testcases N] [--language {en,ja}]
               [--translate | --no-translate] [--test | --no-test]
               [--completion-endpoint URL] [--max-tokens MAX_TOKENS]
               [--temperature TEMPERATURE] [--top-p TOP_P] [--logprobs LOGPROBS]
               [--presence-penalty PRESENCE_PENALTY]
               [--frequency-penalty FREQUENCY_PENALTY] [--best-of BEST_OF]
               contest_id problem_id

Fully-automated AtCoder submitter backed by OpenAI Codex.

positional arguments:
  contest_id            Contest ID (e.g. abc001)
  problem_id            Problem ID (e.g. a)

optional arguments:
  -h, --help            show this help message and exit
  --run_at HH:MM        Schedule execution of this program at the time specified.
                        If not specified, this program runs immediately.
  --testcases N         The number of testcases retrieved from Codex at once.
  --language {en,ja}    The target language extracted from the problem statement.
  --translate, --no-translate
                        If specified, the submitter will try to translate given
                        statement to English using Google Translate. (default:
                        False)
  --test, --no-test     Validate the submission by sample cases provided by
                        challenge description before the actual submission.
                        (default: False)
  --completion-endpoint URL
                        The endpoint of API used for code completion.
  --max-tokens MAX_TOKENS
                        `max_tokens` parameter of OpenAI API.
  --temperature TEMPERATURE
                        `temperature` parameter of OpenAI API.
  --top-p TOP_P         `top_p` parameter of OpenAI API.
  --logprobs LOGPROBS   `logprobs` parameter of OpenAI API.
  --presence-penalty PRESENCE_PENALTY
                        `presence_penalty` parameter of OpenAI API.
  --frequency-penalty FREQUENCY_PENALTY
                        `frequency_penalty` parameter of OpenAI API.
  --best-of BEST_OF     `best_of` parameter of OpenAI API.
```