import os
files = [
    "templates/projetos/landing.html",
    "projetos/landing.html",
    "projetos/urls.py",
]
for f in files:
    print("\n===== " + f + " =====")
    if os.path.isfile(f):
        with open(f, encoding="utf-8", errors="replace") as fh:
            print(fh.read())
    else:
        print("(nao encontrado)")
