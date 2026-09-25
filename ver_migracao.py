import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

import glob

arquivos = glob.glob('projetos/migrations/0004_*.py')
if not arquivos:
    print("❌ Nenhum arquivo 0004 encontrado")
else:
    with open(arquivos[0], 'r', encoding='utf-8') as f:
        print(f"=== CONTEÚDO DE {arquivos[0]} ===")
        print(f.read())

print()
print("=" * 60)
print("COLUNAS REAIS DA TABELA projetos_membroprojeto")
print("=" * 60)
from django.db import connection
cursor = connection.cursor()
cursor.execute("PRAGMA table_info(projetos_membroprojeto);")
for row in cursor.fetchall():
    print(f"  → {row[1]} ({row[2]})")

print()
print("=" * 60)
print("COLUNAS REAIS DA TABELA projetos_projeto")
print("=" * 60)
cursor.execute("PRAGMA table_info(projetos_projeto);")
for row in cursor.fetchall():
    print(f"  → {row[1]} ({row[2]})")