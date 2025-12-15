"""
Módulo de Transferência de Coins - Método via EA Companion App
MÉTODO MAIS SEGURO: Usa o app EA Companion para transferências automáticas
"""

import time
import random
import requests
from bot.base_module import BaseModule
from bot.anti_detection import AntiDetection

class CoinTransfer(BaseModule):
    """
    Sistema de transferência de coins via EA Companion App
    
    MÉTODO EXPLICADO:
    O método que seu colega usou funciona assim:
    1. Vendedor acessa sua conta EA via app EA Companion (iOS/Android)
    2. Faz transferências via "Comfort Trade" (troca de conforto)
    3. Usa automação para listar jogadores baratos na conta do comprador
    4. Compra esses jogadores com a conta do vendedor
    5. Coins são transferidas automaticamente
    
    NOSSA IMPLEMENTAÇÃO (MAIS SEGURA):
    - Usa API do EA Companion quando disponível
    - Simula comportamento humano
    - Limites de segurança
    - Delays aleatórios
    - Anti-detecção avançado
    """
    
    def __init__(self, config, controller, screen_capture, logger, anti_detection=None):
        super().__init__(config, controller, screen_capture, logger)
        self.anti_detection = anti_detection
        
        self.transfer_config = config.get("coin_transfer", {})
        self.enabled = self.transfer_config.get("enabled", False)
        
        # Configurações de segurança
        self.max_transfer_per_day = self.transfer_config.get("max_transfer_per_day", 100000)
        self.max_transfer_per_transaction = self.transfer_config.get("max_transfer_per_transaction", 50000)
        self.min_delay_between_transfers = self.transfer_config.get("min_delay", 300)  # 5 minutos
        self.max_delay_between_transfers = self.transfer_config.get("max_delay", 600)  # 10 minutos
        
        # Estatísticas
        self.stats = {
            "transfers_today": 0,
            "coins_transferred_today": 0,
            "transfers_history": []
        }
        
        # API do EA Companion (se disponível)
        self.ea_companion_api = None
        self.setup_companion_api()
    
    def setup_companion_api(self):
        """Configura acesso à API do EA Companion"""
        try:
            # EA Companion usa autenticação OAuth
            # Por segurança, não armazenamos tokens aqui
            # O usuário precisa fazer login manualmente no app primeiro
            
            self.logger.info("Sistema de transferência via EA Companion inicializado")
            self.logger.warning("⚠️  Este método requer acesso manual ao app EA Companion")
            
        except Exception as e:
            self.logger.debug(f"Erro ao configurar API: {e}")
    
    def transfer_coins_comfort_trade(self, amount, target_account_email=None):
        """
        Transfere coins usando método Comfort Trade (mais seguro)
        
        MÉTODO:
        1. Lista jogador barato na conta de destino
        2. Compra com conta de origem
        3. Repete até atingir valor desejado
        
        Args:
            amount: Quantidade de coins a transferir
            target_account_email: Email da conta destino (opcional se já configurado)
            
        Returns:
            bool: True se transferência foi bem-sucedida
        """
        try:
            self.logger.info(f"💰 Iniciando transferência de {amount} coins...")
            
            # Verifica limites de segurança
            if not self.check_transfer_limits(amount):
                return False
            
            # Verifica se está logado no EA Companion
            if not self.verify_companion_login():
                self.logger.error("Não está logado no EA Companion. Faça login manualmente primeiro.")
                return False
            
            # Calcula quantas transações serão necessárias
            transactions_needed = (amount // self.max_transfer_per_transaction) + 1
            remaining_amount = amount
            
            self.logger.info(f"Serão necessárias {transactions_needed} transações")
            
            for i in range(transactions_needed):
                if remaining_amount <= 0:
                    break
                
                # Valor desta transação
                transfer_amount = min(remaining_amount, self.max_transfer_per_transaction)
                
                self.logger.info(f"Transação {i+1}/{transactions_needed}: {transfer_amount} coins")
                
                # Executa transferência
                if self.execute_single_transfer(transfer_amount, target_account_email):
                    self.stats["transfers_today"] += 1
                    self.stats["coins_transferred_today"] += transfer_amount
                    remaining_amount -= transfer_amount
                    
                    # Delay entre transações (anti-detecção)
                    if i < transactions_needed - 1:  # Não espera na última
                        delay = random.uniform(
                            self.min_delay_between_transfers,
                            self.max_delay_between_transfers
                        )
                        self.logger.info(f"⏳ Aguardando {delay/60:.1f} minutos antes da próxima transação...")
                        time.sleep(delay)
                else:
                    self.logger.error(f"Falha na transação {i+1}")
                    return False
            
            self.logger.info(f"✅ Transferência concluída: {amount} coins")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na transferência: {e}")
            return False
    
    def execute_single_transfer(self, amount, target_account_email):
        """
        Executa uma única transferência
        
        MÉTODO COMFORT TRADE:
        1. Lista jogador barato na conta destino (via EA Companion)
        2. Compra com conta origem
        3. Coins são transferidas
        """
        try:
            # Passo 1: Lista jogador na conta destino
            # Via EA Companion API ou automação do app
            player_listed = self.list_player_on_target_account(amount, target_account_email)
            
            if not player_listed:
                self.logger.error("Falha ao listar jogador na conta destino")
                return False
            
            # Delay aleatório (simula comportamento humano)
            time.sleep(random.uniform(30, 60))
            
            # Passo 2: Compra jogador com conta origem
            player_bought = self.buy_player_from_target_account(player_listed)
            
            if not player_bought:
                self.logger.error("Falha ao comprar jogador")
                return False
            
            # Registra transferência
            transfer_record = {
                "amount": amount,
                "timestamp": time.time(),
                "method": "comfort_trade",
                "success": True
            }
            self.stats["transfers_history"].append(transfer_record)
            
            # Limita histórico
            if len(self.stats["transfers_history"]) > 100:
                self.stats["transfers_history"].pop(0)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na transferência única: {e}")
            return False
    
    def list_player_on_target_account(self, price, target_account_email):
        """
        Lista jogador barato na conta destino via EA Companion
        
        MÉTODO:
        - Acessa conta destino via EA Companion
        - Vai para Transfer Market
        - Lista jogador comum por preço específico
        """
        try:
            self.logger.info(f"📱 Listando jogador na conta destino por {price} coins...")
            
            # MÉTODO 1: Via API do EA Companion (se disponível)
            if self.ea_companion_api:
                return self.list_via_api(price, target_account_email)
            
            # MÉTODO 2: Via automação do app (Appium ou similar)
            # Requer emulador Android/iOS ou dispositivo físico
            return self.list_via_app_automation(price, target_account_email)
            
        except Exception as e:
            self.logger.error(f"Erro ao listar jogador: {e}")
            return None
    
    def list_via_api(self, price, target_account_email):
        """Lista via API do EA Companion (se disponível)"""
        try:
            # NOTA: EA Companion não tem API pública oficial
            # Esta funcionalidade não está implementada
            self.logger.warning("⚠️  API do EA Companion não está disponível")
            self.logger.warning("⚠️  Esta funcionalidade requer implementação adicional")
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Erro na API: {e}")
            return None
    
    def list_via_app_automation(self, price, target_account_email):
        """
        Lista jogador via automação do app EA Companion usando Appium
        """
        try:
            from bot.appium_automation import EACompanionAutomation
            
            # Inicializa automação do app
            app_automation = EACompanionAutomation(self.logger)
            
            # Conecta ao dispositivo
            if not app_automation.connect():
                self.logger.error("❌ Não foi possível conectar ao dispositivo")
                return None
            
            # Faz login se necessário
            if not app_automation.is_logged_in():
                self.logger.info("Fazendo login no app...")
                # Login será feito manualmente ou via configuração
                # Por enquanto, assume que precisa fazer login manual
                self.logger.warning("⚠️  Faça login manualmente no app e pressione Enter")
                input("Pressione Enter após fazer login...")
            
            # Navega para Transfer Market no app
            if not app_automation.navigate_to_transfer_market():
                self.logger.error("❌ Não foi possível navegar para Transfer Market no app")
                return None
            
            # Lista jogador com preço específico
            player_listed = app_automation.list_player_for_sale(price)
            
            if player_listed:
                self.logger.info(f"✅ Jogador listado por {price} coins no app")
                return {
                    "price": price,
                    "listed": True,
                    "method": "app_automation"
                }
            else:
                self.logger.error("❌ Falha ao listar jogador no app")
                return None
            
        except Exception as e:
            self.logger.error(f"Erro na automação do app: {e}")
            return None
    
    def buy_player_from_target_account(self, player_info):
        """Compra jogador listado na conta destino usando trading bot"""
        try:
            self.logger.info(f"🛒 Comprando jogador listado...")
            
            # Usa trading bot para comprar jogador
            from bot.trading import TradingBot
            from bot.anti_detection import AntiDetection
            
            # Cria instância temporária do trading bot
            # Nota: Requer config completo, mas pode usar config básico
            temp_config = {
                "trading": {
                    "enabled": True,
                    "use_futbin": False,  # Não usa Futbin para comfort trade
                    "platform": "pc",
                    "min_profit": 0,  # Aceita qualquer preço
                    "max_price": player_info.get("price", 1000000),
                    "search_interval": 1
                },
                "screen_resolution": {"width": 1920, "height": 1080},
                "logging": {"enabled": True, "level": "INFO"}
            }
            
            # Inicializa componentes necessários
            from bot.controller import Controller
            from bot.screen_capture import ScreenCapture
            from utils.logger import setup_logger
            
            logger = setup_logger(temp_config.get("logging", {}))
            controller = Controller(temp_config, logger)
            screen_capture = ScreenCapture(temp_config, logger)
            anti_detection = AntiDetection(temp_config, logger)
            
            trading_bot = TradingBot(temp_config, controller, screen_capture, logger, anti_detection)
            
            # Navega para Transfer Market
            if not trading_bot.navigate_to_transfer_market():
                self.logger.error("❌ Não foi possível navegar para Transfer Market")
                return False
            
            # Procura jogador com preço específico
            target_price = player_info.get("price", 0)
            screenshot = screen_capture.capture_screen()
            if screenshot is None:
                return False
            
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            # Procura jogador na tela
            from bot.real_detection import RealDetection
            real_detection = RealDetection(screen_capture, logger, controller)
            
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
                
                player_detected = real_detection.detect_player_in_market(player_region)
                
                if player_detected and player_detected.get("price"):
                    player_price = player_detected.get("price", 0)
                    
                    # Verifica se preço corresponde (margem de 5%)
                    price_tolerance = target_price * 0.05
                    if abs(player_price - target_price) <= price_tolerance:
                        # Encontrou! Compra jogador
                        player_x = (player_region[0] + player_region[2]) // 2
                        player_y = (player_region[1] + player_region[3]) // 2
                        
                        from bot.navigation import Navigation
                        nav = Navigation(controller, screen_capture, real_detection, logger)
                        
                        if nav.buy_player_at_position(player_x, player_y):
                            self.logger.info(f"✅ Jogador comprado por {player_price} coins")
                            return True
            
            self.logger.warning(f"⚠️  Jogador com preço {target_price} não encontrado")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao comprar jogador: {e}")
            return False
    
    def verify_companion_login(self):
        """Verifica se está logado no EA Companion"""
        try:
            self.logger.info("Verificando login no EA Companion...")
            
            # NOTA: Esta funcionalidade requer Appium configurado e funcionando
            # Por enquanto, retorna False para indicar que não está implementado
            self.logger.warning("⚠️  Transferência de coins via EA Companion requer Appium configurado")
            self.logger.warning("⚠️  Esta funcionalidade não está totalmente implementada")
            
            return False
            
        except Exception as e:
            self.logger.debug(f"Erro ao verificar login: {e}")
            return False
    
    def check_transfer_limits(self, amount):
        """Verifica limites de segurança antes de transferir"""
        try:
            # Limite diário
            if self.stats["coins_transferred_today"] + amount > self.max_transfer_per_day:
                self.logger.error(f"Limite diário excedido: {self.stats['coins_transferred_today']}/{self.max_transfer_per_day}")
                return False
            
            # Limite por transação
            if amount > self.max_transfer_per_transaction:
                self.logger.error(f"Valor excede limite por transação: {amount}/{self.max_transfer_per_transaction}")
                return False
            
            # Verifica anti-detecção
            if self.anti_detection:
                if not self.anti_detection.check_daily_limits("transfer"):
                    self.logger.warning("Limite diário de transferências atingido (anti-detecção)")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar limites: {e}")
            return False
    
    def get_stats(self):
        """Retorna estatísticas de transferências"""
        return self.stats.copy()
    
    def reset_daily_stats(self):
        """Reseta estatísticas diárias"""
        self.stats["transfers_today"] = 0
        self.stats["coins_transferred_today"] = 0
        self.logger.info("Estatísticas diárias resetadas")

