- I have implemented a web scraper and the scraper initially outputed a JSON result before adding "locator_type","locator",html_id".

- After adding the three fields the following error appears.

File "C:\Users\devis\web-scrapping-automate\.venv\Lib\site-packages\soupsieve\css_parser.py", line 891, in parse_pseudo_class
    raise SelectorSyntaxError(
soupsieve.util.SelectorSyntaxError: ':outline-none' was detected as a pseudo-class and is either unsupported or invalid. If the syntax was not intended to be recognized as a pseudo-class, please escape the colon.
  line 1:
input.w-10.h-12.text-center.text-xl.font-mono.border-b.border-zinc-600.text-cyan-400.focus:outline-none.focus:border-cyan-400

