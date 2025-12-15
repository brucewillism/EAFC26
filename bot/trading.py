"""
Módulo de Trading - Compra e venda automática de jogadores com integração Futbin
"""

import time
import random
from bot.base_module import BaseModule
from bot.game_detection import GameDetection
from bot.futbin_integration import FutbinIntegration

class TradingBot(BaseModule):
    """Bot para trading automático de jogadores com análise Futbin"""
    
    def __init__(self, config, controller, screen_capture, logger, anti_detection=None):
        super().__init__(config, controller, screen_capture, logger)
        self.anti_detection = anti_detection
        self.trading_config = config.get("trading", {})
        self.enabled = self.trading_config.get("enabled", False)
        self.running = True  # Flag para controlar execução
        
        # Inicializa detecção de jogo
        self.game_detection = GameDetection(screen_capture, logger)
        
        # Inicializa detecção real
        from bot.real_detection import RealDetection
        self.real_detection = RealDetection(screen_capture, logger, controller)
        
        # Inicializa navegação inteligente
        from bot.navigation import Navigation
        self.navigation = Navigation(controller, screen_capture, self.real_detection, logger)
        
        # Inicializa sistema de recuperação de erros
        from bot.error_recovery import ErrorRecovery
        self.error_recovery = ErrorRecovery(controller, screen_capture, self.real_detection, logger)
        
        # Inicializa integração com Futbin
        self.futbin = FutbinIntegration(logger, cache_duration=300)
        self.use_futbin = self.trading_config.get("use_futbin", True)
        self.platform = self.trading_config.get("platform", "pc")
        
        # Configurações de trading
        self.min_profit = self.trading_config.get("min_profit", 500)
        self.max_price = self.trading_config.get("max_price", 10000)
        self.min_profit_percentage = self.trading_config.get("min_profit_percentage", 10.0)
        self.search_interval = self.trading_config.get("search_interval", 5)
        self.buy_delay = self.trading_config.get("buy_delay", 2)
        self.sell_delay = self.trading_config.get("sell_delay", 3)
        self.market_monitor_interval = self.trading_config.get("market_monitor_interval", 60)
        
        # Lista de jogadores comprados aguardando venda
        self.pending_sales = []
        
        # Estatísticas detalhadas
        self.stats = {
            "bought": 0,
            "sold": 0,
            "profit": 0,
            "errors": 0,
            "opportunities_found": 0,
            "trades_history": []  # Histórico de trades
        }
        
        # Última verificação de oportunidades
        self.last_opportunity_check = 0
        
    def run_cycle(self):
        """Executa um ciclo de trading com monitoramento de mercado"""
        if not self.enabled:
            return
        
        try:
            self.logger.info("Iniciando ciclo de trading...")
            
            # 1. Verifica oportunidades no Futbin (periodicamente)
            current_time = time.time()
            if current_time - self.last_opportunity_check > self.market_monitor_interval:
                self.check_market_opportunities()
                self.last_opportunity_check = current_time
            
            # 2. Navegar para Transfer Market
            if not self.navigate_to_transfer_market():
                return
            
            # 3. Buscar jogadores
            players = self.search_players()
            
            self.logger.info(f"Jogadores encontrados no mercado: {len(players)}")
            
            # 4. Analisar e comprar jogadores lucrativos
            players_bought = 0
            for player in players:
                if not self.running:  # Verifica se bot foi parado
                    break
                    
                if self.analyze_player(player):
                    player_name = player.get('name', 'Unknown')
                    player_price = player.get('price', 0)
                    expected_profit = player.get('expected_profit', 0)
                    
                    self.logger.info(f"🎯 OPORTUNIDADE ENCONTRADA: {player_name} - Preço: {player_price}, Lucro esperado: {expected_profit}")
                    
                    if self.buy_player(player):
                        players_bought += 1
                        # Adiciona à lista de vendas pendentes
                        self.pending_sales.append({
                            "name": player_name,
                            "buy_price": player_price,
                            "expected_sell_price": player.get("futbin_price", 0),
                            "expected_profit": expected_profit,
                            "timestamp": time.time()
                        })
                        self.logger.info(f"✅ Jogador comprado! Total comprado nesta sessão: {self.stats['bought']}")
                        time.sleep(self.buy_delay)
                    else:
                        self.logger.warning("❌ Falha ao comprar jogador")
            
            if players_bought > 0:
                self.logger.info(f"Total de {players_bought} jogador(es) comprado(s) neste ciclo")
            else:
                self.logger.info("Nenhum jogador comprado neste ciclo (nenhum jogador lucrativo encontrado)")
            
            # 5. Vender jogadores do clube
            players_sold = self.sell_players()
            if players_sold > 0:
                self.logger.info(f"Total de {players_sold} jogador(es) vendido(s) neste ciclo")
            
            # Aguarda antes do próximo ciclo
            time.sleep(self.search_interval)
            
        except Exception as e:
            self.logger.error(f"Erro no ciclo de trading: {e}", exc_info=True)
            self.stats["errors"] += 1
    
    def check_market_opportunities(self):
        """Verifica oportunidades de mercado no Futbin (se disponível)"""
        try:
            if not self.use_futbin:
                self.logger.info("ℹ️ Futbin desabilitado. Bot trabalhará apenas com análise de mercado local.")
                return
            
            self.logger.info("🔍 Verificando oportunidades de mercado no Futbin...")
            
            # Usa estratégia de jogadores baratos por padrão
            strategy = self.trading_config.get("strategy", "undervalued")
            targets = self.trading_config.get("targets") if strategy == "targets" else None
            
            try:
                opportunities = self.futbin.get_market_opportunities(
                    min_profit=self.min_profit,
                    max_price=self.max_price,
                    min_profit_percentage=self.min_profit_percentage,
                    platform=self.platform,
                    targets=targets,
                    limit=20,  # Aumenta limite para jogadores baratos
                    strategy=strategy
                )
                
                if opportunities:
                    self.logger.info(f"📊 {len(opportunities)} oportunidades encontradas no Futbin")
                    for opp in opportunities[:5]:  # Mostra top 5
                        self.logger.info(f"  - {opp.get('player_name', 'Unknown')}: Lucro {opp.get('profit', 0)} ({opp.get('profit_percentage', 0):.1f}%)")
                else:
                    self.logger.debug("Nenhuma oportunidade encontrada no Futbin no momento")
            except Exception as futbin_error:
                # Se Futbin estiver bloqueado, desabilita e continua sem ele
                if "403" in str(futbin_error) or "blocked" in str(futbin_error).lower():
                    self.logger.warning("⚠️ Futbin está bloqueando requisições (403). Desabilitando Futbin e usando apenas análise de mercado local.")
                    self.use_futbin = False
                    self.logger.info("ℹ️ Bot continuará funcionando analisando jogadores diretamente no mercado do jogo.")
                else:
                    self.logger.debug(f"Erro ao verificar oportunidades no Futbin: {futbin_error}")
                
        except Exception as e:
            self.logger.debug(f"Erro ao verificar oportunidades: {e}")
    
    def navigate_to_transfer_market(self):
        """Navega para o Transfer Market usando navegação inteligente"""
        try:
            # Usa sistema de navegação inteligente
            success = self.navigation.navigate_to_transfer_market()
            
            if not success:
                # Tenta recuperar de erro
                self.error_recovery.handle_error("navigation_failed")
                # Tenta novamente
                success = self.navigation.navigate_to_transfer_market()
            
            return success
            
        except Exception as e:
            self.logger.error(f"Erro ao navegar para Transfer Market: {e}")
            return False
    
    def search_players(self):
        """Busca jogadores no mercado - DETECÇÃO REAL"""
        try:
            self.logger.info("Buscando jogadores no mercado...")
            
            # Verifica se está na tela correta
            current_screen = self.real_detection.detect_current_screen()
            if current_screen != "transfer_market":
                self.logger.warning(f"Tela atual: {current_screen}. Navegando para Transfer Market...")
                if not self.navigate_to_transfer_market():
                    return []
            
            # Aguarda carregar
            time.sleep(2)
            
            # Lista de jogadores encontrados
            players = []
            
            # Detecta jogadores na tela usando detecção real
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return []
            
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            # Regiões onde aparecem jogadores (ajustar conforme layout)
            # Geralmente aparecem em lista vertical
            num_slots = 5  # Número de slots visíveis
            
            for i in range(num_slots):
                # Calcula região do slot
                slot_height = screen_height // (num_slots + 2)
                slot_y_start = screen_height // 4 + (i * slot_height)
                slot_y_end = slot_y_start + slot_height
                
                player_region = (
                    screen_width // 4,      # X início
                    slot_y_start,           # Y início
                    screen_width * 3 // 4,  # X fim
                    slot_y_end               # Y fim
                )
                
                # Detecta jogador nesta região
                player_info = self.real_detection.detect_player_in_market(player_region)
                
                if player_info and player_info.get("name") and player_info.get("price"):
                    players.append({
                        "name": player_info["name"],
                        "price": player_info["price"],
                        "region": player_region
                    })
                    self.logger.info(f"Jogador REAL detectado: {player_info['name']} - {player_info['price']} coins")
            
            if players:
                self.logger.info(f"Total de {len(players)} jogadores detectados no mercado")
            else:
                self.logger.warning("Nenhum jogador detectado. Pode precisar calibrar regiões.")
            
            return players
            
        except Exception as e:
            self.logger.error(f"Erro ao buscar jogadores: {e}")
            return []
    
    def analyze_player(self, player):
        """Analisa se um jogador é lucrativo usando Futbin"""
        try:
            player_name = player.get("name", "")
            current_price = player.get("price", 0)
            
            if not player_name or current_price == 0:
                return False
            
            # Verifica limites básicos
            if current_price > self.max_price:
                self.logger.debug(f"{player_name}: Preço muito alto ({current_price} > {self.max_price})")
                return False
            
            # Se Futbin está habilitado, tenta usar análise com dados reais
            if self.use_futbin:
                try:
                    analysis = self.futbin.analyze_trade_opportunity(
                        player_name, 
                        current_price, 
                        self.platform
                    )
                    
                    # Se Futbin retornou dados válidos
                    if analysis and analysis.get("futbin_price", 0) > 0:
                        if not analysis.get("profitable", False):
                            reason = analysis.get("reason", "Não lucrativo")
                            self.logger.debug(f"{player_name}: {reason}")
                            return False
                        
                        profit = analysis.get("profit", 0)
                        profit_percentage = analysis.get("profit_percentage", 0)
                        futbin_price = analysis.get("futbin_price", 0)
                        
                        # Verifica se atende critérios mínimos
                        if profit < self.min_profit:
                            self.logger.debug(f"{player_name}: Lucro insuficiente ({profit} < {self.min_profit})")
                            return False
                        
                        if profit_percentage < self.min_profit_percentage:
                            self.logger.debug(f"{player_name}: Percentual de lucro insuficiente ({profit_percentage:.1f}% < {self.min_profit_percentage}%)")
                            return False
                        
                        # Salva análise no player para uso posterior
                        player["analysis"] = analysis
                        player["futbin_price"] = futbin_price
                        player["expected_profit"] = profit
                        player["profit_percentage"] = profit_percentage
                        
                        self.logger.info(f"✅ OPORTUNIDADE: {player_name} - Compra: {current_price}, Futbin: {futbin_price}, Lucro: {profit} ({profit_percentage:.1f}%)")
                        self.stats["opportunities_found"] += 1
                        return True
                    else:
                        # Futbin não retornou dados (bloqueado ou erro), usa análise sem Futbin
                        self.logger.debug(f"{player_name}: Futbin indisponível, usando análise de mercado local")
                except Exception as e:
                    self.logger.debug(f"{player_name}: Erro ao consultar Futbin ({e}), usando análise local")
            
            # Análise sem Futbin (fallback ou quando Futbin está bloqueado)
            # Estratégia: Compra jogadores baratos e assume que podem valorizar
            # Foca em jogadores com preço baixo que têm potencial de revenda
            if current_price <= self.max_price:
                # Para jogadores baratos (até 5000), assume lucro conservador de 15-25%
                if current_price <= 2000:
                    # Jogadores muito baratos: maior margem de lucro esperada
                    expected_sell_price = current_price * 1.25
                    profit = expected_sell_price - current_price
                    profit_percentage = 25.0
                elif current_price <= 5000:
                    # Jogadores médios: margem moderada
                    expected_sell_price = current_price * 1.20
                    profit = expected_sell_price - current_price
                    profit_percentage = 20.0
                else:
                    # Jogadores mais caros: margem menor
                    expected_sell_price = current_price * 1.15
                    profit = expected_sell_price - current_price
                    profit_percentage = 15.0
                
                # Considera taxa de 5% do EA
                profit_after_tax = profit * 0.95
                
                if profit_after_tax >= self.min_profit:
                    player["expected_profit"] = int(profit_after_tax)
                    player["profit_percentage"] = profit_percentage
                    player["futbin_price"] = 0  # Não temos preço Futbin
                    self.logger.info(f"✅ OPORTUNIDADE (sem Futbin): {player_name} - Compra: {current_price}, Lucro esperado: {int(profit_after_tax)} ({profit_percentage:.1f}%)")
                    self.stats["opportunities_found"] += 1
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao analisar jogador: {e}")
            return False
    
    def buy_player(self, player):
        """Compra um jogador usando navegação inteligente"""
        try:
            player_name = player.get('name', 'Unknown')
            player_price = player.get('price', 0)
            analysis = player.get('analysis', {})
            expected_profit = player.get('expected_profit', 0)
            region = player.get('region')
            
            self.logger.info(f"💰 Comprando jogador: {player_name} por {player_price} coins (Lucro esperado: {expected_profit})")
            
            # Verifica se há erro na tela antes de comprar
            if not self.error_recovery.check_and_recover():
                self.logger.warning("Erro detectado na tela. Pulando compra.")
                return False
            
            # Calcula coordenadas do jogador
            if region:
                # Usa centro da região do jogador
                player_x = (region[0] + region[2]) // 2
                player_y = (region[1] + region[3]) // 2
            else:
                # Fallback: assume posição padrão
                player_x, player_y = 960, 540
            
            # Usa navegação inteligente para comprar
            success = self.navigation.buy_player_at_position(player_x, player_y)
            
            if not success:
                # Tenta recuperar de erro
                error_type = self.error_recovery.detect_error_screen()
                if error_type:
                    self.error_recovery.handle_error(error_type)
                return False
            
            # Verifica se compra foi bem-sucedida (detecta erro após compra)
            time.sleep(1)
            error_type = self.error_recovery.detect_error_screen()
            if error_type:
                self.logger.warning(f"Erro após tentativa de compra: {error_type}")
                self.error_recovery.handle_error(error_type)
                return False
            
            # Adiciona ao histórico com informações do Futbin
            trade_info = {
                "type": "buy",
                "player_name": player_name,
                "price": player_price,
                "futbin_price": analysis.get("futbin_price", 0),
                "expected_profit": expected_profit,
                "profit_percentage": player.get('profit_percentage', 0),
                "timestamp": time.time()
            }
            self.stats["trades_history"].append(trade_info)
            if len(self.stats["trades_history"]) > 100:  # Mantém últimas 100
                self.stats["trades_history"].pop(0)
            
            self.stats["bought"] += 1
            self.stats["profit"] -= player_price  # Reduz profit temporariamente
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao comprar jogador: {e}")
            return False
    
    def sell_players(self):
        """Vende jogadores do clube usando preços do Futbin"""
        try:
            self.logger.info("💼 Verificando jogadores para venda...")
            
            players_sold = 0
            
            # 1. Processa lista de vendas pendentes (jogadores já comprados)
            if self.pending_sales:
                self.logger.info(f"Processando {len(self.pending_sales)} jogadores pendentes para venda...")
                
                # Navega para "My Club" -> "Transfer List" para listar jogadores
                if not self.navigate_to_transfer_list():
                    self.logger.warning("Não foi possível navegar para Transfer List. Pulando vendas pendentes.")
                    return 0
                
                for pending in self.pending_sales[:5]:  # Processa até 5 por ciclo
                    if not self.running:
                        break
                    
                    player_name = pending["name"]
                    expected_sell_price = pending["expected_sell_price"]
                    
                    # Atualiza preço do Futbin antes de vender
                    if self.use_futbin:
                        futbin_data = self.futbin.search_player(player_name, self.platform)
                        if futbin_data and futbin_data.get("price", 0) > 0:
                            expected_sell_price = futbin_data.get("price", 0)
                            pending["expected_sell_price"] = expected_sell_price
                    
                    # Calcula preço de venda considerando taxa de 5%
                    # Vende ligeiramente abaixo do preço Futbin para garantir venda rápida
                    sell_price = int(expected_sell_price * 0.98) if expected_sell_price > 0 else pending.get("buy_price", 0) * 1.15
                    
                    # Procura jogador no clube e lista para venda
                    if self.find_and_list_player(player_name, sell_price):
                        players_sold += 1
                        buy_price = pending["buy_price"]
                        actual_profit = sell_price - buy_price
                        
                        self.logger.info(f"✅ {player_name} listado para venda: Compra {buy_price}, Venda {sell_price}, Lucro {actual_profit}")
                        time.sleep(self.sell_delay)
                    else:
                        self.logger.warning(f"⚠️  Não foi possível listar {player_name} para venda")
                
                # Remove vendidos da lista pendente
                self.pending_sales = self.pending_sales[players_sold:]
            
            # 2. Verifica se há jogadores no clube para vender (duplicados ou não utilizados)
            if players_sold < 5:  # Se ainda há espaço, verifica clube
                if self.navigate_to_my_club():
                    club_players = self.detect_players_in_club()
                    if club_players:
                        self.logger.info(f"Encontrados {len(club_players)} jogadores no clube para possível venda")
                        # Por enquanto, apenas loga. Pode implementar venda automática depois
                        for player in club_players[:3]:  # Limita a 3 para não exceder limite
                            if not self.running:
                                break
                            # Verifica se vale a pena vender (pode adicionar lógica aqui)
                            self.logger.debug(f"Jogador no clube: {player.get('name', 'Unknown')}")
            
            if players_sold == 0:
                self.logger.info("Nenhum jogador para vender no momento")
            
            return players_sold
            
        except Exception as e:
            self.logger.error(f"Erro ao vender jogadores: {e}", exc_info=True)
            return 0
    
    def navigate_to_transfer_list(self):
        """Navega para Transfer List (lista de jogadores para venda)"""
        try:
            self.logger.info("🧭 Navegando para Transfer List...")
            
            # Verifica se já está na tela correta
            current_screen = self.real_detection.detect_current_screen()
            if "transfer" in current_screen.lower() or "list" in current_screen.lower():
                self.logger.info("Já está na tela de Transfer List")
                return True
            
            # Navega: Ultimate Team -> My Club -> Transfer List
            if not self.navigation.navigate_to_ultimate_team():
                return False
            
            time.sleep(1)
            
            # Clica em "My Club"
            if not self.navigation.click_button("My Club", method="auto", timeout=5):
                # Fallback: tenta coordenadas padrão
                self.controller.click(960, 450)
                time.sleep(1)
            
            # Clica em "Transfer List"
            if not self.navigation.click_button("Transfer List", method="auto", timeout=5):
                # Fallback: tenta coordenadas padrão
                self.controller.click(960, 500)
                time.sleep(1)
            
            # Verifica se chegou
            time.sleep(2)
            current_screen = self.real_detection.detect_current_screen()
            if "transfer" in current_screen.lower() or "list" in current_screen.lower():
                self.logger.info("✅ Chegou ao Transfer List")
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao navegar para Transfer List: {e}")
            return False
    
    def navigate_to_my_club(self):
        """Navega para My Club"""
        try:
            self.logger.info("🧭 Navegando para My Club...")
            
            if not self.navigation.navigate_to_ultimate_team():
                return False
            
            time.sleep(1)
            
            if not self.navigation.click_button("My Club", method="auto", timeout=5):
                self.controller.click(960, 450)
                time.sleep(2)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao navegar para My Club: {e}")
            return False
    
    def find_and_list_player(self, player_name, sell_price):
        """Encontra jogador no clube e lista para venda"""
        try:
            self.logger.info(f"🔍 Procurando {player_name} no clube...")
            
            # Detecta jogadores na tela atual
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return False
            
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            # Procura jogador em slots visíveis (ajustar conforme layout)
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
                player_info = self.real_detection.detect_player_in_market(player_region)
                
                if player_info and player_info.get("name"):
                    detected_name = player_info.get("name", "").lower()
                    target_name = player_name.lower()
                    
                    # Verifica se é o jogador procurado (match parcial)
                    if target_name in detected_name or detected_name in target_name:
                        player_x = (player_region[0] + player_region[2]) // 2
                        player_y = (player_region[1] + player_region[3]) // 2
                        
                        # Lista jogador para venda
                        return self.list_player_for_sale_at_position(player_x, player_y, sell_price)
            
            self.logger.warning(f"Jogador {player_name} não encontrado no clube")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao procurar jogador: {e}")
            return False
    
    def detect_players_in_club(self):
        """Detecta jogadores no clube"""
        try:
            players = []
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return []
            
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            # Detecta jogadores visíveis
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
                
                player_info = self.real_detection.detect_player_in_market(player_region)
                if player_info and player_info.get("name"):
                    players.append(player_info)
            
            return players
            
        except Exception as e:
            self.logger.error(f"Erro ao detectar jogadores no clube: {e}")
            return []
    
    def list_player_for_sale(self, player_name, sell_price):
        """Lista jogador para venda (wrapper para compatibilidade)"""
        # Esta função agora é um wrapper que chama find_and_list_player
        # Mantida para compatibilidade com código existente
        return self.find_and_list_player(player_name, sell_price)
    
    def list_player_for_sale_at_position(self, x, y, sell_price):
        """Lista jogador para venda na posição especificada"""
        try:
            self.logger.info(f"💼 Listando jogador em ({x}, {y}) por {sell_price} coins...")
            
            # 1. Clica no jogador
            self.controller.click(x, y)
            time.sleep(1)
            
            # 2. Clica em "List for Transfer" ou "Sell"
            if not self.navigation.click_button("List for Transfer", method="auto", timeout=3):
                if not self.navigation.click_button("Sell", method="auto", timeout=3):
                    # Fallback: tenta coordenadas padrão (lado direito da tela)
                    self.controller.click(1400, 600)
                    time.sleep(1)
            
            # 3. Define preço de venda
            # Primeiro, limpa campo de preço (se houver)
            self.controller.press_key('tab')
            time.sleep(0.3)
            
            # Seleciona todo o texto e digita novo preço
            self.controller.key_combination('ctrl', 'a')
            time.sleep(0.2)
            self.controller.type_text(str(sell_price), human_typing=True)
            time.sleep(0.5)
            
            # 4. Confirma listagem
            if not self.navigation.click_button("Confirm", method="auto", timeout=3):
                if not self.navigation.click_button("List", method="auto", timeout=3):
                    # Fallback: Enter ou coordenadas padrão
                    self.controller.press_key('enter')
                    time.sleep(0.5)
            
            # 5. Fecha diálogo de confirmação (se aparecer)
            time.sleep(1)
            self.controller.press_key('esc')
            time.sleep(0.5)
            
            # Adiciona ao histórico
            trade_info = {
                "type": "sell",
                "player_name": "Unknown",  # Nome será atualizado se disponível
                "price": sell_price,
                "timestamp": time.time()
            }
            self.stats["trades_history"].append(trade_info)
            if len(self.stats["trades_history"]) > 100:
                self.stats["trades_history"].pop(0)
            
            self.stats["sold"] += 1
            self.stats["profit"] += sell_price
            
            self.logger.info("✅ Jogador listado para venda")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao listar jogador: {e}")
            return False
    
    def get_stats(self):
        """Retorna estatísticas do trading"""
        return self.stats.copy()

