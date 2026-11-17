import hashlib
from datetime import timedelta
from django.utils import timezone
from django.core.files.base import ContentFile
from projetos.models import ProntuarioArquivado

def calcular_hash_sha256(arquivo):
    """
    Calcula o Hash SHA-256 de um arquivo em memória (BytesIO) ou físico.
    """
    sha256_hash = hashlib.sha256()
    
    if hasattr(arquivo, 'seek'):
        arquivo.seek(0)

    for chunk in iter(lambda: arquivo.read(4096), b""):
        sha256_hash.update(chunk)
        
    return sha256_hash.hexdigest()

def processar_arquivamento_frio(projeto, prontuario, arquivo_pdf_gerado):
    """
    Recebe o PDF gerado, calcula o Hash e arquiva por 20 anos.
    """
    hash_integridade = calcular_hash_sha256(arquivo_pdf_gerado)
    
    if hasattr(arquivo_pdf_gerado, 'seek'):
        arquivo_pdf_gerado.seek(0)

    data_hoje = timezone.now().date()
    data_expiracao = data_hoje + timedelta(days=365*20)

    prontuario_arquivado = ProntuarioArquivado(
        prontuario=prontuario,
        hash_sha256=hash_integridade,
        data_expiracao=data_expiracao
    )
    
    nome_arquivo = f"prontuario_{prontuario.numero_prontuario}_{data_hoje}.pdf"
    prontuario_arquivado.arquivo_pdf.save(
        nome_arquivo, 
        ContentFile(arquivo_pdf_gerado.read()), 
        save=True
    )
    
    return prontuario_arquivado, hash_integridade
