#!/bin/bash
# ==============================================================================
# REABITECH - SNAPSHOT DO PROJETO
# Gera um arquivo .txt com estrutura + conteudo dos arquivos-chave
# Pra colar numa IA em outra conversa sem perder contexto
#
# Uso:
#   bash snapshot.sh                -> modo essencial (~30k chars)
#   bash snapshot.sh medio          -> inclui views + base.html (~80k)
#   bash snapshot.sh completo       -> inclui templates + css + js (~200k)
#   bash snapshot.sh custom a.py b.py c.py -> so os arquivos passados
# ==============================================================================

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

MODO="${1:-essencial}"
shift || true
CUSTOM_FILES="$@"

OUTPUT="snapshot_reabitech.txt"

IGNORE_DIRS="__pycache__|\.git|\.venv|venv|node_modules|staticfiles|media|\.pytest_cache|htmlcov|\.vscode|\.idea"

ESSENCIAL=(
    "backend/settings.py"
    "backend/urls.py"
    "requirements.txt"
    "usuarios/models.py"
    "usuarios/urls.py"
    "projetos/models.py"
    "projetos/urls.py"
    "prontuario/models.py"
    "prontuario/urls.py"
    "consultas/models.py"
    "consultas/urls.py"
    "mensageria/models.py"
    "mensageria/urls.py"
    "analytics/urls.py"
    "fisioterapia/models.py"
    "psicologia/models.py"
)

MEDIO=(
    "${ESSENCIAL[@]}"
    "dashboard/views.py"
    "dashboard/urls.py"
    "dashboard/context_processors.py"
    "usuarios/signals.py"
    "consultas/signals.py"
    "mensageria/signals.py"
    "mensageria/views.py"
    "mensageria/forms.py"
    "mensageria/context_processors.py"
    "analytics/views.py"
    "analytics/utils.py"
    "prontuario/timeline_utils.py"
    "templates/base.html"
)

COMPLETO=(
    "${MEDIO[@]}"
    "popular_dados.py"
    "popular_mensageria.py"
    "templates/dashboard/fisioterapeuta/dashboard.html"
    "templates/dashboard/login.html"
    "static/css/premium-effects.css"
    "static/css/premium-pages.css"
    "static/css/premium-glass-3d.css"
    "static/css/glass-sidebar-3d.css"
    "static/js/premium-effects.js"
    "static/js/lenis-init.js"
)

case "$MODO" in
    essencial) FILES=("${ESSENCIAL[@]}") ;;
    medio)     FILES=("${MEDIO[@]}") ;;
    completo)  FILES=("${COMPLETO[@]}") ;;
    custom)
        if [ -z "$CUSTOM_FILES" ]; then
            echo -e "${YELLOW}Modo custom precisa de arquivos. Ex: bash snapshot.sh custom a.py b.py${NC}"
            exit 1
        fi
        FILES=($CUSTOM_FILES)
        ;;
    *)
        echo -e "${YELLOW}Modo invalido: ${MODO}${NC}"
        echo "Opcoes: essencial | medio | completo | custom"
        exit 1
        ;;
esac

echo -e "${CYAN}REABITECH Snapshot${NC}"
echo -e "${CYAN}Modo: ${MODO}${NC}"
echo ""

{
    echo "==============================================================="
    echo "REABITECH - SNAPSHOT DO PROJETO"
    echo "Gerado em: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Modo: ${MODO}"
    echo "==============================================================="
    echo ""

    echo "==============================================================="
    echo "ESTRUTURA DO PROJETO"
    echo "==============================================================="
    echo ""

    if command -v tree &> /dev/null; then
        tree -L 3 -I "${IGNORE_DIRS}" --noreport
    else
        find . -type d \
            -not -path "*/.git*" \
            -not -path "*/__pycache__*" \
            -not -path "*/venv*" -not -path "*/.venv*" \
            -not -path "*/node_modules*" \
            -not -path "*/staticfiles*" \
            -not -path "*/media*" \
            -not -path "*/.pytest_cache*" \
            -not -path "*/htmlcov*" \
            -not -path "*/.vscode*" \
            | sort
    fi

    echo ""
    echo "==============================================================="
    echo "CONTEUDO DOS ARQUIVOS"
    echo "==============================================================="
    echo ""

    TOTAL=0
    for f in "${FILES[@]}"; do
        [ -f "$f" ] && TOTAL=$((TOTAL + 1))
    done

    echo "Total de arquivos incluidos: ${TOTAL}"
    echo ""

    for f in "${FILES[@]}"; do
        if [ ! -f "$f" ]; then
            echo "==============================================================="
            echo "ARQUIVO: $f (NAO ENCONTRADO)"
            echo "==============================================================="
            echo ""
            continue
        fi

        echo "==============================================================="
        echo "ARQUIVO: $f"
        echo "==============================================================="
        echo ""
        cat "$f"
        echo ""
        echo ""
    done

    echo "==============================================================="
    echo "FIM DO SNAPSHOT"
    echo "==============================================================="
} > "$OUTPUT"

SIZE=$(wc -c < "$OUTPUT")
LINES=$(wc -l < "$OUTPUT")
KB=$((SIZE / 1024))

echo ""
echo -e "${GREEN}OK: Snapshot gerado${NC}"
echo -e "  Arquivo:  ${CYAN}${OUTPUT}${NC}"
echo -e "  Tamanho:  ${SIZE} bytes (${KB} KB)"
echo -e "  Linhas:   ${LINES}"
echo -e "  Modo:     ${MODO}"
echo ""
echo -e "${YELLOW}Pra copiar e colar numa IA:${NC}"
echo -e "  Windows (clipboard):  ${CYAN}cat ${OUTPUT} | clip${NC}"
echo -e "  Ver no terminal:      ${CYAN}cat ${OUTPUT}${NC}"
echo ""
