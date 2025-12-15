"""
EA FC 26 Bot - Main Entry Point
Bot automatizado para farming de coins no EA FC 26
"""

import json
import sys
import time
import keyboard
from pathlib import Path

from bot.controller import Controller
from bot.screen_capture import ScreenCapture
from bot.trading import TradingBot
from bot.squad_battles import SquadBattlesBot
from bot.objectives import ObjectivesBot
from bot.anti_detection import AntiDetection
from bot.adaptive_system import AdaptiveSystem
from bot.ea_login import EALogin
from bot.team_manager import TeamManager
from utils.logger import setup_logger
from utils.risk_scanner import RiskScanner

class EAFCBot:
    def __init__(self, config_path="config.json"):
        """Inicializa o bot principal"""
        self.config = self.load_config(config_path)
        self.logger = setup_logger(self.config.get("logging", {}))
        self.running = False
        self.paused = False
        self.risk_report = None
        
        # Inicializa sistema adaptativo PRIMEIRO (controla tudo)
        # Antes do adaptativo, aplica mitigação de risco e hard caps
        self.config, self.risk_report = RiskScanner.apply_mitigations(self.config, logger=self.logger)

        self.adaptive_system = AdaptiveSystem(self.config, self.logger)
        
        # Inicializa sistema anti-detecção (usa parâmetros adaptativos)
        self.anti_detection = AntiDetection(self.config, self.logger, self.adaptive_system)
        
        # Inicializa componentes
        self.controller = Controller(self.config, self.logger, self.anti_detection)
        self.screen_capture = ScreenCapture(self.config, self.logger)
        
        # Inicializa gamepad (se disponível)
        try:
            from bot.gamepad_controller import GamepadController
            self.gamepad = GamepadController(self.config, self.logger, self.anti_detection)
            if self.gamepad.use_vgamepad:
                self.logger.info("✅ Gamepad virtual inicializado e pronto para uso")
            else:
                self.logger.warning("⚠️ Gamepad não disponível. Usando teclado como fallback.")
                self.gamepad = None
        except Exception as e:
            self.logger.warning(f"⚠️ Erro ao inicializar gamepad: {e}. Usando teclado como fallback.")
            self.gamepad = None
        
        # Inicializa login EA
        self.ea_login = EALogin(self.config, self.controller, self.screen_capture, self.logger)
        
        # Inicializa gerenciador de time
        self.team_manager = TeamManager(self.config, self.controller, self.screen_capture, self.logger)
        
        # Inicializa módulos
        self.trading_bot = TradingBot(self.config, self.controller, self.screen_capture, self.logger, self.anti_detection)
        self.squad_battles_bot = SquadBattlesBot(self.config, self.controller, self.screen_capture, self.logger, self.anti_detection, gamepad=self.gamepad)
        self.objectives_bot = ObjectivesBot(self.config, self.controller, self.screen_capture, self.logger, team_manager=self.team_manager)
        
        # Inicializa Comfort Trade (se habilitado)
        self.comfort_trade = None
        if self.config.get("comfort_trade", {}).get("enabled", False):
            try:
                from bot.comfort_trade import ComfortTrade
                self.comfort_trade = ComfortTrade(self.config, self.controller, self.screen_capture, self.logger, self.anti_detection)
                self.logger.warning("⚠️  Comfort Trade inicializado - RISCOS ALTOS!")
            except Exception as e:
                self.logger.error(f"Erro ao inicializar Comfort Trade: {e}")
        
        # Passa referência do bot para os módulos que precisam verificar se está rodando
        self.squad_battles_bot.bot_instance = self
        self.squad_battles_bot.game_logic.bot_instance = self
        
        # Configura hotkeys
        self.setup_hotkeys()
        
    def load_config(self, config_path):
        """Carrega configurações do arquivo JSON"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Arquivo de configuração {config_path} não encontrado!")
            sys.exit(1)
        except json.JSONDecodeError:
            print(f"Erro ao ler {config_path}. Verifique o formato JSON.")
            sys.exit(1)
    
    def setup_hotkeys(self):
        """Configura as hotkeys de controle"""
        safety = self.config.get("safety", {})
        
        pause_key = safety.get("pause_hotkey", "f9")
        stop_key = safety.get("stop_hotkey", "f10")
        exit_key = safety.get("emergency_exit", "esc")
        
        keyboard.on_press_key(pause_key, lambda _: self.toggle_pause())
        keyboard.on_press_key(stop_key, lambda _: self.stop())
        keyboard.on_press_key(exit_key, lambda _: self.emergency_exit())
        
        self.logger.info(f"Hotkeys configuradas: {pause_key.upper()} (Pausar), {stop_key.upper()} (Parar), {exit_key.upper()} (Sair)")
    
    def toggle_pause(self):
        """Pausa ou retoma o bot"""
        self.paused = not self.paused
        status = "PAUSADO" if self.paused else "RETOMADO"
        self.logger.warning(f"Bot {status}")
        print(f"\n[{status}] Pressione {self.config['safety']['pause_hotkey'].upper()} novamente para {'retomar' if self.paused else 'pausar'}")
    
    def stop(self):
        """Para o bot completamente"""
        self.running = False
        self.logger.warning("Bot parado pelo usuário")
        print("\n[PARADO] Bot interrompido pelo usuário")
    
    def emergency_exit(self):
        """Sai do programa imediatamente"""
        self.logger.critical("Saída de emergência ativada!")
        print("\n[EMERGÊNCIA] Saindo do programa...")
        sys.exit(0)
    
    def check_prerequisites(self):
        """Verifica pré-requisitos antes de executar"""
        try:
            # 1. Verifica se pelo menos um módulo está habilitado
            trading_enabled = self.config.get("trading", {}).get("enabled", False)
            sb_enabled = self.config.get("squad_battles", {}).get("enabled", False)
            obj_enabled = self.config.get("objectives", {}).get("enabled", False)
            
            if not (trading_enabled or sb_enabled or obj_enabled):
                self.logger.error("Nenhum módulo habilitado no config.json")
                return False
            
            # 2. Verifica se consegue capturar tela
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                self.logger.error("Não consegue capturar tela. Jogo pode não estar aberto.")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar pré-requisitos: {e}")
            return False
    
    def run(self):
        """Loop principal do bot com sistema anti-detecção"""
        self.running = True
        self.logger.info("=" * 50)
        self.logger.info("EA FC 26 Bot iniciado - MODO ANTI-DETECÇÃO ATIVO")
        self.logger.info("=" * 50)
        print("\n" + "=" * 50)
        print("EA FC 26 BOT INICIADO - SISTEMA ADAPTATIVO ATIVO")
        print("=" * 50)
        print("[ADAPTATIVO] Sistema adaptativo: Ajusta automaticamente a mudancas de deteccao")
        print(f"[PERFIL] Perfil atual: {self.adaptive_system.get_current_profile()}")
        print(f"[RISCO] Nivel de risco: {self.adaptive_system.get_current_risk_level()}")
        print(f"Pressione {self.config['safety']['pause_hotkey'].upper()} para pausar/retomar")
        print(f"Pressione {self.config['safety']['stop_hotkey'].upper()} para parar")
        print(f"Pressione {self.config['safety']['emergency_exit'].upper()} para sair")
        print("=" * 50 + "\n")

        # Mostra avaliação de risco
        if self.risk_report:
            reasons = ", ".join(self.risk_report.get("reasons", [])) or "sem alertas"
            suggestions = "; ".join(self.risk_report.get("suggestions", []))
            print(f"[RISK] Nível: {self.risk_report.get('risk', 'unknown')}")
            print(f"[RISK] Motivos: {reasons}")
            if suggestions:
                print(f"[RISK] Sugestões: {suggestions}")
        
        try:
            # Verifica pré-requisitos ANTES de começar
            if not self.check_prerequisites():
                self.logger.error("Pré-requisitos não atendidos. Bot não pode continuar.")
                print("\n❌ PRÉ-REQUISITOS NÃO ATENDIDOS!")
                print("💡 Execute: python diagnostico_bot.py para mais detalhes")
                return
            
            # Realiza login se necessário
            if self.config.get("login", {}).get("auto_login", False):
                if not self.ea_login.login():
                    self.logger.error("Falha no login. Bot não pode continuar.")
                    return
                
                # Navega para Ultimate Team
                if not self.ea_login.navigate_to_ultimate_team():
                    self.logger.warning("Não foi possível navegar para Ultimate Team")
                    print("\n⚠️  ATENÇÃO: Não foi possível navegar para Ultimate Team")
                    print("💡 Certifique-se que:")
                    print("   - O jogo está aberto e visível")
                    print("   - Você está na tela principal")
                    print("   - Execute: python calibrar_automatico.py")
                
                # Verifica se time existe (IMPORTANTE!)
                self.logger.info("Verificando se time existe na conta...")
                from bot.real_detection import RealDetection
                real_detection = RealDetection(self.screen_capture, self.logger, self.controller)
                team_exists = real_detection.check_team_exists()
                
                # Verifica qual conta está sendo usada
                account_type = self.config.get("account", {}).get("type", "main")
                account_name = "principal" if account_type == "main" else "secundária"
                
                if not team_exists:
                    self.logger.warning(f"⚠️  TIME NÃO ENCONTRADO NA CONTA {account_name.upper()}!")
                    print(f"\n⚠️  ATENÇÃO: Time não encontrado na conta {account_name}!")
                    print("💡 O bot precisa de um time criado para funcionar:")
                    print("   - Trading: Precisa de time para acessar Transfer Market")
                    print("   - Squad Battles: Precisa de time para jogar")
                    print("   - Objetivos: Precisa de time para completar")
                    print("\n📝 SOLUÇÃO:")
                    print("   1. Crie um time manualmente no jogo")
                    print("   2. Ou habilite 'auto_create' no config.json (recomendado)")
                    
                    # Se auto_create está habilitado, tenta criar
                    if self.config.get("team", {}).get("auto_create", False):
                        self.logger.info("Tentando criar time automaticamente...")
                        print("🔄 Tentando criar time automaticamente...")
                    else:
                        self.logger.warning("Continuando sem time (pode falhar nas ações)")
                        print("⚠️  Continuando sem time - algumas ações podem falhar")
                else:
                    self.logger.info(f"✅ Time encontrado na conta {account_name}! Bot pode funcionar normalmente")
                
                # Verifica e cria time se necessário
                if self.config.get("team", {}).get("auto_create", False):
                    if not self.team_manager.check_and_create_team():
                        self.logger.warning("Não foi possível verificar/criar time, continuando...")
            
            while self.running:
                if not self.paused:
                    # Monitora e adapta continuamente
                    self.adaptive_system.monitor_and_adapt()
                    
                    # Verifica se deve fazer pausa longa (anti-detecção)
                    if self.anti_detection.should_take_break():
                        break_duration = self.anti_detection.take_break()
                        self.logger.warning(f"Pausa anti-deteccao: {break_duration/60:.1f} minutos")
                        print(f"\n[PAUSA] PAUSA ANTI-DETECCAO: {break_duration/60:.1f} minutos")
                        print("Simulando comportamento humano - jogador fazendo pausa\n")
                        time.sleep(break_duration)
                        # Reseta sessão após pausa
                        self.anti_detection.session_start = time.time()
                    
                    # Verifica limites diários e horários
                    if self.anti_detection.should_avoid_action():
                        self.logger.info("Evitando ação (horário de pico ou limite atingido)")
                        time.sleep(60)  # Aguarda 1 minuto
                        continue
                    
                    # Verifica se deve parar antes de executar módulos
                    if not self.running:
                        break
                    
                    # Executa módulos ativos com verificação de limites
                    if self.config.get("trading", {}).get("enabled", False):
                        if not self.running:
                            break
                        if self.anti_detection.check_daily_limits("trade"):
                            self.trading_bot.run_cycle()
                    
                    if not self.running:
                        break
                    
                    if self.config.get("squad_battles", {}).get("enabled", False):
                        if not self.running:
                            break
                        if self.anti_detection.check_daily_limits("match"):
                            self.squad_battles_bot.run_cycle()
                        else:
                            self.logger.warning("Limite diário de partidas atingido. Aguardando...")
                            # Aguarda com verificação de parada
                            for _ in range(60):  # 60 iterações de 5 segundos = 5 minutos
                                if not self.running:
                                    break
                                time.sleep(5)
                    
                    if not self.running:
                        break
                    
                    if self.config.get("objectives", {}).get("enabled", False):
                        if not self.running:
                            break
                        self.objectives_bot.run_cycle()
                    
                    if not self.running:
                        break
                    
                    # Comfort Trade (executa apenas uma vez quando habilitado)
                    if self.comfort_trade and self.config.get("comfort_trade", {}).get("enabled", False):
                        if not self.running:
                            break
                        self.logger.warning("⚠️  Executando Comfort Trade - RISCOS ALTOS!")
                        if self.comfort_trade.execute_comfort_trade():
                            self.logger.info("✅ Comfort Trade concluído!")
                            # Desabilita após execução (segurança)
                            self.config["comfort_trade"]["enabled"] = False
                            self.logger.warning("⚠️  Comfort Trade desabilitado após execução (segurança)")
                        else:
                            self.logger.error("❌ Erro ao executar Comfort Trade")
                    
                    if not self.running:
                        break
                    
                    # Delay variado entre ciclos (anti-detecção + adaptativo)
                    base_delay = self.anti_detection.get_human_like_delay("general")
                    delay_multiplier = self.adaptive_system.get_adaptive_parameters("delay_multiplier") or 1.0
                    delay = base_delay * delay_multiplier
                    
                    # Aguarda com verificação periódica de parada
                    elapsed = 0
                    check_interval = 0.5  # Verifica a cada 0.5s
                    while elapsed < delay and self.running:
                        time.sleep(min(check_interval, delay - elapsed))
                        elapsed += check_interval
                else:
                    time.sleep(0.5)
                    
        except KeyboardInterrupt:
            self.logger.info("Interrupção pelo usuário (Ctrl+C)")
        except Exception as e:
            self.logger.error(f"Erro no loop principal: {e}", exc_info=True)
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Limpeza ao encerrar"""
        # Registra resultado da sessão no sistema adaptativo
        if hasattr(self, 'adaptive_system'):
            # Calcula estatísticas da sessão
            session_success = True  # Assume sucesso se chegou até aqui
            warnings = 0  # Pode ser incrementado se houver avisos
            
            self.adaptive_system.register_session_result(session_success, warnings)
            
            # Mostra estatísticas de adaptação
            stats = self.adaptive_system.get_adaptation_stats()
            self.logger.info(f"Estatísticas de adaptação: {stats}")
        
        self.logger.info("Encerrando bot...")
        print("\n[FINALIZANDO] Bot encerrado com sucesso")
        
        # Mostra resumo se sistema adaptativo estiver ativo
        if hasattr(self, 'adaptive_system'):
            print(f"[PERFIL] Perfil final: {self.adaptive_system.get_current_profile()}")
            print(f"[RISCO] Nivel de risco final: {self.adaptive_system.get_current_risk_level()}")
            print(f"[ADAPTACOES] Adaptacoes realizadas: {stats.get('adaptation_count', 0)}")

if __name__ == "__main__":
    bot = EAFCBot()
    bot.run()

