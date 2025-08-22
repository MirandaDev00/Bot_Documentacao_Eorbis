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
        "danger": "#ef4444", "warn": "#f59e0b", "text": "#0f172a", "muted": "#64748b",
        "border": "#e5e7eb", "list_sel": "#dbeafe", "code_bg": "#f0f1f3"
    },
    'dark': {
        "bg": "#0B1220", "panel": "#101826", "accent": "#60A5FA", "accent2": "#34D399",
        "danger": "#F87171", "warn": "#FBBF24", "text": "#E5E7EB", "muted": "#94A3B8",
        "border": "#1F2A3A", "list_sel": "#1f2937", "code_bg": "#141C2B"
    }
}