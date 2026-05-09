import site
import os

sp = site.getsitepackages()[0]
pyresparser_dir = os.path.join(sp, 'pyresparser')

# Fix 1: Patch constants.py for stopwords
f = os.path.join(pyresparser_dir, 'constants.py')
with open(f, 'r') as file:
    content = file.read()
content = content.replace(
    "STOPWORDS = set(stopwords.words('english'))",
    "try:\n    STOPWORDS = set(stopwords.words('english'))\nexcept:\n    STOPWORDS = set()"
)
with open(f, 'w') as file:
    file.write(content)
print("Patched constants.py!")

# Fix 2: Patch resume_parser.py to use en_core_web_sm
f2 = os.path.join(pyresparser_dir, 'resume_parser.py')
with open(f2, 'r') as file:
    content2 = file.read()
content2 = content2.replace(
    "custom_nlp = spacy.load(os.path.dirname(os.path.abspath(__file__)))",
    "custom_nlp = spacy.load('en_core_web_sm')"
)
with open(f2, 'w') as file:
    file.write(content2)
print("Patched resume_parser.py!")

# Fix 3: Patch utils.py for spacy v3 matcher API
f3 = os.path.join(pyresparser_dir, 'utils.py')
with open(f3, 'r') as file:
    content3 = file.read()

# Fix the matcher.add call and the pattern format
content3 = content3.replace(
    "matcher.add('NAME', None, *pattern)",
    "matcher.add('NAME', [list(pattern)])"
)
content3 = content3.replace(
    "matcher.add('NAME', [pattern])",
    "matcher.add('NAME', [list(pattern)])"
)
with open(f3, 'w') as file:
    file.write(content3)
print("Patched utils.py!")