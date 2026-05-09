import site
import os

sp = site.getsitepackages()[0]
f = os.path.join(sp, 'pyresparser/constants.py')

with open(f, 'r') as file:
    content = file.read()

content = content.replace(
    "STOPWORDS = set(stopwords.words('english'))",
    "try:\n    STOPWORDS = set(stopwords.words('english'))\nexcept:\n    STOPWORDS = set()"
)

with open(f, 'w') as file:
    file.write(content)

print("Patched successfully!")