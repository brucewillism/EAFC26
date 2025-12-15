"""
Sistema de Recuperação de Erros - Lida com erros comuns e recupera o bot
"""

import time
import cv2
import numpy as np

class ErrorRecovery:
    """Sistema que detecta e recupera de erros comuns"""
    
    def __init__(self, controller, screen_capture, real_detection, logger):
        self.controller = controller
        self.screen_capture = screen_capture
        self.real_detection = real_detection
        self.logger = logger
        
        # Contadores de erros
        self.error_counts = {
            "navigation_failed": 0,
            "player_not_found": 0,
            "purchase_failed": 0,
            "screen_not_detected": 0
        }
        
        # Limites antes de tentar recuperação
        self.error_limits = {
            "navigation_failed": 3,
            "player_not_found": 5,
            "purchase_failed": 3,
            "screen_not_detected": 3
        }
    
    def detect_error_screen(self):
        """
        Detecta se está em uma tela de erro
        
        Returns:
            str: Tipo de erro detectado ou None
        """
        try:
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return None
            
            # Lê texto de regiões comuns de erro
            error_regions = [
                (400, 400, 1520, 500),  # Centro da tela
                (400, 500, 1520, 600),  # Centro inferior
            ]
            
            error_keywords = {
                "no_coins": ["not enough", "insufficient", "sem coins", "coins insuficientes"],
                "player_sold": ["already sold", "já vendido", "sold out"],
                "connection_error": ["connection", "conexão", "error", "erro"],
                "timeout": ["timeout", "tempo esgotado"],
                "server_error": ["server", "servidor", "unavailable", "indisponível"]
            }
            
            for region in error_regions:
                text = self.real_detection.read_text_from_region(region)
                if text:
                    text_lower = text.lower()
                    for error_type, keywords in error_keywords.items():
                        if any(keyword in text_lower for keyword in keywords):
                            self.logger.warning(f"⚠️ Erro detectado: {error_type}")
                            return error_type
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Erro ao detectar tela de erro: {e}")
            return None
    
    def handle_error(self, error_type, context=None):
        """
        Lida com um erro específico
        
        Args:
            error_type: Tipo de erro
            context: Contexto adicional do erro
            
        Returns:
            bool: True se erro foi recuperado
        """
        try:
            self.logger.info(f"🔧 Tentando recuperar de erro: {error_type}")
            
            # Incrementa contador
            if error_type in self.error_counts:
                self.error_counts[error_type] += 1
            
            # Ações de recuperação baseadas no tipo de erro
            if error_type == "no_coins":
                return self._handle_no_coins()
            elif error_type == "player_sold":
                return self._handle_player_sold()
            elif error_type == "connection_error":
                return self._handle_connection_error()
            elif error_type == "navigation_failed":
                return self._handle_navigation_failed()
            elif error_type == "screen_not_detected":
                return self._handle_screen_not_detected()
            else:
                # Recuperação genérica
                return self._handle_generic_error()
                
        except Exception as e:
            self.logger.error(f"Erro ao tentar recuperar: {e}")
            return False
    
    def _handle_no_coins(self):
        """Lida com erro de coins insuficientes"""
        try:
            self.logger.warning("💰 Coins insuficientes. Fechando diálogo...")
            # Fecha diálogo de erro
            self.controller.press_key('esc')
            time.sleep(1)
            self.controller.press_key('esc')
            time.sleep(1)
            return True
        except:
            return False
    
    def _handle_player_sold(self):
        """Lida com erro de jogador já vendido"""
        try:
            self.logger.warning("⏭️ Jogador já vendido. Continuando...")
            self.controller.press_key('esc')
            time.sleep(1)
            return True
        except:
            return False
    
    def _handle_connection_error(self):
        """Lida com erro de conexão"""
        try:
            self.logger.warning("🌐 Erro de conexão. Aguardando...")
            time.sleep(5)
            # Tenta voltar ao menu
            self.controller.press_key('esc')
            time.sleep(2)
            self.controller.press_key('esc')
            time.sleep(2)
            return True
        except:
            return False
    
    def _handle_navigation_failed(self):
        """Lida com falha de navegação"""
        try:
            self.logger.warning("🧭 Falha na navegação. Tentando voltar ao menu...")
            # Volta ao menu principal
            for _ in range(3):
                self.controller.press_key('esc')
                time.sleep(1)
            return True
        except:
            return False
    
    def _handle_screen_not_detected(self):
        """Lida com tela não detectada"""
        try:
            self.logger.warning("📺 Tela não detectada. Aguardando carregamento...")
            time.sleep(3)
            # Tenta detectar novamente
            current_screen = self.real_detection.detect_current_screen()
            if current_screen != "unknown":
                return True
            return False
        except:
            return False
    
    def _handle_generic_error(self):
        """Recuperação genérica para erros desconhecidos"""
        try:
            self.logger.warning("⚠️ Erro genérico. Tentando recuperar...")
            # Fecha diálogos
            self.controller.press_key('esc')
            time.sleep(1)
            # Aguarda um pouco
            time.sleep(2)
            return True
        except:
            return False
    
    def check_and_recover(self):
        """
        Verifica se há erros e tenta recuperar
        
        Returns:
            bool: True se recuperou ou não havia erro
        """
        try:
            # Detecta erro na tela
            error_type = self.detect_error_screen()
            
            if error_type:
                return self.handle_error(error_type)
            
            return True
            
        except Exception as e:
            self.logger.debug(f"Erro ao verificar recuperação: {e}")
            return True
    
    def reset_error_counters(self):
        """Reseta contadores de erro"""
        for key in self.error_counts:
            self.error_counts[key] = 0
        self.logger.info("Contadores de erro resetados")
    
    def get_error_stats(self):
        """Retorna estatísticas de erros"""
        return self.error_counts.copy()

