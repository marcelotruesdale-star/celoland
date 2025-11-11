from flask import Flask, request, jsonify
from flask_cors import CORS
import re
# Importe as bibliotecas necessárias para web scraping
import requests
from bs4 import BeautifulSoup

# 1. Configuração do Flask
app = Flask(__name__)
# Habilita CORS para permitir que o frontend (index.html) se comunique com o servidor
CORS(app) 

# Variáveis de Configuração (Substitua pelos seus dados reais para envio real)
TELEGRAM_BOT_TOKEN = "SEU_TOKEN_BOT_AQUI"
TELEGRAM_CHAT_ID = "-SEU_CHAT_ID_AQUI" # IDs de canais ou grupos costumam começar com '-'

# --- Funções de Simulação/Realização (Web Scraping e Telegram) ---

def buscar_info_produto_real(url):
    """
    Função REAL de busca de dados do produto, extraindo informações do link da Amazon.
    
    NOTA: Os seletores da Amazon podem mudar. Se o scraping falhar, os seletores
    dentro do bloco 'try' precisam ser atualizados.
    """
    
    # ----------------------------------------------------------------------
    # --- INÍCIO DA LÓGICA DE WEB SCRAPING REAL (MELHORADA) ---
    # ----------------------------------------------------------------------
    
    try:
        # Configurar headers para simular um navegador real (necessário para a Amazon)
        # O User-Agent foi atualizado para ser mais "comum"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br'
        }
        
        # Fazer a requisição HTTP
        response = requests.get(url, headers=headers, timeout=20) # Aumentado o timeout
        response.raise_for_status() # Lança exceção para erros HTTP (4xx ou 5xx)
        
        # Analisar o conteúdo HTML
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 1. Título - Tentando seletor mais genérico (e o original)
        titulo_elemento = soup.find(id='productTitle')
        if not titulo_elemento:
             titulo_elemento = soup.find('span', id='productTitle')
             
        titulo = titulo_elemento.text.strip() if titulo_elemento else None
        
        # 2. Preço Atual - Buscando em todos os elementos 'a-offscreen' e filtrando o primeiro
        preco_atual = None
        
        # Tenta 1: Encontrar o preço principal dentro de 'a-offscreen' (local mais comum para o preço)
        price_offscreen = soup.find('span', class_='a-offscreen')

        if price_offscreen:
            preco_atual = price_offscreen.text.strip()
        else:
            # Tenta 2: Encontrar no price block principal
            price_main_block = soup.find(id='priceblock_ourprice') 
            if price_main_block:
                preco_atual = price_main_block.text.strip()
            
            # Tenta 3: Encontrar na classe de preço mais comum 'priceToPay'
            if not preco_atual:
                price_to_pay = soup.find('span', class_='priceToPay')
                if price_to_pay:
                    price_offscreen_fallback = price_to_pay.find('span', class_='a-offscreen')
                    if price_offscreen_fallback:
                        preco_atual = price_offscreen_fallback.text.strip()
            
            # Tenta 4: Montar o valor a partir dos elementos de preço (inteiro e decimal)
            if not preco_atual:
                preco_atual_elemento = soup.find(class_='a-price-whole') 
                if preco_atual_elemento:
                    centavos_elemento = soup.find(class_='a-price-fraction')
                    simbolo_elemento = soup.find(class_='a-price-symbol')
                    
                    preco_atual_str = ""
                    if simbolo_elemento:
                        preco_atual_str += simbolo_elemento.text.strip() + " "
                    if preco_atual_elemento:
                        preco_atual_str += preco_atual_elemento.text.strip()
                    if centavos_elemento:
                        preco_atual_str += "," + centavos_elemento.text.strip()
                    
                    preco_atual = preco_atual_str if preco_atual_str.strip() != "" else None


        # 3. Preço Antigo (Geralmente marcado com riscado na classe 'a-text-strike')
        preco_antigo_elemento = soup.find('span', class_='a-text-strike')
        preco_antigo = preco_antigo_elemento.text.strip() if preco_antigo_elemento else None

        
        # Verifica se os dados essenciais foram encontrados e parecem válidos
        # Deve ter título E o preço deve conter "R$" ou ser um valor numérico (para garantir que não seja texto vazio)
        if titulo and preco_atual and (preco_atual.startswith('R$') or any(char.isdigit() for char in preco_atual)):
            print(f"SCRAPING SUCESSO: Título: {titulo}, Preço: {preco_atual}")
            return {
                "sucesso": True,
                "titulo": titulo,
                "preco_atual": preco_atual,
                "preco_antigo": preco_antigo
            }
        
        # Se chegou aqui, os dados não foram encontrados ou estão em formato inesperado
        raise Exception("Dados essenciais não encontrados na página (Scraping falhou).")
            
    except Exception as e:
        print(f"Erro durante o scraping (voltando para a simulação): {e}")
        
    # ----------------------------------------------------------------------
    # --- FIM DA LÓGICA DE WEB SCRAPING REAL (início da SIMULAÇÃO/FALLBACK) ---
    # ----------------------------------------------------------------------

    # Tenta encontrar o ASIN (código do produto) na URL para simular diferentes respostas
    asin_match = re.search(r'/[A-Z0-9]{10}(/|$|\?)', url)
    
    if not asin_match:
        print("SIMULAÇÃO: ASIN não encontrado. Retornando falha.")
        return {
            "sucesso": False,
            "titulo": "Título não encontrado via Scraping ou Simulação.",
            "preco_atual": None,
            "preco_antigo": None
        }

    # Se o scraping falhou (caiu no 'except' ou não encontrou os seletores),
    # ele usa a lógica de simulação/mock (os dados fixos) como um FALLBACK para testar.
    print("SIMULAÇÃO: Retornando dados mockados como fallback.")
    return {
        "sucesso": True,
        "titulo": f"PRODUTO MOCKADO (Link: {url[:30]}...)",
        "preco_atual": "R$ 349,99",
        "preco_antigo": "R$ 499,90"
    }

def enviar_mensagem_telegram(mensagem, link_afiliado):
    """
    Tenta enviar a mensagem para o Telegram usando a API real.
    Verifique se TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID estão configurados.
    """
    
    # 1. Checagem de Configuração (Se não estiver configurado, entra em modo de simulação)
    if TELEGRAM_BOT_TOKEN == "SEU_TOKEN_BOT_AQUI" or TELEGRAM_CHAT_ID == "-SEU_CHAT_ID_AQUI":
        print("\n--- AVISO: MODO DE SIMULAÇÃO ATIVADO ---")
        print("Preencha TELEGRAM_BOT_TOKEN e TELEGRAM_CHAT_ID para envio REAL.")
        print("Link de Afiliado (Final):", link_afiliado)
        print("Conteúdo da Mensagem:\n", mensagem)
        print("---------------------------------------\n")
        return True # Retorna True para não falhar o frontend no modo de simulação

    # 2. Envio REAL para o Telegram
    telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": mensagem,
        "parse_mode": "Markdown" # Usa Markdown para negritos, itálicos, etc.
    }
    
    print("\n--- TENTATIVA DE ENVIO REAL AO TELEGRAM ---")
    print(f"Chat ID: {TELEGRAM_CHAT_ID}")
    
    try:
        response = requests.post(telegram_api_url, data=payload)
        response.raise_for_status() # Lança erro para status 4xx/5xx
        
        resultado = response.json()
        if resultado.get('ok'):
            print("ENVIO SUCESSO. Verifique o Telegram.")
            return True
        else:
            print(f"FALHA NO ENVIO: {resultado.get('description', 'Erro desconhecido da API.')}")
            return False
            
    except requests.exceptions.HTTPError as e:
        print(f"ERRO HTTP ao enviar ao Telegram: {e.response.text}")
        return False
    except Exception as e:
        print(f"ERRO GERAL ao enviar ao Telegram: {e}")
        return False


# --- Endpoints da API ---

@app.route('/api/teste-conexao', methods=['GET'])
def teste_conexao():
    """Endpoint para verificar se o servidor está rodando."""
    return jsonify({"ok": True, "mensagem": "Conexão Flask OK!"})

@app.route('/api/buscar-produto', methods=['POST'])
def buscar_produto():
    """Endpoint para buscar informações do produto dado um link da Amazon."""
    data = request.get_json()
    link = data.get('url')
    
    if not link:
        return jsonify({"sucesso": False, "erro": "Link da Amazon é obrigatório"}), 400

    # Chamada à função de busca REAL/SIMULADA
    resultado = buscar_info_produto_real(link)
    
    return jsonify(resultado)

@app.route('/api/enviar-telegram', methods=['POST'])
def enviar_telegram():
    """Endpoint para formatar a mensagem e simular o envio ao Telegram."""
    dados = request.get_json()
    
    # 1. Validar dados
    nome = dados.get('nome')
    link_original = dados.get('link')
    tag_afiliado = dados.get('tag_afiliado')
    
    if not all([nome, link_original, tag_afiliado]):
        return jsonify({"sucesso": False, "erro": "Nome, Link e Tag são obrigatórios"}), 400

    # 2. Construir o Link de Afiliado (Lógica Crítica)
    # A maneira mais segura de adicionar a tag é substituir qualquer tag existente ou adicionar
    # no final se for um link "limpo" (sem query parameters).
    link_afiliado = link_original
    tag_param = f"tag={tag_afiliado}"
    
    # Remove qualquer tag existente (ex: tag=velha-20)
    link_afiliado = re.sub(r'([?&])tag=[^&]*', r'\1', link_afiliado)

    # Adiciona a nova tag
    if '?' in link_afiliado:
        # Se já tem query params, adiciona com '&'
        if not link_afiliado.endswith(('?', '&')):
             link_afiliado += '&'
        link_afiliado += tag_param
    else:
        # Se não tem, adiciona com '?'
        link_afiliado += '?' + tag_param
        
    # Limpa possíveis duplos '?' ou '&'
    link_afiliado = link_afiliado.replace('?&', '?').replace('&&', '&')
    

    # 3. Formatar a Mensagem do Telegram
    mensagem = f"🚨 *OFERTA EXCLUSIVA* 🚨\n\n"
    mensagem += f"🎁 *{nome}*\n\n"
    
    if dados.get('preco_de'):
        mensagem += f"❌ DE: ~{dados['preco_de']}~\n" # Usando ~ para riscar (strikethrough) em Markdown
    if dados.get('preco_por'):
        mensagem += f"🔥 POR: *{dados['preco_por']}*\n" # Usando * para negrito em Markdown
        
    if dados.get('cupom'):
        mensagem += f"\n🏷️ *Cupom*: `{dados['cupom']}`\n" # Usando ` para código
        
    if dados.get('descricao'):
        mensagem += f"\n📝 _{dados['descricao']}_\n" # Usando _ para itálico
        
    mensagem += f"\n🔗 [Link para Amazon]({link_afiliado})" # Link formatado para o Telegram
    
    # 4. Tentar Envio REAL
    if enviar_mensagem_telegram(mensagem, link_afiliado):
        return jsonify({"sucesso": True, "mensagem": "Mensagem enviada com sucesso! Verifique seu Telegram."})
    else:
        return jsonify({"sucesso": False, "erro": "Falha no envio para o Telegram. Verifique seu Token e Chat ID."}), 500

# 5. Inicialização do Servidor
if __name__ == '__main__':
    print("Servidor Flask inicializado. Acesse http://127.0.0.1:5000/")
    # Garante que o servidor seja acessível externamente (necessário para alguns ambientes)
    app.run(debug=True, host='0.0.0.0')
