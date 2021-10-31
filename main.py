import argparse
import sys
from app import run_without_test, run_with_test
from atcodertools.common.logging import logger
import schedule
from time import sleep

DEFAULT_COMPLETION_API_ENDPOINT = 'https://api.openai.com/v1/engines/davinci-codex/completions'


def job(
        problem_id, contest_id, testcases, completion_endpoint, completion_parameter, language,
        translate, test):
  if test:
    run_with_test(problem_id, contest_id, testcases=testcases,
                  completion_endpoint=completion_endpoint,
                  completion_parameter=completion_parameter, language=language, translate=translate)
  else:
    run_without_test(problem_id, contest_id, testcases=testcases,
                     completion_endpoint=completion_endpoint,
                     completion_parameter=completion_parameter, language=language,
                     translate=translate)


def main(prog, args):
  parser = argparse.ArgumentParser(
      description='Fully-automated code submitter backed by OpenAI Codex.', prog=prog)
  parser.add_argument('contest_id', help='Contest ID (e.g. abc001)')
  parser.add_argument('problem_id', help='Problem ID (e.g. a)')
  parser.add_argument(
      '--run_at', metavar='HH:MM', default='',
      help='Schedule execution of this program at the time specified. If not specified, this program runs immediately.')
  parser.add_argument('--testcases', metavar='N', type=int, default=5,
                      help='The number of testcases retrieved from Codex at once.')
  parser.add_argument('--language', choices=['en', 'ja'], default='ja',
                      help='The target language extracted from the problem statement.')
  parser.add_argument(
      '--translate', action=argparse.BooleanOptionalAction, default=False,
      help='If specified, the submitter will try to translate given statement to English using Google Translate.')
  parser.add_argument(
      '--test', action=argparse.BooleanOptionalAction, default=False,
      help='Validate the submission by sample cases provided by challenge description before the actual submission.')
  parser.add_argument('--completion-endpoint', metavar='URL',
                      default=DEFAULT_COMPLETION_API_ENDPOINT,
                      help='The endpoint of API used for code completion.')
  parser.add_argument('--max-tokens', type=int, default=2048,
                      help='`max_tokens` parameter of OpenAI API.')
  parser.add_argument('--temperature', type=float,
                      help='`temperature` parameter of OpenAI API.')
  parser.add_argument('--top-p', type=float,
                      help='`top_p` parameter of OpenAI API.')
  parser.add_argument('--logprobs', type=int,
                      help='`logprobs` parameter of OpenAI API.')
  parser.add_argument('--presence-penalty', type=float,
                      help='`presence_penalty` parameter of OpenAI API.')
  parser.add_argument('--frequency-penalty', type=float,
                      help='`frequency_penalty` parameter of OpenAI API.')
  parser.add_argument('--best-of', type=int,
                      help='`best_of` parameter of OpenAI API.')

  parsed_args = parser.parse_args(args)

  completion_parameter = {}

  if parsed_args.max_tokens is not None:
    completion_parameter['max_tokens'] = parsed_args.max_tokens
  if parsed_args.temperature is not None:
    completion_parameter['temperature'] = parsed_args.temperature
  if parsed_args.top_p is not None:
    completion_parameter['top_p'] = parsed_args.top_p
  if parsed_args.logprobs is not None:
    completion_parameter['logprobs'] = parsed_args.logprobs
  if parsed_args.presence_penalty is not None:
    completion_parameter['presence_penalty'] = parsed_args.presence_penalty
  if parsed_args.frequency_penalty is not None:
    completion_parameter['frequency_penalty'] = parsed_args.frequency_penalty
  if parsed_args.best_of is not None:
    completion_parameter['best_of'] = parsed_args.best_of

  logger.info(f'Loaded config: contest = {parsed_args.contest_id}')
  logger.info(f'Loaded config: problem = {parsed_args.problem_id}')

  if parsed_args.run_at == '':
    job(problem_id=parsed_args.problem_id, contest_id=parsed_args.contest_id,
        testcases=parsed_args.testcases, completion_endpoint=parsed_args.completion_endpoint,
        completion_parameter=completion_parameter, language=parsed_args.language,
        translate=parsed_args.translate, test=parsed_args.test)
  else:
    schedule.every().day.at(parsed_args.run_at).do(
        job, problem_id=parsed_args.problem_id, contest_id=parsed_args.contest_id,
        testcases=parsed_args.testcases, completion_endpoint=parsed_args.completion_endpoint,
        completion_parameter=completion_parameter, language=parsed_args.language,
        translate=parsed_args.translate, test=parsed_args.test)

    logger.info('Waiting for the beginning of the contest...')
    while True:
      schedule.run_pending()
      sleep(0.1)


if __name__ == "__main__":
  main(sys.argv[0], sys.argv[1:])
