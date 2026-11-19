import os, glob
cands = glob.glob("*/settings.py") + ["settings.py"]
for f in cands:
    print("\n===== " + f + " =====")
    with open(f, encoding="utf-8", errors="replace") as fh:
        txt = fh.read()
    for chave in ("INSTALLED_APPS", "TEMPLATES", "STATICFILES_DIRS", "STATIC_ROOT", "LOGIN_URL", "LOGIN_REDIRECT_URL"):
        i = txt.find(chave)
        if i != -1:
            print("--- " + chave + " ---")
            print(txt[i:i+900])
