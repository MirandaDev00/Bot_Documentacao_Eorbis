# config.py

import os

# Caminho para o diretório de saída temporário para o transformer
OUTPUT_DIR = "temp_output"

# URL para pegar a versão do E-Orbis (sem login)
VERSAO_URL = "http://192.168.99.183:8585/eorbis/"

# URL base para links de imagens do Obsidian no HTML gerado
URL_BASE_IMAGENS = "https://raw.githubusercontent.com/MirandaDev00/Bot_Documentacao_Eorbis/main/Bot_/img_doc/"

# Dicionário de temas para fácil alternância
THEMES = {
    'light': {
        "bg": "#f7f8fa", "panel": "#ffffff", "accent": "#2563eb", "accent2": "#10b981",
        "danger": "#ff0000", "warn": "#ffa200", "text": "#000000", "muted": "#64748b",
        "border": "#e5e7eb", "list_sel": "#dbeafe", "code_bg": "#f0f1f3"
    },
    'dark': {
        "bg": "#000000", "panel": "#000000", "accent": "#0073FF", "accent2": "#00FFA2",
        "danger": "#FF0000", "warn": "#FFB700", "text": "#FFFFFF", "muted": "#94A3B8",
        "border": "#FFFFFF", "list_sel": "#000000", "code_bg": "#000000"
    }
}