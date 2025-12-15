"""
Módulo de Comfort Trade - Transferência de Coins via Controle de Conta
⚠️ ATENÇÃO: Este método envolve riscos de segurança e banimento!
"""

import time
import random
from bot.base_module import BaseModule
from bot.trading import TradingBot
from bot.squad_battles import SquadBattlesBot
from bot.appium_automation import EACompanionAutomation

class ComfortTrade(BaseModule):
    """
    Gerencia transferência de coins via Comfort Trade
    
    ⚠️ RISCOS:
    - Banimento do Mercado de Transferências
    - Reset de Coins
    - Banimento da Conta
    - Roubo de Credenciais (se não confiar no vendedor)
    """
    
    def __init__(self, config, controller, screen_capture, logger, anti_detection=None):
        super().__init__(config, controller, screen_capture, logger)
        self.anti_detection = anti_detection
        
        self.comfort_config = config.get("comfort_trade", {})
        self.enabled = self.comfort_config.get("enabled", False)
        
        # Configuração da conta de destino (cliente)
        self.client_account = self.comfort_config.get("client_account", {})
        self.client_email = self.client_account.get("email", "")
        self.client_password = self.client_account.get("password", "")
        self.client_backup_codes = self.client_account.get("backup_codes", [])
        
        # Método de transferência
        self.transfer_method = self.comfort_config.get("transfer_method", "market")  # "market" ou "farming"
        
        # Configurações de transferência
        self.target_coins = self.comfort_config.get("target_coins", 0)  # Quantidade de coins a transferir
        self.coins_per_transaction = self.comfort_config.get("coins_per_transaction", 50000)  # Máximo por transação
        self.transfer_delay_min = self.comfort_config.get("transfer_delay_min", 300)  # 5 minutos entre transferências
        self.transfer_delay_max = self.comfort_config.get("transfer_delay_max", 600)  # 10 minutos
        
        # Estatísticas
        self.stats = {
            "coins_transferred": 0,
            "transactions_completed": 0,
            "matches_played": 0,
            "cards_sold": 0,
            "errors": 0
        }
        
        # Inicializa módulos auxiliares
        self.trading_bot = None
        self.squad_battles_bot = None
        self.companion_app = None
        
        # Estado
        self.is_client_logged_in = False
        self.current_session_start = None
        self.running = True  # Flag para controlar execução
    
    def initialize(self):
        """Inicializa módulos auxiliares"""
        try:
            # Inicializa trading bot para transferências via mercado
            if self.transfer_method == "market":
                self.trading_bot = TradingBot(
                    self.config, 
                    self.controller, 
                    self.screen_capture, 
                    self.logger, 
                    self.anti_detection
                )
            
            # Inicializa squad battles para farmar coins
            if self.transfer_method == "farming":
                self.squad_battles_bot = SquadBattlesBot(
                    self.config,
                    self.controller,
                    self.screen_capture,
                    self.logger,
                    self.anti_detection
                )
            
            # Inicializa Companion App automation
            try:
                self.companion_app = EACompanionAutomation(self.logger)
            except Exception as e:
                self.logger.warning(f"Companion App não disponível: {e}")
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao inicializar Comfort Trade: {e}")
            return False
    
    def login_to_client_account(self):
        """
        Faz login na conta do cliente
        
        ⚠️ ATENÇÃO: Requer credenciais completas do cliente
        """
        try:
            if not self.client_email or not self.client_password:
                self.logger.error("❌ Credenciais do cliente não configuradas!")
                self.logger.error("💡 Configure 'comfort_trade.client_account.email' e 'password' no config.json")
                return False
            
            self.logger.warning("⚠️  ATENÇÃO: Fazendo login na conta do cliente...")
            self.logger.warning("⚠️  RISCO: Login de localização incomum pode ser detectado!")
            
            # Atualiza configuração de login temporariamente
            original_email = self.config.get("login", {}).get("email", "")
            original_password = self.config.get("login", {}).get("password", "")
            
            # Usa credenciais do cliente
            self.config["login"]["email"] = self.client_email
            self.config["login"]["password"] = self.client_password
            
            # Tenta login via Companion App (mais seguro que jogo)
            if self.companion_app:
                self.logger.info("🔐 Tentando login via Companion App...")
                if self.companion_app.connect():
                    if self.companion_app.login(self.client_email, self.client_password):
                        self.is_client_logged_in = True
                        self.logger.info("✅ Login via Companion App bem-sucedido!")
                        return True
            
            # Fallback: login via jogo (mais arriscado)
            self.logger.warning("⚠️  Usando login via jogo (mais arriscado)...")
            from bot.ea_login import EALogin
            ea_login = EALogin(self.config, self.controller, self.screen_capture, self.logger)
            
            if ea_login.login():
                self.is_client_logged_in = True
                self.logger.info("✅ Login via jogo bem-sucedido!")
                return True
            else:
                self.logger.error("❌ Falha no login")
                # Restaura credenciais originais
                self.config["login"]["email"] = original_email
                self.config["login"]["password"] = original_password
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao fazer login na conta do cliente: {e}")
            return False
    
    def transfer_coins_via_market(self, amount):
        """
        Transfere coins via Mercado de Transferências
        
        Método:
        1. Cliente lista jogador barato por preço alto
        2. Bot compra esse jogador
        3. Coins são transferidas (menos 5% de taxa)
        """
        try:
            if not self.is_client_logged_in:
                self.logger.error("❌ Não está logado na conta do cliente!")
                return False
            
            # Verifica limites diários (anti-ban)
            if self.anti_detection:
                if not self.anti_detection.check_daily_limits("trade"):
                    self.logger.warning("⚠️ Limite diário de trades atingido. Aguardando...")
                    return False
                
                # Verifica se deve evitar ação (horário de pico)
                if self.anti_detection.should_avoid_action():
                    self.logger.warning("⚠️ Horário de pico detectado. Aguardando...")
                    time.sleep(3600)  # Aguarda 1 hora
                    return False
            
            self.logger.info(f"💰 Iniciando transferência de {amount} coins via mercado...")
            
            # Divide em transações menores para evitar detecção
            transactions = []
            remaining = amount
            
            while remaining > 0:
                transaction_amount = min(remaining, self.coins_per_transaction)
                transactions.append(transaction_amount)
                remaining -= transaction_amount
            
            self.logger.info(f"📊 Serão feitas {len(transactions)} transações")
            
            # Limita número de transações por dia (anti-ban)
            max_transactions_per_day = 5  # Máximo de 5 transações de comfort trade por dia
            if len(transactions) > max_transactions_per_day:
                self.logger.warning(f"⚠️ Muitas transações ({len(transactions)}). Limitando a {max_transactions_per_day} por dia (anti-ban)")
                transactions = transactions[:max_transactions_per_day]
            
            # Executa cada transação com delay humano
            for i, transaction_amount in enumerate(transactions, 1):
                # Verifica se deve parar
                if not self.running:
                    break
                
                # Verifica limites antes de cada transação
                if self.anti_detection:
                    if not self.anti_detection.check_daily_limits("trade"):
                        self.logger.warning(f"⚠️ Limite diário atingido na transação {i}")
                        break
                
                self.logger.info(f"🔄 Transação {i}/{len(transactions)}: {transaction_amount} coins")
                
                # Aguarda delay humano entre transações (anti-ban)
                if i > 1:
                    if self.anti_detection:
                        # Usa delay humano do sistema anti-detecção
                        delay = self.anti_detection.get_human_like_delay("trade")
                        delay = max(self.transfer_delay_min, min(self.transfer_delay_max, delay * 60))  # Converte para segundos
                    else:
                        delay = random.uniform(self.transfer_delay_min, self.transfer_delay_max)
                    
                    self.logger.info(f"⏳ Aguardando {delay/60:.1f} minutos antes da próxima transação (anti-ban)...")
                    time.sleep(delay)
                    
                    # Adiciona variação aleatória extra (anti-ban)
                    if self.anti_detection:
                        extra_delay = random.uniform(30, 120)  # 30s a 2min extra
                        time.sleep(extra_delay)
                
                # Adiciona ação ao histórico (anti-ban)
                if self.anti_detection:
                    self.anti_detection.add_action_to_history("comfort_trade_transfer", time.time())
                
                # Procura jogador listado pelo cliente
                # (O cliente deve ter listado um jogador barato por preço alto)
                if self._find_and_buy_client_player(transaction_amount):
                    self.stats["coins_transferred"] += transaction_amount
                    self.stats["transactions_completed"] += 1
                    self.logger.info(f"✅ Transação {i} concluída!")
                    
                    # Delay humano após transação (anti-ban)
                    if self.anti_detection:
                        post_delay = self.anti_detection.get_human_like_delay("general")
                        time.sleep(post_delay)
                else:
                    self.logger.error(f"❌ Falha na transação {i}")
                    self.stats["errors"] += 1
                    # Continua mesmo com erro (pode ser que o jogador já foi vendido)
                    
                    # Delay mesmo em caso de erro (anti-ban)
                    if self.anti_detection:
                        error_delay = random.uniform(10, 30)
                        time.sleep(error_delay)
            
            self.logger.info(f"✅ Transferência concluída! Total: {self.stats['coins_transferred']} coins")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao transferir coins via mercado: {e}")
            self.stats["errors"] += 1
            return False
    
    def _find_and_buy_client_player(self, price):
        """
        Encontra e compra jogador listado pelo cliente
        
        O cliente deve ter listado um jogador com características únicas:
        - Liga específica
        - Nacionalidade específica
        - Posição específica
        - Preço alto (valor da transferência)
        """
        try:
            self.logger.info("🔍 Procurando jogador listado pelo cliente...")
            
            # Navega para Transfer Market
            from bot.navigation import Navigation
            from bot.real_detection import RealDetection
            
            real_detection = RealDetection(self.screen_capture, self.logger, self.controller)
            nav = Navigation(self.controller, self.screen_capture, real_detection, self.logger)
            
            if not nav.navigate_to_transfer_market():
                self.logger.error("❌ Não foi possível navegar para Transfer Market")
                return False
            
            # Configurações de busca (devem ser combinadas com o cliente)
            search_filters = self.comfort_config.get("search_filters", {})
            
            # Aplica filtros de busca
            # (Implementação depende da interface do jogo)
            # Por enquanto, assume que o jogador está na primeira página
            
            # Procura jogador com preço específico usando detecção real
            self.logger.info(f"💰 Procurando jogador por {price} coins...")
            
            # Delay humano antes de buscar (anti-ban)
            if self.anti_detection:
                search_delay = self.anti_detection.get_human_like_delay("trade")
            else:
                search_delay = random.uniform(2, 4)
            time.sleep(search_delay)
            
            # Detecta jogadores na tela e procura pelo preço
            from bot.real_detection import RealDetection
            real_detection = RealDetection(self.screen_capture, self.logger, self.controller)
            
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return False
            
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            # Procura em slots visíveis
            num_slots = 5
            for i in range(num_slots):
                slot_height = screen_height // (num_slots + 2)
                slot_y_start = screen_height // 4 + (i * slot_height)
                slot_y_end = slot_y_start + slot_height
                
                player_region = (
                    screen_width // 4,
                    slot_y_start,
                    screen_width * 3 // 4,
                    slot_y_end
                )
                
                # Detecta jogador nesta região
                player_info = real_detection.detect_player_in_market(player_region)
                
                if player_info and player_info.get("price"):
                    player_price = player_info.get("price", 0)
                    
                    # Verifica se o preço corresponde (com margem de erro de 5%)
                    price_tolerance = price * 0.05
                    if abs(player_price - price) <= price_tolerance:
                        # Encontrou jogador com preço correto!
                        player_x = (player_region[0] + player_region[2]) // 2
                        player_y = (player_region[1] + player_region[3]) // 2
                        
                        self.logger.info(f"✅ Jogador encontrado com preço {player_price} coins")
                        
                        # Compra jogador usando navegação
                        if nav.buy_player_at_position(player_x, player_y):
                            self.logger.info("✅ Jogador comprado com sucesso!")
                            return True
                        else:
                            self.logger.warning("⚠️  Falha ao comprar jogador")
                            return False
            
            self.logger.warning(f"⚠️  Jogador com preço {price} não encontrado")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao procurar jogador do cliente: {e}")
            return False
    
    def farm_coins_via_matches(self, target_coins):
        """
        Farm coins jogando partidas e vendendo cartas
        
        Método:
        1. Joga Squad Battles
        2. Coleta recompensas
        3. Vende cartas não utilizadas
        4. Repete até atingir target_coins
        """
        try:
            if not self.is_client_logged_in:
                self.logger.error("❌ Não está logado na conta do cliente!")
                return False
            
            self.logger.info(f"🎮 Iniciando farm de coins via partidas...")
            self.logger.info(f"🎯 Meta: {target_coins} coins")
            
            current_coins = 0
            matches_played = 0
            
            # Loop até atingir meta
            while current_coins < target_coins:
                self.logger.info(f"📊 Progresso: {current_coins}/{target_coins} coins ({matches_played} partidas)")
                
                # Joga uma partida de Squad Battles
                if self.squad_battles_bot:
                    self.logger.info("🎮 Jogando partida de Squad Battles...")
                    if self.squad_battles_bot.play_match():
                        matches_played += 1
                        self.stats["matches_played"] += 1
                        
                        # Coleta recompensas - REQUER DETECÇÃO REAL
                        # TODO: Implementar detecção real de coins ganhos após partida
                        self.logger.warning("⚠️  Detecção de coins ganhos não implementada. Pulando coleta de recompensas.")
                        # coins_earned = 0  # Será detectado quando implementado
                        # current_coins += coins_earned
                    else:
                        self.logger.warning("⚠️  Partida não foi completada")
                
                # Vende cartas não utilizadas (a cada 3 partidas)
                if matches_played % 3 == 0:
                    self.logger.info("📦 Vendendo cartas não utilizadas...")
                    cards_sold = self._sell_unused_cards()
                    self.stats["cards_sold"] += cards_sold
                
                # Verifica limites diários antes de próxima partida (anti-ban)
                if self.anti_detection:
                    if not self.anti_detection.check_daily_limits("match"):
                        self.logger.warning("⚠️ Limite diário de partidas atingido")
                        break
                    
                    # Verifica horário de pico
                    if self.anti_detection.should_avoid_action():
                        self.logger.warning("⚠️ Horário de pico. Aguardando...")
                        time.sleep(3600)  # Aguarda 1 hora
                        continue
                
                # Delay humano entre partidas (anti-ban)
                if self.anti_detection:
                    match_delay = self.anti_detection.get_human_like_delay("match")
                    match_delay = max(60, min(300, match_delay * 60))  # 1-5 minutos
                else:
                    match_delay = random.uniform(60, 120)  # 1-2 minutos
                time.sleep(match_delay)
            
            self.logger.info(f"✅ Farm concluído! Total: {current_coins} coins em {matches_played} partidas")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao farmar coins: {e}")
            return False
    
    def _sell_unused_cards(self):
        """Vende cartas não utilizadas no time"""
        try:
            # Navega para o clube
            from bot.navigation import Navigation
            nav = Navigation(self.controller, self.screen_capture, self.logger)
            
            # Vende cartas duplicadas ou não utilizadas
            # (Implementação requer navegação e detecção)
            self.logger.info("💼 Vendendo cartas...")
            
            # TODO: Implementar venda real de cartas
            # Requer:
            # 1. Navegação para "My Club" -> "Unassigned"
            # 2. Detecção de cartas não utilizadas
            # 3. Listagem para venda
            self.logger.warning("⚠️  Venda de cartas não implementada. Funcionalidade desabilitada.")
            
            return 0  # Retorna 0 até implementar venda real
            
        except Exception as e:
            self.logger.error(f"Erro ao vender cartas: {e}")
            return 0
    
    def execute_comfort_trade(self):
        """
        Executa o processo completo de Comfort Trade
        
        ⚠️ ATENÇÃO: Este método envolve riscos significativos!
        """
        try:
            if not self.enabled:
                self.logger.warning("⚠️  Comfort Trade não está habilitado!")
                return False
            
            # Aviso de segurança
            self.logger.warning("=" * 60)
            self.logger.warning("⚠️  AVISO DE SEGURANÇA - COMFORT TRADE")
            self.logger.warning("=" * 60)
            self.logger.warning("⚠️  RISCOS:")
            self.logger.warning("   - Banimento do Mercado de Transferências")
            self.logger.warning("   - Reset de Coins")
            self.logger.warning("   - Banimento da Conta")
            self.logger.warning("   - Roubo de Credenciais")
            self.logger.warning("=" * 60)
            
            # Inicializa módulos
            if not self.initialize():
                return False
            
            # Faz login na conta do cliente
            if not self.login_to_client_account():
                return False
            
            # Executa transferência baseada no método escolhido
            if self.transfer_method == "market":
                if not self.transfer_coins_via_market(self.target_coins):
                    return False
            elif self.transfer_method == "farming":
                if not self.farm_coins_via_matches(self.target_coins):
                    return False
            else:
                self.logger.error(f"❌ Método de transferência inválido: {self.transfer_method}")
                return False
            
            # Log de estatísticas
            self.logger.info("=" * 60)
            self.logger.info("📊 ESTATÍSTICAS DO COMFORT TRADE")
            self.logger.info("=" * 60)
            self.logger.info(f"💰 Coins transferidas: {self.stats['coins_transferred']}")
            self.logger.info(f"🔄 Transações completadas: {self.stats['transactions_completed']}")
            self.logger.info(f"🎮 Partidas jogadas: {self.stats['matches_played']}")
            self.logger.info(f"📦 Cartas vendidas: {self.stats['cards_sold']}")
            self.logger.info(f"❌ Erros: {self.stats['errors']}")
            self.logger.info("=" * 60)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao executar Comfort Trade: {e}")
            return False
    
    def get_stats(self):
        """Retorna estatísticas do Comfort Trade"""
        return self.stats.copy()

