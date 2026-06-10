from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pdfplumber
import os
import re

app = FastAPI(
    title="Manual Nobreak FXP-2000",
    description="Extração de informações técnicas do Manual do Nobreak FXP-2000",
    version="1.0"
)

PDF_PATH = os.path.join(os.path.dirname(__file__), "manual_avancado_nobreak_fxp2000.pdf")

SECOES = [
    "Introdução",
    "Aplicações Recomendadas",
    "Instalação",
    "Características Técnicas",
    "Painel de Controle",
    "Modos de Operação",
    "Alarmes e Diagnóstico",
    "Manutenção da Bateria",
    "Especificações Adicionais",
    "Suporte Técnico"
]


def extrair_texto_pdf() -> str:
    """Extrai todo o texto do PDF."""
    if not os.path.exists(PDF_PATH):
        raise HTTPException(status_code=404, detail="Arquivo PDF do manual não encontrado.")
    texto = ""
    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            texto += page.extract_text() + "\n"
    return texto


def extrair_secao(texto_completo: str, secao: str) -> str:
    """Extrai o conteúdo de uma seção específica do texto do PDF."""
    # Procura a seção pelo número + nome ou só pelo nome
    padrao_inicio = re.compile(
        rf"(\d+\.\s*)?{re.escape(secao)}",
        re.IGNORECASE
    )

    match_inicio = padrao_inicio.search(texto_completo)
    if not match_inicio:
        return None

    inicio = match_inicio.start()

    # Procura a próxima seção numerada para delimitar o fim
    padrao_proxima = re.compile(r"\n\d+\.\s+[A-ZÁÉÍÓÚÂÊÔÃÕÇ]", re.MULTILINE)
    match_fim = padrao_proxima.search(texto_completo, match_inicio.end())

    if match_fim:
        conteudo = texto_completo[inicio:match_fim.start()]
    else:
        conteudo = texto_completo[inicio:]

    return conteudo.strip()


# ──────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────

@app.get("/api/listar_secoes")
def listar_secoes():
    """Lista todas as seções disponíveis no manual."""
    return {
        "data": [{"secao": s} for s in SECOES]
    }


class RequestConsultaSecao(BaseModel):
    secao: str


@app.post("/api/consultar_secao")
def consultar_secao(body: RequestConsultaSecao):
    """Retorna o conteúdo de uma seção específica do manual."""
    secao = body.secao.strip()

    if secao not in SECOES:
        raise HTTPException(
            status_code=400,
            detail=f"Seção '{secao}' não encontrada. Use GET /api/listar_secoes para ver as opções."
        )

    texto_completo = extrair_texto_pdf()
    conteudo = extrair_secao(texto_completo, secao)

    if not conteudo:
        raise HTTPException(
            status_code=404,
            detail=f"Não foi possível extrair o conteúdo da seção '{secao}'."
        )

    return {
        "secao": secao,
        "conteudo": conteudo
    }
