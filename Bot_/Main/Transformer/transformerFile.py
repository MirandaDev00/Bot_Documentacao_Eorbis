# Main/Transformer/transformerFile.py

import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

# As URLs e diretórios agora são importados do config.py
# Os arquivos Logs/ e Results/ serão gerenciados pela main.py

def obter_versao(url, log_file):
    """Tenta obter a versão de uma URL ou retorna uma fallback."""
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        div = soup.find("div", class_="softgray")
        if div and "Versão:" in div.text:
            versao = div.text.strip().split("Versão:")[-1].strip()
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(versao)
            return versao
    except requests.RequestException as e:
        print(f"[WARN] Falha de conexão ao obter versão: {e}")
    except Exception as e:
        print(f"[WARN] Erro ao extrair a versão do HTML: {e}")
    
    # Versão fallback
    return "1.0.0"


def transformar_html(html_content, versao, img_padrao_eorbis, img_padrao_metaprime):
    """
    Transforma o conteúdo HTML bruto, aplicando estilos e estrutura.
    Retorna o conteúdo HTML transformado.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Garante as tags <html>, <head> e <body>
    if not soup.html:
        html_tag = soup.new_tag("html")
        for el in list(soup.contents):
            html_tag.append(el.extract())
        soup.append(html_tag)

    if not soup.head:
        head_tag = soup.new_tag("head")
        head_tag.append(soup.new_tag("meta", charset="UTF-8"))
        soup.html.insert(0, head_tag)
    
    if not soup.body:
        body_tag = soup.new_tag("body")
        # Move todo o conteúdo para dentro do <body>, exceto o <head>
        for el in list(soup.html.contents):
            if el.name and el.name.lower() != "head":
                body_tag.append(el.extract())
        soup.html.append(body_tag)

    # Adiciona cabeçalho com logo e versão
    header_div = soup.new_tag("div", style="border-bottom: 2px solid #ccc; padding-bottom: 10px; margin-bottom: 20px;")
    
    logo_eorbis_tag = soup.new_tag("img", src=img_padrao_eorbis, alt="Logo E-Orbis", 
                                  style="max-width:200px; display:block; margin:10px 0;")
    header_div.append(logo_eorbis_tag)

    versao_tag = soup.new_tag("p", style="font-size:12pt; text-align:left; margin:10px 0;")
    versao_tag.string = f"Versão: {versao} | Última atualização: {datetime.today().strftime('%d/%m/%Y')}"
    header_div.append(versao_tag)

    soup.body.insert(0, header_div)

    # Aplica estilos aos elementos
    style_map = {
        "h1": "font-size:20pt; font-weight:bold; text-align:center;",
        "h2": "font-size:18pt; font-weight:bold; text-align:left; margin-top:20px;",
        "h3": "font-size:16pt; font-weight:bold; text-align:left; margin-top:15px;",
    }
    for tag, style in style_map.items():
        for el in soup.find_all(tag):
            el["style"] = style

    # Estilo para blocos de atenção (OBS)
    for p in soup.find_all("p"):
        if p.text.strip().startswith(("OBS:", "⚠️ OBS:")):
            p["style"] = "font-size:16pt; text-align:center; margin:20px 0; border: 1px solid #ffcc00; padding: 10px;"
            p.insert_before(soup.new_tag("hr"))
            p.insert_after(soup.new_tag("hr"))

    # Imagens centralizadas, exceto logos
    for img in soup.find_all("img"):
        if "Logo E-Orbis" not in img.get("alt", "") and "Logo Meta Prime" not in img.get("alt", ""):
            img["style"] = "display:block; margin:20px auto; max-width:1200px;"

    # Destaque para textos em strong com parênteses
    for strong in soup.find_all("strong"):
        if "(" in strong.text and ")" in strong.text:
            strong["style"] = "font-weight:bold; color:#2563eb;" # Exemplo de cor

    # Adiciona o footer com o logo MetaPrime
    footer_tag = soup.new_tag("footer", style="border-top: 2px solid #ccc; padding-top: 10px; margin-top: 20px; text-align: right;")
    img_metaprime = soup.new_tag("img", src=img_padrao_metaprime, alt="Logo Meta Prime", 
                                style="max-width:200px; display:inline-block;")
    footer_tag.append(img_metaprime)
    soup.body.append(footer_tag)
    
    return str(soup)