import os
import ast

PASTA_PROJETO = '.'
DIRETORIOS_IGNORADOS = ['.git', '__pycache__', 'migrations', 'venv', 'env', 'node_modules', 'media']

def analisar_python(caminho_arquivo):
    try:
        with open(caminho_arquivo, 'r', encoding='utf-8') as f:
            conteudo = f.read()
        arvore = ast.parse(conteudo)
        
        resultado = []
        for no in arvore.body:
            if isinstance(no, ast.ClassDef):
                resultado.append(f"  - Classe: {no.name}")
                for item in no.body:
                    if isinstance(item, ast.FunctionDef):
                        resultado.append(f"      Def: {item.name}")
            elif isinstance(no, ast.FunctionDef):
                resultado.append(f"  - Função: {no.name}")
        return resultado
    except Exception as e:
        return [f"  - [Aviso: Não foi possível analisar o interior do ficheiro]"]

def gerar_mapa():
    mapa = "# MAPA DE ARQUITETURA - REABITECH (TCC)\n"
    mapa += "Este documento contém a árvore de diretórios, ficheiros e as assinaturas de classes/funções em Python do projeto.\n\n"
    
    print("A gerar o mapa do projeto...")
    
    for root, dirs, files in os.walk(PASTA_PROJETO):
        # Filtra os diretórios que não devem ser lidos
        dirs[:] = [d for d in dirs if d not in DIRETORIOS_IGNORADOS]
        
        # Filtra ficheiros válidos
        arquivos_validos = [f for f in files if f.endswith(('.py', '.html', '.css', '.js'))]
        
        if not arquivos_validos:
            continue
            
        nivel = root.replace(PASTA_PROJETO, '').count(os.sep)
        indentacao = ' ' * 4 * nivel
        nome_pasta = os.path.basename(root) if root != PASTA_PROJETO else 'RAIZ DO PROJETO'
        
        mapa += f"\n{indentacao}[📁 DIRETÓRIO: {nome_pasta}]\n"
        
        for file in arquivos_validos:
            caminho_completo = os.path.join(root, file)
            mapa += f"{indentacao}    📄 {file}\n"
            
            # Se for Python, extrai as classes e funções
            if file.endswith('.py'):
                detalhes = analisar_python(caminho_completo)
                for detalhe in detalhes:
                    mapa += f"{indentacao}    {detalhe}\n"
                    
    nome_ficheiro_saida = 'mapa_arquitetura_reabitech.txt'
    with open(nome_ficheiro_saida, 'w', encoding='utf-8') as f:
        f.write(mapa)
        
    print(f"Sucesso! O ficheiro {nome_ficheiro_saida} foi criado.")

if __name__ == '__main__':
    gerar_mapa()