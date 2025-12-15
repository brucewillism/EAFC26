"""
Módulo de Integração com Futbin - Busca preços e oportunidades de mercado
Com técnicas anti-detecção para evitar bloqueios
"""

import requests
import time
import json
from urllib.parse import quote
import re
import urllib3
import random

# Desabilita warnings de SSL (necessário para alguns ambientes)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class FutbinIntegration:
    """Integração com Futbin para buscar preços e oportunidades de mercado"""
    
    def __init__(self, logger, cache_duration=300):
        """
        Inicializa integração com Futbin
        
        Args:
            logger: Logger para logs
            cache_duration: Duração do cache em segundos (padrão: 5 minutos)
        """
        self.logger = logger
        self.cache_duration = cache_duration
        self.cache = {}  # Cache de preços
        self.session = requests.Session()
        self.blocked = False  # Flag para indicar se Futbin está bloqueado
        self.blocked_count = 0  # Contador de bloqueios consecutivos
        self.last_request_time = 0  # Timestamp da última requisição
        self.request_count = 0  # Contador de requisições na sessão
        self.session_started = False  # Flag para indicar se sessão foi iniciada
        
        # Lista de User-Agents realistas (rotaciona entre eles)
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        ]
        
        # Inicializa headers com User-Agent aleatório
        self._update_headers()
        
        # Visita página inicial para estabelecer sessão
        self._establish_session()
    
    def _update_headers(self):
        """Atualiza headers com User-Agent aleatório e headers realistas"""
        user_agent = random.choice(self.user_agents)
        
        # Headers completos que simulam navegador real
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',  # Do Not Track
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Cache-Control': 'max-age=0',
        })
    
    def _establish_session(self):
        """Estabelece sessão visitando a página inicial do Futbin"""
        try:
            if self.session_started:
                return
            
            self.logger.debug("🌐 Estabelecendo sessão com Futbin...")
            
            # Visita página inicial para obter cookies
            response = self.session.get(
                'https://www.futbin.com/',
                timeout=15,
                verify=False,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                self.session_started = True
                self.logger.debug("✅ Sessão estabelecida com sucesso")
                
                # Aguarda um pouco para simular leitura da página
                time.sleep(random.uniform(1.0, 2.5))
            else:
                self.logger.warning(f"⚠️ Erro ao estabelecer sessão: Status {response.status_code}")
                
        except Exception as e:
            self.logger.debug(f"Erro ao estabelecer sessão: {e}")
    
    def _human_delay(self, min_seconds=2.0, max_seconds=5.0):
        """
        Delay aleatório que simula comportamento humano
        - Delays maiores entre requisições
        - Variação aleatória
        """
        delay = random.uniform(min_seconds, max_seconds)
        
        # Adiciona pequenas variações para parecer mais humano
        jitter = random.uniform(0.1, 0.5)
        delay += jitter
        
        time.sleep(delay)
    
    def _rate_limit_check(self):
        """
        Verifica e aplica rate limiting para evitar detecção
        - Máximo 1 requisição a cada 3-6 segundos
        - Pausa maior a cada 10 requisições
        """
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        # Delay mínimo entre requisições (3-6 segundos)
        min_delay = random.uniform(3.0, 6.0)
        
        if time_since_last < min_delay:
            wait_time = min_delay - time_since_last
            self.logger.debug(f"⏳ Rate limiting: aguardando {wait_time:.1f}s")
            time.sleep(wait_time)
        
        # A cada 10 requisições, pausa maior (simula pausa para "ler" resultados)
        self.request_count += 1
        if self.request_count % 10 == 0:
            pause_time = random.uniform(10.0, 20.0)
            self.logger.debug(f"☕ Pausa humana: {pause_time:.1f}s (após {self.request_count} requisições)")
            time.sleep(pause_time)
        
        self.last_request_time = time.time()
        
    def search_player(self, player_name, platform="pc"):
        """
        Busca jogador no Futbin
        
        Args:
            player_name: Nome do jogador
            platform: Plataforma (pc, xbox, ps)
            
        Returns:
            dict com informações do jogador ou None
        """
        # Se Futbin está bloqueado, não tenta buscar
        if self.blocked:
            return None
            
        try:
            # Verifica cache
            cache_key = f"{player_name}_{platform}"
            if cache_key in self.cache:
                cached_data, cached_time = self.cache[cache_key]
                if time.time() - cached_time < self.cache_duration:
                    self.logger.debug(f"Usando cache para {player_name}")
                    return cached_data
            
            # Estabelece sessão se necessário
            if not self.session_started:
                self._establish_session()
            
            # Aplica rate limiting
            self._rate_limit_check()
            
            # Atualiza referer para parecer navegação natural
            self.session.headers['Referer'] = 'https://www.futbin.com/'
            self.session.headers['Sec-Fetch-Site'] = 'same-origin'
            
            # Busca no Futbin
            search_url = f"https://www.futbin.com/search?year=26&term={quote(player_name)}"
            
            self.logger.info(f"Buscando {player_name} no Futbin...")
            
            # Delay humano antes da requisição
            self._human_delay(1.5, 3.0)
            
            response = self.session.get(search_url, timeout=15, verify=False, allow_redirects=True)
            
            if response.status_code == 403:
                self.blocked_count += 1
                if self.blocked_count >= 3:
                    self.blocked = True
                    self.logger.warning(f"🚫 Futbin bloqueou múltiplas requisições (403). Desabilitando Futbin temporariamente.")
                    self.logger.warning(f"💡 O bot continuará funcionando com análise de mercado local.")
                else:
                    self.logger.warning(f"⚠️ Futbin bloqueou requisição (403) para {player_name}. Tentativa {self.blocked_count}/3")
                time.sleep(2)  # Aguarda mais tempo antes de tentar novamente
                return None
            elif response.status_code == 200:
                # Se requisição foi bem-sucedida, reseta contador de bloqueios
                if self.blocked_count > 0:
                    self.blocked_count = 0
                    self.blocked = False
                    self.logger.info("✅ Futbin voltou a funcionar!")
                
                # Rotaciona User-Agent ocasionalmente (a cada 5 requisições)
                if self.request_count % 5 == 0:
                    self._update_headers()
                    self.logger.debug("🔄 User-Agent rotacionado")
            elif response.status_code != 200:
                self.logger.warning(f"Erro ao buscar {player_name}: Status {response.status_code}")
                return None
            
            # Tenta extrair dados da resposta
            # Futbin usa JavaScript para carregar dados, então precisamos fazer scraping diferente
            # Por enquanto, vamos usar a API pública se disponível
            
            # Alternativa: buscar via página do jogador
            player_data = self._search_player_page(player_name, platform)
            
            if player_data:
                # Salva no cache
                self.cache[cache_key] = (player_data, time.time())
            
            return player_data
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar jogador {player_name}: {e}")
            return None
    
    def _search_player_page(self, player_name, platform="pc"):
        """Busca dados do jogador na página do Futbin"""
        try:
            # Tenta encontrar o ID do jogador primeiro
            # Futbin usa URLs como: https://www.futbin.com/26/player/12345/player-name
            # Aplica rate limiting
            self._rate_limit_check()
            
            search_url = f"https://www.futbin.com/search?year=26&term={quote(player_name)}"
            
            # Delay humano
            self._human_delay(1.5, 3.0)
            
            response = self.session.get(search_url, timeout=15, verify=False, allow_redirects=True)
            if response.status_code == 403 or response.status_code != 200:
                return None
            
            # Procura por links de jogadores na resposta
            # Futbin retorna HTML com links para jogadores
            html = response.text
            
            # Procura padrão de link de jogador
            # Exemplo: /26/player/12345/player-name
            pattern = r'/26/player/(\d+)/[^"\']+'
            matches = re.findall(pattern, html)
            
            if not matches:
                # Tenta método alternativo: busca direta na API
                return self._get_player_price_api(player_name, platform)
            
            # Pega o primeiro resultado (jogador mais relevante)
            player_id = matches[0]
            
            # Busca preços na API do Futbin
            return self._get_player_price_by_id(player_id, platform)
            
        except Exception as e:
            self.logger.debug(f"Erro ao buscar página do jogador: {e}")
            return None
    
    def _get_player_price_by_id(self, player_id, platform="pc"):
        """Busca preço do jogador pelo ID na API do Futbin"""
        try:
            # API do Futbin para preços
            # Formato: https://www.futbin.com/26/playerPrices?player={player_id}
            # Aplica rate limiting
            self._rate_limit_check()
            
            api_url = f"https://www.futbin.com/26/playerPrices?player={player_id}"
            
            # Delay humano
            self._human_delay(1.5, 3.0)
            
            response = self.session.get(api_url, timeout=15, verify=False, allow_redirects=True)
            if response.status_code == 403 or response.status_code != 200:
                return None
            
            data = response.json()
            
            # Mapeia plataforma
            platform_map = {
                "pc": "PC",
                "xbox": "Xbox",
                "ps": "PS"
            }
            platform_key = platform_map.get(platform.lower(), "PC")
            
            if platform_key in data:
                prices = data[platform_key]
                return {
                    "player_id": player_id,
                    "name": prices.get("name", "Unknown"),
                    "price": prices.get("LCPrice", 0),  # Lowest Buy Now Price
                    "min_price": prices.get("min_price", 0),
                    "max_price": prices.get("max_price", 0),
                    "ps4": prices.get("PS4", {}).get("LCPrice", 0) if "PS4" in prices else 0,
                    "xbox": prices.get("Xbox", {}).get("LCPrice", 0) if "Xbox" in prices else 0,
                    "pc": prices.get("PC", {}).get("LCPrice", 0) if "PC" in prices else 0,
                    "updated": prices.get("updated", 0)
                }
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Erro ao buscar preço por ID: {e}")
            return None
    
    def _get_player_price_api(self, player_name, platform="pc"):
        """Método alternativo: busca preço via API de busca"""
        try:
            # Tenta usar a API de busca do Futbin
            # Nota: Futbin pode ter rate limiting, então usamos com cuidado
            
            # Por enquanto, retorna estrutura básica
            # Em produção, você precisaria fazer scraping mais sofisticado
            # ou usar uma API oficial se disponível
            
            return {
                "name": player_name,
                "price": 0,  # Não encontrado
                "platform": platform,
                "error": "API method not fully implemented"
            }
            
        except Exception as e:
            self.logger.debug(f"Erro na API alternativa: {e}")
            return None
    
    def find_undervalued_players(self, max_price=5000, min_rating=75, platform="pc", limit=20):
        """
        Busca jogadores baratos com potencial de valorização
        
        Estratégia: Foca em jogadores jovens, com boa avaliação e preço baixo
        que podem valorizar com o tempo ou eventos do jogo.
        
        Args:
            max_price: Preço máximo para considerar (padrão: 5000)
            min_rating: Avaliação mínima (padrão: 75)
            platform: Plataforma
            limit: Número máximo de jogadores
            
        Returns:
            list de jogadores subvalorizados
        """
        # Se Futbin está bloqueado, retorna lista vazia
        if self.blocked:
            return []
            
        try:
            self.logger.info(f"🔍 Buscando jogadores baratos com potencial (max: {max_price}, min rating: {min_rating})...")
            
            # Lista de jogadores jovens e promissores com potencial de valorização
            # Focando em jogadores baratos de ligas menores e jovens talentos
            undervalued_targets = [
                # Jovens talentos baratos (até 5000)
                "Evanilson", "David", "Isak", "Osimhen", "Vlahovic",
                "Gonçalo Ramos", "Hojlund", "Gakpo", "Kudus", "Olise",
                "Eze", "Palmer", "Garnacho", "Mainoo", "Branthwaite",
                "Gvardiol", "Scalvini", "Bastoni", "Todibo", "Disasi",
                "Caicedo", "Ugarte", "Bellingham", "Camavinga", "Tchouameni",
                "Pedri", "Gavi", "Wirtz", "Musiala", "Bellingham",
                "Saka", "Martinelli", "Foden", "Palmer", "Eze",
                "Leao", "Kvaratskhelia", "Vinicius Junior", "Rodrygo", "Endrick",
                
                # Jogadores de ligas menores com potencial
                "Kudus", "Osimhen", "Lookman", "Boniface", "Simon",
                "Doku", "Trossard", "Mitoma", "Kulusevski", "Johnson",
                
                # Defensores jovens baratos
                "Gvardiol", "Bastoni", "Todibo", "Disasi", "Scalvini",
                "Branthwaite", "Colwill", "Guehi", "Tomori", "Saliba",
                
                # Meio-campistas promissores
                "Caicedo", "Ugarte", "Lavia", "Onana", "Sangare",
                "Bellingham", "Camavinga", "Tchouameni", "Wirtz", "Musiala",
            ]
            
            opportunities = []
            
            for name in undervalued_targets:
                try:
                    # Delay já está no search_player, mas adiciona variação extra
                    # para parecer mais humano (algumas buscas mais rápidas, outras mais lentas)
                    if random.random() < 0.3:  # 30% das vezes, pausa extra
                        extra_delay = random.uniform(2.0, 4.0)
                        self.logger.debug(f"⏸️ Pausa extra: {extra_delay:.1f}s")
                        time.sleep(extra_delay)
                    
                    player = self.search_player(name, platform=platform)
                    if not player:
                        continue
                    
                    price = player.get("price", 0) or 0
                    if price <= 0:
                        continue
                    
                    # Foca apenas em jogadores baratos
                    if price > max_price:
                        continue
                    
                    # Calcula potencial de lucro
                    # Para jogadores baratos, objetivo é comprar 20-30% abaixo do preço Futbin
                    target_buy = int(price * 0.70)  # Comprar 30% abaixo
                    if target_buy < 150:  # Preço mínimo do jogo
                        target_buy = 150
                    
                    expected_profit = int(price * 0.95 - target_buy)  # Considera taxa de 5%
                    profit_pct = (expected_profit / target_buy * 100) if target_buy > 0 else 0
                    
                    # Só adiciona se o lucro for significativo
                    if expected_profit >= 200 and profit_pct >= 15:
                        opportunities.append({
                            "player_name": player.get("name", name),
                            "player_id": player.get("player_id"),
                            "futbin_price": price,
                            "target_buy_price": target_buy,
                            "profit": expected_profit,
                            "profit_percentage": round(profit_pct, 2),
                            "platform": platform,
                            "strategy": "undervalued"  # Marca como estratégia de subvalorizados
                        })
                        
                        if len(opportunities) >= limit:
                            break
                            
                except Exception as e:
                    self.logger.debug(f"Erro ao buscar {name}: {e}")
                    continue
            
            # Ordena por % de lucro (maior primeiro)
            opportunities.sort(key=lambda x: x["profit_percentage"], reverse=True)
            
            self.logger.info(f"✅ Encontrados {len(opportunities)} jogadores baratos com potencial")
            return opportunities
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar jogadores subvalorizados: {e}")
            return []
    
    def get_market_opportunities(self, min_profit=500, max_price=10000,
                                 min_profit_percentage=10.0, platform="pc",
                                 targets=None, limit=10, strategy="undervalued"):
        """
        Busca oportunidades de mercado no Futbin
        
        Args:
            min_profit: Lucro mínimo esperado
            max_price: Preço máximo para compra
            min_profit_percentage: % mínima de lucro
            platform: plataforma (pc, xbox, ps)
            targets: lista de nomes de jogadores para monitorar (opcional)
            limit: Número máximo de oportunidades
            strategy: "undervalued" (jogadores baratos) ou "targets" (jogadores específicos)
            
        Returns:
            list de oportunidades
        """
        try:
            # Se estratégia for "undervalued", busca jogadores baratos
            if strategy == "undervalued" or not targets:
                return self.find_undervalued_players(
                    max_price=max_price,
                    min_rating=75,
                    platform=platform,
                    limit=limit
                )
            
            # Estratégia antiga: busca jogadores específicos
            opportunities = []

            for name in targets:
                player = self.search_player(name, platform=platform)
                if not player:
                    continue

                price = player.get("price", 0) or 0
                if price <= 0 or price > max_price:
                    continue

                # Define um alvo de compra abaixo do preço Futbin para garantir lucro
                target_buy = price - min_profit
                profit_pct = (min_profit / price * 100) if price else 0

                if min_profit_percentage and profit_pct < min_profit_percentage:
                    # Ajusta alvo para cumprir % de lucro
                    target_buy = price * (1 - min_profit_percentage / 100)
                    profit_pct = min_profit_percentage

                expected_profit = price - target_buy
                if expected_profit < min_profit:
                    continue

                opportunities.append({
                    "player_name": player.get("name", name),
                    "player_id": player.get("player_id"),
                    "futbin_price": price,
                    "target_buy_price": max(150, int(target_buy)),
                    "profit": int(expected_profit),
                    "profit_percentage": round(profit_pct, 2),
                    "platform": platform,
                    "strategy": "targets"
                })

                if len(opportunities) >= limit:
                    break

            return opportunities
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar oportunidades: {e}")
            return []
    
    def analyze_trade_opportunity(self, player_name, market_price, platform="pc"):
        """
        Analisa se uma oportunidade de trade é lucrativa
        
        Args:
            player_name: Nome do jogador
            market_price: Preço no mercado do jogo
            platform: Plataforma
            
        Returns:
            dict com análise da oportunidade
        """
        try:
            # Busca preço no Futbin
            futbin_data = self.search_player(player_name, platform)
            
            if not futbin_data or futbin_data.get("price", 0) == 0:
                return {
                    "profitable": False,
                    "reason": "Jogador não encontrado no Futbin ou sem preço",
                    "market_price": market_price,
                    "futbin_price": 0,
                    "profit": 0
                }
            
            futbin_price = futbin_data.get("price", 0)
            
            # Calcula lucro potencial
            # Considera taxa de 5% do EA
            tax_rate = 0.05
            sell_price_after_tax = futbin_price * (1 - tax_rate)
            profit = sell_price_after_tax - market_price
            profit_percentage = (profit / market_price * 100) if market_price > 0 else 0
            
            return {
                "profitable": profit > 0,
                "market_price": market_price,
                "futbin_price": futbin_price,
                "sell_price_after_tax": sell_price_after_tax,
                "profit": profit,
                "profit_percentage": profit_percentage,
                "player_data": futbin_data
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar oportunidade: {e}")
            return {
                "profitable": False,
                "reason": f"Erro na análise: {e}",
                "market_price": market_price,
                "futbin_price": 0,
                "profit": 0
            }
    
    def get_price_history(self, player_name, days=7, platform="pc"):
        """
        Busca histórico de preços do jogador
        
        Args:
            player_name: Nome do jogador
            days: Número de dias de histórico
            platform: Plataforma
            
        Returns:
            list com histórico de preços
        """
        try:
            # Busca dados do jogador
            player_data = self.search_player(player_name, platform)
            
            if not player_data or "player_id" not in player_data:
                return []
            
            player_id = player_data["player_id"]
            
            # Busca histórico na API do Futbin
            # API: https://www.futbin.com/26/playerGraph?type=graph&player={player_id}&days={days}
            api_url = f"https://www.futbin.com/26/playerGraph?type=graph&player={player_id}&days={days}"
            
            response = self.session.get(api_url, timeout=10, verify=False)
            if response.status_code != 200:
                return []
            
            data = response.json()
            
            # Processa dados do gráfico
            history = []
            if "data" in data:
                for point in data["data"]:
                    history.append({
                        "date": point.get("date", ""),
                        "price": point.get("price", 0),
                        "platform": platform
                    })
            
            return history
            
        except Exception as e:
            self.logger.debug(f"Erro ao buscar histórico: {e}")
            return []
    
    def clear_cache(self):
        """Limpa o cache de preços"""
        self.cache.clear()
        self.logger.info("Cache do Futbin limpo")
    
    def get_cache_stats(self):
        """Retorna estatísticas do cache"""
        return {
            "cached_players": len(self.cache),
            "cache_duration": self.cache_duration
        }

