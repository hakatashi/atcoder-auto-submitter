from atcodertools.tools.envgen import main as envgen_main
from bs4 import BeautifulSoup
from atcodertools.common.logging import logger
from pathlib import Path
from googletrans import Translator

translator = Translator()

def flatmap(f, xs):
  ys = []
  for x in xs:
    ys.extend(f(x))
  return ys

def find_index(f, xs):
  for i, x in enumerate(xs):
    if f(x):
      return i
  return -1

def get_template(contest, problem_id, language='en', translate=False):
  logger.info('Invoking atcoder-tools...')

  problem_index = ord(problem_id) - ord('a')

  res = envgen_main(
    "python a.py",
    [contest, "--lang", "python", "--config", ".atcodertools.toml"],
    problem_index
  )

  problem_a_html = res[0].original_html
  soup = BeautifulSoup(problem_a_html, features="lxml")
  en_descriptions = soup.find("span", {"class": f'lang-{language}'})
  if en_descriptions is None:
    raise Exception(f'Statement with language = {language} not found')
  en_sections = en_descriptions.findAll("div", {"class": "part"})
  en_statement = en_sections[0]

  en_output_section = None
  for section in en_sections:
    h3 = section.find('h3')
    if h3 and h3.get_text() == 'Output':
      en_output_section = section

  en_statement_tags = en_statement.findAll(['p', 'ul', 'ol'])

  en_statement_lines = []
  for tag in en_statement_tags:
    if tag.name == 'p':
      en_statement_lines.extend(tag.get_text().split('\r\n'))
    else:
      li_elements = tag.findAll('li')
      if tag.name == 'ul':
        en_statement_lines.extend(map(lambda el: f'* {el.get_text()}', li_elements))
      elif tag.name == 'ol':
        en_statement_lines.extend(map(
          lambda d: f'{d[0] + 1}. {d[1].get_text()}',
          enumerate(li_elements)
        ))
  
  if en_output_section is not None:
    codes = en_output_section.find('code')
    if codes is not None or '-1' in en_output_section.get_text():
      en_output_section_tags = en_output_section.findAll('p')
      for tag in en_output_section_tags:
        en_statement_lines.extend(tag.get_text().split('\r\n'))

  logger.info(f'Problem statement extracted: {en_statement_lines}')

  if translate:
    logger.info(f'Translating statement...')
    translation_result = translator.translate('\n'.join(en_statement_lines))
    logger.info(f'Translation succeeded: {translation_result.text.splitlines()}')
    en_statement_lines = translation_result.text.splitlines()

  template_path = Path('workspace', contest, chr(ord('A') + problem_index), 'main.py')
  with template_path.open() as f:
    template_lines = list(f)

  logger.info('Read generated code from atcoder-tools.')

  # Strips shebang
  template_lines = template_lines[1:]

  solve_function_definition_index = find_index(lambda line: 'solve' in line, template_lines)
  solve_function_definition = template_lines[solve_function_definition_index]

  logger.info(f'Extracted the definition of solve function: {solve_function_definition.strip()}')

  intro_lines = template_lines[:solve_function_definition_index]
  outro_lines = template_lines[solve_function_definition_index+2:]

  return en_statement_lines, intro_lines, solve_function_definition, outro_lines

def normalize_statement_line(line):
  return line \
    .replace('\\neq', '!=') \
    .replace('\\,', ' ') \
    .replace('\\times', 'x') \
    .replace('\\leq', '<=') \
    .replace('\\le', '<=') \
    .replace('\\lt', '<') \
    .replace('\\geq', '>=') \
    .replace('\\ge', '>=') \
    .replace('\\gt', '>') \
    .replace('\\dots', '...') \
    .replace('\\cdots', '...') \
    .replace('\\ldots', '...') \
    .replace('^', ' ** ') \
    .replace('\\mathrm', '') \
    .strip()

def get_prompt(en_statement_lines, intro_lines, solve_function_definition):
  statement_lines = map(normalize_statement_line, en_statement_lines)
  comment_lines = list(map(lambda line: f'# {line}\n', statement_lines))

  tag_lines = []

  prompt_lines = tag_lines + intro_lines + comment_lines + [solve_function_definition]
  notag_prompt_lines = intro_lines + comment_lines + [solve_function_definition]
  return ''.join(prompt_lines).strip(), ''.join(notag_prompt_lines).strip()

