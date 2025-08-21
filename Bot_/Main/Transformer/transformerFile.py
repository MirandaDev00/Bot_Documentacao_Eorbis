import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

input_dir = "Results/output_md/"
output_dir = "Results/output_transformer/"
versao_url = "http://192.168.99.183:8585/eorbis/"
versao_fallback = "1.0.0"
log_versao_file = "Logs/versao.txt"
img_padrao_eorbis = "https://raw.githubusercontent.com/MirandaDev00/Bot_Documentacao_Eorbis/main/Bot_/Assets/Logo%20eorbis.png"
img_padrao_metaprime = "https://raw.githubusercontent.com/MirandaDev00/Bot_Documentacao_Eorbis/main/Bot_/Assets/Logo%20metaprime.png"

os.makedirs(output_dir, exist_ok=True)

def obter_versao(url):
    try:
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        div = soup.find("div", class_="softgray")
        if div and "Versão:" in div.text:
            versao = div.text.strip().split("Versão:")[-1].strip()
            with open(log_versao_file, "w", encoding="utf-8") as f:
                f.write(versao)
            return versao
    except Exception as e:
        print(f"[WARN] Não foi possível obter versão do E-Orbis: {e}")
    return versao_fallback

def transformar_html(arquivo_entrada, arquivo_saida, versao):
    with open(arquivo_entrada, "r", encoding="utf-8") as f:
        conteudo = f.read()

    soup = BeautifulSoup(conteudo, "html.parser")

    if not soup.html:
        html_tag = soup.new_tag("html")
        for el in list(soup.contents):
            html_tag.append(el.extract())
        soup.append(html_tag)

    if not soup.head:
        head_tag = soup.new_tag("head")
        head_tag.append(soup.new_tag("meta", charset="UTF-8"))
        logo_tag = soup.new_tag("img", src=img_padrao_eorbis, alt="Logo E-Orbis")
        logo_tag["style"] = "max-width:200px; display:block; margin:10px 0;"
        head_tag.append(logo_tag)

        versao_tag = soup.new_tag("p")
        versao_tag.string = f"Versão: {versao} | Última atualização: {datetime.today().strftime('%d/%m/%Y')}"
        versao_tag["style"] = "font-size:12pt; text-align:left; margin:10px 0;"
        head_tag.append(versao_tag)

        soup.html.insert(0, head_tag)

    if not soup.body:
        body_tag = soup.new_tag("body")
        for el in list(soup.html.contents):
            if el.name != "head":
                body_tag.append(el.extract())
        soup.html.append(body_tag)

    # Estilizar título principal
    titulo = soup.body.find("h1")
    if titulo:
        titulo["style"] = "font-size:20pt; font-weight:bold; text-align:center;"

    # Estilizar resumo logo após título
    if titulo:
        resumo = titulo.find_next("p")
        if resumo:
            resumo["style"] = "font-size:16pt; text-align:left; margin:20px 0;"
            resumo.insert_before(soup.new_tag("hr"))
            resumo.insert_after(soup.new_tag("hr"))

    # Estilos para subtítulos
    for h2 in soup.body.find_all("h2"):
        h2["style"] = "font-size:18pt; font-weight:bold; text-align:left; margin-top:20px;"
    for h3 in soup.body.find_all("h3"):
        h3["style"] = "font-size:16pt; font-weight:bold; text-align:left; margin-top:15px;"

    # Estilo para blocos de atenção
    for p in soup.body.find_all("p"):
        if p.text.strip().startswith(("OBS:", "⚠️ OBS:")):
            p["style"] = "font-size:16pt; text-align:center; margin:20px 0;"
            p.insert_before(soup.new_tag("hr"))
            p.insert_after(soup.new_tag("hr"))

    # Imagens centralizadas, exceto logos
    for img in soup.body.find_all("img"):
        if "Logo E-Orbis" not in img.get("alt", "") and "Logo Meta Prime" not in img.get("alt", ""):
            img["style"] = "display:block; margin:20px auto; max-width:1200px;"

    # Destaque para textos em strong com parênteses
    for strong in soup.body.find_all("strong"):
        if "(" in strong.text and ")" in strong.text:
            strong["style"] = "font-weight:bold;"

    # Logo MetaPrime
    footer_tag = soup.new_tag("footer")
    img_metaprime = soup.new_tag("img", src=img_padrao_metaprime, alt="Logo Meta Prime")
    img_metaprime["style"] = "max-width:200px; float:right; margin:20px 0; display:block;"
    footer_tag.append(img_metaprime)
    soup.body.append(footer_tag)

    with open(arquivo_saida, "w", encoding="utf-8") as f:
        f.write(str(soup))

    print(f"✅ Transformado: {arquivo_saida}")


if __name__ == "__main__":
    versao_atual = obter_versao(versao_url)

    for arquivo in os.listdir(input_dir):
        if arquivo.endswith(".html"):
            caminho_entrada = os.path.join(input_dir, arquivo)
            caminho_saida = os.path.join(output_dir, arquivo)
            transformar_html(caminho_entrada, caminho_saida, versao_atual)
