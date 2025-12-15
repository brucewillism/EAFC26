"""
Modo Sem Captura de Tela - Usa EA Companion App e Futbin
Funcionalidades limitadas, mas não precisa do jogo aberto
"""

import time
from bot.base_module import BaseModule
from bot.appium_automation import EACompanionAutomation
from bot.futbin_integration import FutbinIntegration

class ModoSemCaptura(BaseModule):
    """
    Modo que funciona sem captura de tela do jogo
    Usa EA Companion App e Futbin
    """
    
    def __init__(self, config, logger):
        super().__init__(config, None, None, logger)
        self.config = config
        self.logger = logger
        
        # Inicializa EA Companion App
        self.companion = EACompanionAutomation(logger)
        self.companion_connected = False
        
        # Inicializa Futbin
        self.futbin = FutbinIntegration(logger)
        
        # Estatísticas
        self.stats = {
            "trades_via_app": 0,
            "coins_earned": 0,
            "opportunities_found": 0
        }
    
    def connect_companion(self):
        """Conecta ao EA Companion App (usa sessão existente se já estiver logado)"""
        try:
            if self.companion.connect():
                self.companion_connected = True
                self.logger.info("✅ Conectado ao EA Companion App!")
                
                # Verifica se já está logado
                if self.companion.is_logged_in():
                    self.logger.info("✅ App já está logado! Usando sessão existente.")
                    self.logger.info("💡 Não precisa fazer login - pode usar direto!")
                    return True
                else:
                    self.logger.warning("⚠️  App não está logado.")
                    self.logger.info("💡 Opções:")
                    self.logger.info("   1. Faça login manualmente no app")
                    self.logger.info("   2. Ou configure email/senha no config.json")
                    # Tenta fazer login se tiver credenciais
                    login_config = self.config.get("login", {})
                    email = login_config.get("email")
                    password = login_config.get("password")
                    if email and password:
                        self.logger.info("🔐 Tentando fazer login automaticamente...")
                        if self.companion.login(email, password):
                            return True
                    return False
            else:
                self.logger.warning("⚠️  Não foi possível conectar ao EA Companion App")
                return False
        except Exception as e:
            self.logger.error(f"Erro ao conectar: {e}")
            return False
    
    def trading_via_app(self):
        """
        Faz trading usando apenas o EA Companion App
        Não precisa do jogo aberto!
        """
        try:
            if not self.companion_connected:
                if not self.connect_companion():
                    return False
            
            self.logger.info("💰 Iniciando trading via EA Companion App...")
            
            # 1. Verifica mercado no app
            market_data = self.companion.check_transfer_market()
            if not market_data:
                self.logger.warning("Não foi possível acessar mercado no app")
                return False
            
            # 2. Analisa oportunidades usando Futbin
            opportunities = self.futbin.find_market_opportunities()
            
            if not opportunities:
                self.logger.info("Nenhuma oportunidade encontrada no Futbin")
                return False
            
            # 3. Tenta comprar via app (limitado)
            bought = 0
            for opp in opportunities[:5]:  # Limita a 5 por ciclo
                player_name = opp.get("name")
                max_price = opp.get("max_buy_price", 0)
                
                self.logger.info(f"Tentando comprar {player_name} por até {max_price}...")
                
                # Tenta comprar via app
                if self.companion.buy_player(player_name, max_price):
                    bought += 1
                    self.stats["trades_via_app"] += 1
                    self.logger.info(f"✅ Comprado: {player_name}")
                    time.sleep(5)  # Delay entre compras
                else:
                    self.logger.warning(f"❌ Não foi possível comprar {player_name}")
            
            self.logger.info(f"Trading via app concluído: {bought} jogadores comprados")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro no trading via app: {e}")
            return False
    
    def check_objectives_via_app(self):
        """
        Verifica objetivos usando EA Companion App
        Não precisa do jogo aberto!
        """
        try:
            if not self.companion_connected:
                if not self.connect_companion():
                    return False
            
            self.logger.info("🎯 Verificando objetivos via EA Companion App...")
            
            objectives = self.companion.get_objectives()
            
            if objectives:
                completed = 0
                for obj in objectives:
                    if not obj.get("completed", False):
                        # Tenta completar via app (se possível)
                        if self.companion.complete_objective(obj):
                            completed += 1
                            self.logger.info(f"✅ Objetivo completado: {obj.get('name')}")
                
                self.logger.info(f"Objetivos verificados: {completed} completados")
                return True
            else:
                self.logger.warning("Não foi possível obter objetivos do app")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao verificar objetivos: {e}")
            return False
    
    def transfer_coins_via_app(self, amount, target_email):
        """
        Transfere coins usando EA Companion App
        Não precisa do jogo aberto!
        """
        try:
            if not self.companion_connected:
                if not self.connect_companion():
                    return False
            
            self.logger.info(f"💸 Transferindo {amount} coins via EA Companion App...")
            
            # Usa método Comfort Trade via app
            if self.companion.transfer_coins(amount, target_email):
                self.logger.info(f"✅ Transferência concluída: {amount} coins")
                return True
            else:
                self.logger.warning("❌ Transferência falhou")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro na transferência: {e}")
            return False
    
    def run_cycle(self):
        """Executa um ciclo completo sem captura de tela"""
        try:
            self.logger.info("🚀 Iniciando ciclo sem captura de tela...")
            
            # 1. Conecta ao app
            if not self.companion_connected:
                if not self.connect_companion():
                    self.logger.warning("Não foi possível conectar ao app. Algumas funcionalidades estarão limitadas.")
                    return
            
            # 2. Trading via app
            trading_config = self.config.get("trading", {})
            if trading_config.get("enabled", False):
                self.trading_via_app()
            
            # 3. Objetivos via app
            objectives_config = self.config.get("objectives", {})
            if objectives_config.get("enabled", False):
                self.check_objectives_via_app()
            
            # 4. Transferência (se habilitada)
            transfer_config = self.config.get("coin_transfer", {})
            if transfer_config.get("enabled", False):
                target_email = transfer_config.get("secondary_account")
                amount = transfer_config.get("max_transfer_per_transaction", 50000)
                # self.transfer_coins_via_app(amount, target_email)  # Descomente se quiser
            
            self.logger.info("✅ Ciclo sem captura de tela concluído")
            
        except Exception as e:
            self.logger.error(f"Erro no ciclo sem captura: {e}")
        finally:
            # Não desconecta, mantém conexão para próximos ciclos
            pass
    
    def disconnect(self):
        """Desconecta do app"""
        try:
            if self.companion_connected:
                self.companion.disconnect()
                self.companion_connected = False
                self.logger.info("✅ Desconectado do EA Companion App")
        except Exception as e:
            self.logger.debug(f"Erro ao desconectar: {e}")

