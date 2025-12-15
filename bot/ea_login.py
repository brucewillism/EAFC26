"""
Módulo de Login e Conexão com EA
"""

import time
import pyautogui
from bot.controller import Controller
from bot.screen_capture import ScreenCapture

class EALogin:
    """Gerencia login e conexão com servidor EA"""
    
    def __init__(self, config, controller, screen_capture, logger):
        self.config = config
        self.controller = controller
        self.screen_capture = screen_capture
        self.logger = logger
        
        self.login_config = config.get("login", {})
        self.email = self.login_config.get("email", "")
        self.password = self.login_config.get("password", "")
        self.auto_login = self.login_config.get("auto_login", False)
        
    def login(self):
        """Realiza login na EA"""
        try:
            self.logger.info("Iniciando processo de login na EA...")
            
            # Aguarda jogo carregar
            time.sleep(3)
            
            # Verifica se já está logado
            if self.is_logged_in():
                self.logger.info("Já está logado na EA")
                return True
            
            # Navega para tela de login se necessário
            if not self.navigate_to_login():
                self.logger.error("Não foi possível navegar para tela de login")
                return False
            
            # Preenche email
            if not self.enter_email():
                self.logger.error("Erro ao preencher email")
                return False
            
            # Preenche senha
            if not self.enter_password():
                self.logger.error("Erro ao preencher senha")
                return False
            
            # Clica em login
            if not self.click_login():
                self.logger.error("Erro ao clicar em login")
                return False
            
            # Aguarda login
            time.sleep(5)
            
            # Verifica se login foi bem-sucedido
            if self.is_logged_in():
                self.logger.info("Login realizado com sucesso!")
                return True
            else:
                self.logger.error("Login falhou")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro no processo de login: {e}")
            return False
    
    def navigate_to_login(self):
        """Navega para tela de login"""
        try:
            # Implementação básica - precisa ser calibrada
            # Pressiona ESC para voltar ao menu principal
            self.controller.press_key('esc')
            time.sleep(1)
            
            # Procura por botão de login ou menu
            # Coordenadas precisam ser calibradas
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao navegar para login: {e}")
            return False
    
    def enter_email(self):
        """Preenche campo de email"""
        try:
            if not self.email:
                self.logger.error("Email não configurado")
                return False
            
            # Clica no campo de email (coordenadas precisam ser calibradas)
            # self.controller.click(email_field_x, email_field_y)
            
            # Digita email
            self.controller.type_text(self.email, human_typing=True)
            time.sleep(0.5)
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao preencher email: {e}")
            return False
    
    def enter_password(self):
        """Preenche campo de senha"""
        try:
            if not self.password:
                self.logger.error("Senha não configurada")
                return False
            
            # Pressiona TAB para ir ao próximo campo
            self.controller.press_key('tab')
            time.sleep(0.5)
            
            # Digita senha
            self.controller.type_text(self.password, human_typing=True)
            time.sleep(0.5)
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao preencher senha: {e}")
            return False
    
    def click_login(self):
        """Clica no botão de login"""
        try:
            # Pressiona ENTER ou clica no botão de login
            # Coordenadas precisam ser calibradas
            # self.controller.click(login_button_x, login_button_y)
            self.controller.press_key('enter')
            time.sleep(1)
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao clicar em login: {e}")
            return False
    
    def is_logged_in(self):
        """Verifica se está logado usando detecção real"""
        try:
            # Usa detecção real para verificar se está logado
            from bot.real_detection import RealDetection
            real_detection = RealDetection(self.screen_capture, self.logger, self.controller)
            
            # Detecta tela atual
            current_screen = real_detection.detect_current_screen()
            
            # Se está em Ultimate Team ou menu principal, provavelmente está logado
            if current_screen in ["ultimate_team", "squad_battles", "transfer_market", "objectives"]:
                return True
            
            # Verifica se há texto indicando login (procura por "Ultimate Team" ou similar)
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return False
            
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            # Região superior onde geralmente aparece nome do usuário ou menu
            top_region = (screen_width//4, 0, screen_width*3//4, screen_height//4)
            text = real_detection.read_text_from_region(top_region, config='--psm 7')
            
            if text:
                text_lower = text.lower()
                # Procura indicadores de que está logado
                login_indicators = ["ultimate team", "my club", "squad", "transfer", "objectives"]
                if any(indicator in text_lower for indicator in login_indicators):
                    return True
            
            # Verifica se há botão de login (indica que NÃO está logado)
            if "login" in text_lower or "entrar" in text_lower or "sign in" in text_lower:
                return False
            
            # Se não encontrou nada, assume que não está logado (mais seguro)
            return False
            
        except Exception as e:
            self.logger.debug(f"Erro ao verificar login: {e}")
            return False
    
    def navigate_to_ultimate_team(self):
        """Navega para Ultimate Team usando navegação inteligente"""
        try:
            self.logger.info("Navegando para Ultimate Team...")
            
            # Usa navegação inteligente
            from bot.navigation import Navigation
            from bot.real_detection import RealDetection
            
            real_detection = RealDetection(self.screen_capture, self.logger, self.controller)
            navigation = Navigation(self.controller, self.screen_capture, real_detection, self.logger)
            
            # Usa método de navegação já implementado
            return navigation.navigate_to_ultimate_team()
            
        except Exception as e:
            self.logger.error(f"Erro ao navegar para Ultimate Team: {e}")
            return False

