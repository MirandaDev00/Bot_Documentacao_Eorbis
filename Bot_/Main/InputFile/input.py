import markdown2
import os
import re

arquivo = "C:/Users/User/Desktop/Arquivos/Miranda/01 - Documentação/Doc/arquivosmd/1.7.2.1 Caixa.md"
arquivo_saida = "saida.html"

URL_BASE = "https://raw.githubusercontent.com/MirandaDev00/Doc-eobirs/main/img_doc/"

def my_link_handler(match):
    texto, url = match.group(1), match.group(2)
    obsidian_match = re.match(r'!\[\[(.*?)\]\]', texto)
    if obsidian_match:
        nome_imagem = obsidian_match.group(1)
        return f'<img src="{URL_BASE}{nome_imagem}" alt="{nome_imagem}">'
    return f'<a href="{url}">{texto}</a>'

html = markdown2.markdown_path(
    arquivo,
    extras=["tables", "fenced-code-blocks", "cuddled-lists","metadata"]
)

html = re.sub(r'!\[\[(.*?)\]\]', lambda m: f'<img src="{URL_BASE}{m.group(1)}" alt="{m.group(1)}">', html)

with open(arquivo_saida, 'w', encoding='utf-8') as f:
    f.write(html)
