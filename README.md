# atcoder-auto-submitter

Fully-automated AtCoder submitter backed by OpenAI Codex.

This is not an officially supported Google product.

## ⚠Deprecation Notice⚠

Due to the rule changes made by AtCoder on June 7, 2024, using this tool during AtCoder Beginners Contest will be a violation of the contest rules. For details, please see "[Rule changes in ABC due to the rise of generative AI.](https://atcoder.jp/posts/1246)"

In addition, since this tool has no intended use other than taking the fastest in ABC, this repository will be deprecated and archived.

2024年6月7日のAtCoder社のルール変更に伴い、AtCoder Beginners Contest の開催中に本ツールを利用することはコンテストのルール違反となります。詳しくは『[生成AIの台頭に伴うABCにおけるルール変更について](https://atcoder.jp/posts/1246)』をご覧ください。

なお、本ツールはABCのFastestを取る以外の想定用途がないことから、このリポジトリはdeprecateとし、アーカイブいたします。

## Setup

1. Install this module and [atcoder-tools](https://github.com/kyuridenamida/atcoder-tools).

    ```
    pip install git+https://github.com/hakatashi/atcoder-auto-submitter atcoder-tools
    ```

2. Make sure you are logged in with atcoder-tools.

    ```
    atcoder-tools gen abc001
    ```

3. Store necessary API keys into `~/.config/atcoder-auto-submitter/.env`

    ```
    mkdir -p ~/.config/atcoder-auto-submitter
    curl -L https://github.com/hakatashi/atcoder-auto-submitter/raw/main/.env.example -o ~/.config/atcoder-auto-submitter/.env
    vi ~/.config/atcoder-auto-submitter/.env
    ```

4. Have fun!

    ```
    atcoder-auto-submitter abc222 a
    ```

## Usage

```
$ atcoder-auto-submitter --help
usage: atcoder-auto-submitter
       [-h] [--run_at HH:MM] [--testcases N] [--language {en,ja}]
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
  --run_at HH:MM        Schedule execution of this program at the time
                        specified. If not specified, this program runs
                        immediately.
  --testcases N         The number of testcases retrieved from Codex at once.
  --language {en,ja}    The target language extracted from the problem
                        statement.
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
