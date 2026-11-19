import os
p = "projetos/views.py"
if not os.path.isfile(p):
    print("(nao encontrado)")
else:
    with open(p, encoding="utf-8", errors="replace") as fh:
        linhas = fh.readlines()
    for i, linha in enumerate(linhas, 1):
        if 55 <= i <= 105:
            print(f"{i:04d}: {linha}", end="")
