from flask import Flask, request, jsonify
from flask_cors import CORS
import re
# Importe as bibliotecas necessárias para web scraping aqui
# Exemplo:
# import requests
# from bs4 import BeautifulSoup
# from decimal import Decimal # Para lidar com preços de forma segura

# 1. Configuração do Flask
app = Flask(__name__)
# Habilita CORS para permitir que o frontend (index.html) se comunique com o servidor
CORS(app) 

# Variáveis de Configuração (Substitua pelos seus dados reais no ambiente de produção)
TELEGRAM_BOT_TOKEN = "SEU_TOKEN_BOT_AQUI"
TELEGRAM_CHAT_ID = "-SEU_CHAT_ID_AQUI" # IDs de canais ou grupos costumam começar com '-'

# --- Funções de Simulação/Realização (Web Scraping e Telegram) ---

def buscar_info_produto_real(url):
    """
    Função REAL de busca de dados do produto.
    
    ESTE É O BLOCO QUE VOCÊ PRECISA MUDAR para extrair os dados da Amazon.
    """
    
    # ----------------------------------------------------------------------
    # --- INÍCIO DA LÓGICA DE WEB SCRAPING REAL ---
    # ----------------------------------------------------------------------
    
    # Exemplo de lógica de extração (substitua pelo seu código real):
    # try:
    #     # 1. Configurar headers para parecer um navegador (necessário para Amazon)
    #     headers = {
    #         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    #     }
    #     
    #     # 2. Fazer a requisição HTTP
    #     response = requests.get(url, headers=headers, timeout=10)
    #     response.raise_for_status() # Lança erro para status HTTP ruins (4xx ou 5xx)
    #     
    #     # 3. Analisar o conteúdo HTML
    #     soup = BeautifulSoup(response.content, 'html.parser')
    #     
    #     # 4. Encontrar os elementos e extrair o texto
    #     # ESTES SELECTORES SÃO EXEMPLOS E PODEM MUDAR NA AMAZON!
    #     titulo_elemento = soup.find(id='productTitle')
    #     preco_atual_elemento = soup.find('span', class_='a-price-whole') # Exemplo de selector de preço
    #     
    #     titulo = titulo_elemento.text.strip() if titulo_elemento else None
    #     
    #     # Precisa de lógica complexa para extrair e formatar o preço corretamente
    #     preco_atual = f"R$ {preco_atual_elemento.text.strip()}" if preco_atual_elemento else None
    #     
    #     if titulo and preco_atual:
    #         return {
    #             "sucesso": True,
    #             "titulo": titulo,
    #             "preco_atual": preco_atual,
    #             "preco_antigo": None # A lógica para preço 'de' é geralmente mais difícil de extrair
    #         }
    #     
    # except Exception as e:
    #     print(f"Erro durante o scraping: {e}")
    #     pass # Segue para a simulação se o scraping falhar
        
    # ----------------------------------------------------------------------
    # --- FIM DA LÓGICA DE WEB SCRAPING REAL (início da SIMULAÇÃO) ---
    # ----------------------------------------------------------------------

    # Tenta encontrar o ASIN (código do produto) na URL para simular diferentes respostas
    asin_match = re.search(r'/[A-Z0-9]{10}(/|$|\?)', url)
    
    if not asin_match:
        print("SIMULAÇÃO: ASIN não encontrado. Retornando falha.")
        return {
            "sucesso": False,
            "titulo": None,
            "preco_atual": None,
            "preco_antigo": None
        }

    # ASIN encontrado, retorna dados mockados de sucesso
    print("SIMULAÇÃO: Retornando dados mockados com sucesso.")
    return {
        "sucesso": True,
        "titulo": "Fone de Ouvido Bluetooth Premium com Cancelamento de Ruído (SIMULADO)",
        "preco_atual": "R$ 349,99",
        "preco_antigo": "R$ 499,90"
    }

def enviar_mensagem_telegram_simulado(mensagem, link_afiliado):
    """
    SIMULA o envio da mensagem para o Telegram.
    Em um ambiente real, você faria uma requisição POST para a API do Telegram.
    """
    print("\n--- SIMULAÇÃO DE ENVIO AO TELEGRAM ---")
    print(f"Link de Afiliado (Final): {link_afiliado}")
    print("\nConteúdo da Mensagem:")
    print(mensagem)
    print("---------------------------------------\n")
    
    # Se você quiser integrar de verdade, o código seria algo assim:
    # telegram_api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    # payload = {
    #     "chat_id": TELEGRAM_CHAT_ID,
    #     "text": mensagem,
    #     "parse_mode": "Markdown" # ou "HTML", dependendo do formato da sua mensagem
    # }
    # try:
    #     response = requests.post(telegram_api_url, data=payload)
    #     response.raise_for_status()
    #     return response.json().get('ok', False)
    # except Exception as e:
    #     print(f"Erro ao enviar ao Telegram: {e}")
    #     return False

    # Retorna sucesso na simulação
    return True

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
    mensagem = f"🚨 OFERTA EXCLUSIVA 🚨\n\n"
    mensagem += f"🎁 {nome}\n\n"
    
    if dados.get('preco_de'):
        mensagem += f"❌ DE: {dados['preco_de']}\n"
    if dados.get('preco_por'):
        mensagem += f"🔥 POR: {dados['preco_por']}\n"
        
    if dados.get('cupom'):
        mensagem += f"\n🏷️ Cupom: {dados['cupom']}\n"
        
    if dados.get('descricao'):
        mensagem += f"\n📝 {dados['descricao']}\n"
        
    mensagem += f"\n🔗 {link_afiliado}" # Adiciona o link de afiliado no final da mensagem
    
    # 4. Simular Envio
    if enviar_mensagem_telegram_simulado(mensagem, link_afiliado):
        return jsonify({"sucesso": True, "mensagem": "Mensagem enviada com sucesso para o Telegram (Simulação)"})
    else:
        return jsonify({"sucesso": False, "erro": "Falha na simulação de envio ao Telegram"}), 500

# 5. Inicialização do Servidor
if __name__ == '__main__':
    print("Servidor Flask inicializado. Acesse http://127.0.0.1:5000/")
    # Garante que o servidor seja acessível externamente (necessário para alguns ambientes)
    app.run(debug=True, host='0.0.0.0')
