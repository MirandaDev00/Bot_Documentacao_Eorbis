import os
import requests
from bs4 import BeautifulSoup
from datetime import datetime

input_dir = "Results/output_md/"
output_dir = "Results/output_transformer/"
versao_url = "http://192.168.99.183:8585/eorbis/"
versao_fallback = "1.0.0"
log_versao_file = "Logs/versao.txt"
img_padrao_eorbis = "Bot_/Assets/logo eorbis.png"
img_padrao_metaprime = "Bot_/Assets/logo metaprime.png"


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

    cabecalho = soup.new_tag("p")
    cabecalho.string = f"Versão: {versao} | Última atualização: {datetime.today().strftime('%d/%m/%Y')}"
    cabecalho["style"] = "font-size:12pt; text-align:left;"
    if soup.body:
        soup.body.insert(0, cabecalho)
    else:
        soup.insert(0, cabecalho)


    titulo = soup.find("h1")
    if titulo:
        titulo["style"] = "font-size:20pt; font-weight:bold; text-align:center;"

    if titulo:
        resumo = titulo.find_next("p")
        if resumo:
            resumo["style"] = "font-size:16pt; text-align:left; margin:20px 0;"
            hr1 = soup.new_tag("hr")
            hr2 = soup.new_tag("hr")
            resumo.insert_before(hr1)
            resumo.insert_after(hr2)

    for h2 in soup.find_all("h2"):
        h2["style"] = "font-size:18pt; font-weight:bold; text-align:left; margin-top:20px;"

    for h3 in soup.find_all("h3"):
        h3["style"] = "font-size:16pt; font-weight:bold; text-align:left; margin-top:15px;"

    for p in soup.find_all("p"):
        if p.text.strip().startswith("Atenção:") or p.text.strip().startswith("⚠️ Atenção:"):
            p["style"] = "font-size:16pt; text-align:center; margin:20px 0;"
            hr1 = soup.new_tag("hr")
            hr2 = soup.new_tag("hr")
            p.insert_before(hr1)
            p.insert_after(hr2)

    for img in soup.find_all("img"):
        img["style"] = "display:block; margin:20px auto; max-width:1200px;"

    for strong in soup.find_all("strong"):
        if "(" in strong.text and ")" in strong.text:
            strong["style"] = "font-weight:bold;"

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
