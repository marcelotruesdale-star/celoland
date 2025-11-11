from flask import Flask, request, jsonify
from flask_cors import CORS
import requests
from bs4 import BeautifulSoup
import re
import time # Opcional, pode ser removido se não for usado para delay em loops

# As seguintes importações foram removidas por não usarem mais Selenium:
# from selenium import webdriver
# from selenium.webdriver.chrome.service import Service
# ... e todas as outras imports relacionadas ao selenium

app = Flask(__name__)
CORS(app)

# 🔑 Configurações do Telegram
# NOTA: Em produção, estas chaves devem ser lidas de Variáveis de Ambiente (muito mais seguro!)
TELEGRAM_BOT_TOKEN = "8361375328:AAFnhlEZubW18IhNEoTGfFO4l6MlQJEUkEk"
TELEGRAM_CHAT_ID = "-1003203872885"

# --- NOVO CORE DE SCRAPING (Sem Selenium) ---
def buscar_info_amazon_simples(url):
    """Busca informações do produto na Amazon usando apenas requests e BeautifulSoup."""
    
    # 🕵️ Simula um navegador real. CRUCIAL para não ser bloqueado imediatamente.
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    }
    
    try:
        # Tenta a requisição GET
        response = requests.get(url, headers=headers, timeout=10)
        
        # 🛑 Checa se a requisição foi bem-sucedida (código 200)
        if response.status_code != 200:
            # Se for 503 ou 403, geralmente significa bloqueio anti-bot.
            return {'erro': f"Falha ao acessar a URL. Código de resposta: {response.status_code}", 'sucesso': False}
            
        soup = BeautifulSoup(response.content, 'html.parser')

        # --- BUSCA O TÍTULO ---
        titulo = None
        title_tag = soup.find('span', {'id': 'productTitle'})
        if title_tag:
            titulo = title_tag.get_text().strip()
        
        # --- BUSCA O PREÇO ATUAL (a-offscreen é o mais confiável sem JS) ---
        preco_atual = None
        price_tag_offscreen = soup.find('span', {'class': 'a-offscreen'})
        if price_tag_offscreen and 'R$' in price_tag_offscreen.get_text():
            preco_atual = price_tag_offscreen.get_text().strip().replace('\xa0', ' ')
        
        # Tenta buscar o preço visível (menos confiável, mas vale a tentativa)
        if not preco_atual:
             price_tag_visible = soup.find('span', {'class': 'a-price-whole'})
             if price_tag_visible:
                 cents_tag = soup.find('span', {'class': 'a-price-fraction'})
                 if cents_tag:
                     preco_atual = f"R$ {price_tag_visible.get_text().strip()},{cents_tag.get_text().strip()}"


        # --- BUSCA O PREÇO ANTIGO (RISCADO) ---
        preco_antigo = None
        old_price_tag = soup.find('span', {'data-a-strike': 'true'})
        if not old_price_tag:
            old_price_tag = soup.find('span', {'class': 'a-text-price'})
            
        if old_price_tag:
            preco_text = old_price_tag.get_text().strip()
            # Usa Regex para garantir que só pega o valor R$ XX,XX
            preco_match = re.search(r'R\$?\s*(\d+[.,]\d+)', preco_text)
            if preco_match:
                preco_antigo = f"R$ {preco_match.group(1).replace('.', ',')}"


        # --- BUSCA A IMAGEM ---
        imagem = None
        img_tag = soup.find('img', {'id': 'landingImage'})
        # A URL da imagem pode estar em outro atributo (data-a-dynamic-image) ou tag dependendo do layout
        if img_tag and img_tag.get('src'):
            imagem = img_tag.get('src')
        
        return {
            'titulo': titulo,
            'preco_atual': preco_atual,
            'preco_antigo': preco_antigo,
            'imagem': imagem,
            'sucesso': titulo is not None
        }
        
    except requests.exceptions.RequestException as e:
        return {'erro': f"Erro de conexão (requests): {str(e)}", 'sucesso': False}
    except Exception as e:
        return {'erro': f"Erro inesperado no scraping: {str(e)}", 'sucesso': False}

# --- Funções Auxiliares (mantidas) ---

def extrair_asin(link):
    """Extrai o ASIN do link"""
    match = re.search(r'/dp/([A-Z0-9]{10})', link)
    return match.group(1) if match else None

def formatar_link_afiliado(link, tag_afiliado):
    """Formata o link com a tag de afiliado"""
    asin = extrair_asin(link)
    if not asin:
        return link
    
    dominio = 'amazon.com.br' if 'amazon.com.br' in link else 'amazon.com'
    return f"https://www.{dominio}/dp/{asin}?tag={tag_afiliado}"


# --- Endpoints da API ---

@app.route('/api/buscar-produto', methods=['GET', 'POST']) 
def buscar_produto():
    """Endpoint para buscar as informações usando requisição simples."""
    
    # Prioriza o 'url' dos parâmetros GET (para formulário do Google Sites)
    url = request.args.get('url', '')
    
    # Se não veio no GET e veio um POST (JSON), tenta o JSON
    if not url and request.method == 'POST' and request.json:
        url = request.json.get('url', '')
    
    if not url or 'amazon.com' not in url:
        return jsonify({'erro': 'URL inválida da Amazon. Certifique-se de que o campo do formulário é "name=url"', 'sucesso': False}), 400
    
    # Chama a função de scraping simplificada
    info = buscar_info_amazon_simples(url) 
    return jsonify(info)


@app.route('/api/enviar-telegram', methods=['POST'])
def enviar_telegram():
    """Envia a oferta para o Telegram"""
    data = request.json
    
    nome = data.get('nome', '')
    link = data.get('link', '')
    tag_afiliado = data.get('tag_afiliado', '')
    preco_de = data.get('preco_de', '')
    preco_por = data.get('preco_por', '')
    cupom = data.get('cupom', '')
    descricao = data.get('descricao', '')
    
    if not nome or not link:
        return jsonify({'erro': 'Nome e link são obrigatórios', 'sucesso': False}), 400
    
    # Formata o link com tag de afiliado
    link_final = formatar_link_afiliado(link, tag_afiliado)
    
    # Monta a mensagem
    mensagem = f"🚨 OFERTA EXCLUSIVA 🚨\n\n"
    mensagem += f"🎁 {nome}\n\n"
    
    if preco_de:
        mensagem += f"❌ DE: {preco_de}\n"
    if preco_por:
        mensagem += f"🔥 POR: {preco_por}\n"
    if cupom:
        mensagem += f"\n🏷️ Cupom: {cupom}\n"
    if descricao:
        mensagem += f"\n📝 {descricao}\n"
    
    mensagem += f"\n{link_final}"
    
    # Envia para o Telegram
    url_telegram = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': TELEGRAM_CHAT_ID,
        'text': mensagem,
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.post(url_telegram, json=payload)
        resultado = response.json()
        
        if resultado.get('ok'):
            return jsonify({'sucesso': True, 'mensagem': 'Enviado com sucesso!'})
        else:
            return jsonify({'erro': resultado.get('description', 'Erro desconhecido'), 'sucesso': False}), 500
            
    except Exception as e:
        return jsonify({'erro': str(e), 'sucesso': False}), 500

@app.route('/api/teste-conexao', methods=['GET'])
def teste_conexao():
    """Testa a conexão com o Telegram"""
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getMe"
    
    try:
        response = requests.get(url)
        return jsonify(response.json())
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    print("🚀 Servidor iniciado em http://localhost:5000")
    app.run(debug=True, port=5000)