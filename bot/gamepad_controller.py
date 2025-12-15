"""
Módulo de Controle de Gamepad - Emula gamepad Xbox/PS4 com movimentos humanos
"""

import time
import random
import math
import logging

try:
    import vgamepad as vg
    VGAMEPAD_AVAILABLE = True
except ImportError:
    VGAMEPAD_AVAILABLE = False
    logging.warning("vgamepad não disponível. Instale com: pip install vgamepad")

try:
    import pyvjoy
    PYVJOY_AVAILABLE = True
except ImportError:
    PYVJOY_AVAILABLE = False

class GamepadController:
    """Controla gamepad virtual com movimentos humanos e anti-detecção"""
    
    def __init__(self, config, logger, anti_detection=None):
        self.config = config
        self.logger = logger
        self.anti_detection = anti_detection
        
        # Tenta inicializar vgamepad (preferido)
        self.gamepad = None
        self.use_vgamepad = False
        
        if VGAMEPAD_AVAILABLE:
            try:
                self.gamepad = vg.VX360Gamepad()
                self.use_vgamepad = True
                self.logger.info("✅ Gamepad virtual inicializado (vgamepad)")
            except Exception as e:
                self.logger.warning(f"Erro ao inicializar vgamepad: {e}")
        
        if not self.use_vgamepad:
            self.logger.warning("⚠️ Gamepad virtual não disponível. Usando fallback.")
        
        # Configurações de delays
        self.safety = config.get("safety", {})
        self.human_config = config.get("human_behavior", {})
        
        # Delays específicos por contexto
        self.delays = {
            "in_game": (0.05, 0.2),      # 50 a 200ms in-game
            "menu_navigation": (1.0, 4.0), # 1 a 4s menus
            "button_press": (0.05, 0.15),  # 50 a 150ms para botões
            "analog_movement": (0.05, 0.2) # 50 a 200ms para analógico
        }
        
        # Estado do analógico
        self.analog_state = {
            "left_x": 0.0,   # -1.0 a 1.0
            "left_y": 0.0,   # -1.0 a 1.0
            "right_x": 0.0,  # -1.0 a 1.0
            "right_y": 0.0   # -1.0 a 1.0
        }
        
        # Configuração de oscilação do analógico
        self.analog_oscillation = {
            "enabled": True,
            "min_degrees": 1.0,   # Oscilação mínima
            "max_degrees": 5.0,   # Oscilação máxima
            "frequency": 0.1      # Frequência de oscilação
        }
        
        # Último movimento do analógico
        self.last_analog_time = 0
        
    def _human_delay(self, context="in_game"):
        """Aplica delay humano baseado no contexto"""
        if context not in self.delays:
            context = "in_game"
        
        min_delay, max_delay = self.delays[context]
        
        # Usa distribuição gaussiana para parecer mais humano
        delay = random.gauss(
            (min_delay + max_delay) / 2,
            (max_delay - min_delay) / 4
        )
        
        # Limita aos extremos
        delay = max(min_delay, min(max_delay, delay))
        
        # Adiciona micro-variações
        delay += random.uniform(-0.01, 0.01)
        
        time.sleep(delay)
    
    def _add_analog_oscillation(self, direction_degrees, intensity=1.0):
        """
        Adiciona oscilação aleatória ao vetor do analógico
        
        Args:
            direction_degrees: Direção desejada em graus (0-360)
            intensity: Intensidade do movimento (0.0 a 1.0)
            
        Returns:
            (x, y) com oscilação aplicada
        """
        if not self.analog_oscillation["enabled"]:
            # Sem oscilação, retorna direção pura
            rad = math.radians(direction_degrees)
            return (math.cos(rad) * intensity, math.sin(rad) * intensity)
        
        # Adiciona oscilação aleatória (1-5 graus)
        oscillation = random.uniform(
            self.analog_oscillation["min_degrees"],
            self.analog_oscillation["max_degrees"]
        )
        
        # Direção da oscilação (aleatória)
        oscillation_direction = random.uniform(0, 360)
        
        # Aplica oscilação
        final_direction = direction_degrees + math.cos(math.radians(oscillation_direction)) * oscillation
        
        # Converte para radianos
        rad = math.radians(final_direction)
        
        # Retorna coordenadas com intensidade
        x = math.cos(rad) * intensity
        y = math.sin(rad) * intensity
        
        return (x, y)
    
    def move_analog_left(self, direction_degrees, intensity=1.0, duration=None):
        """
        Move o analógico esquerdo com oscilação humana
        
        Args:
            direction_degrees: Direção em graus (0=Direita, 90=Baixo, 180=Esquerda, 270=Cima)
            intensity: Intensidade do movimento (0.0 a 1.0)
            duration: Duração do movimento em segundos (None = instantâneo)
        """
        try:
            if not self.use_vgamepad or not self.gamepad:
                self.logger.warning("Gamepad não disponível para movimento analógico")
                return False
            
            # Adiciona oscilação
            x, y = self._add_analog_oscillation(direction_degrees, intensity)
            
            # Limita valores entre -1.0 e 1.0
            x = max(-1.0, min(1.0, x))
            y = max(-1.0, min(1.0, y))
            
            # Aplica movimento
            self.gamepad.left_joystick_float(x_value_float=x, y_value_float=y)
            self.gamepad.update()
            
            # Atualiza estado
            self.analog_state["left_x"] = x
            self.analog_state["left_y"] = y
            
            # Se duration especificado, mantém movimento
            if duration:
                time.sleep(duration)
                # Retorna ao centro
                self.gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
                self.gamepad.update()
                self.analog_state["left_x"] = 0.0
                self.analog_state["left_y"] = 0.0
            else:
                # Delay humano antes de atualizar
                self._human_delay("analog_movement")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao mover analógico esquerdo: {e}")
            return False
    
    def move_analog_right(self, direction_degrees, intensity=1.0, duration=None):
        """Move o analógico direito com oscilação humana"""
        try:
            if not self.use_vgamepad or not self.gamepad:
                return False
            
            x, y = self._add_analog_oscillation(direction_degrees, intensity)
            x = max(-1.0, min(1.0, x))
            y = max(-1.0, min(1.0, y))
            
            self.gamepad.right_joystick_float(x_value_float=x, y_value_float=y)
            self.gamepad.update()
            
            self.analog_state["right_x"] = x
            self.analog_state["right_y"] = y
            
            if duration:
                time.sleep(duration)
                self.gamepad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
                self.gamepad.update()
                self.analog_state["right_x"] = 0.0
                self.analog_state["right_y"] = 0.0
            else:
                self._human_delay("analog_movement")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao mover analógico direito: {e}")
            return False
    
    def press_button(self, button, duration=0.1, context="in_game"):
        """
        Pressiona um botão do gamepad
        
        Args:
            button: Nome do botão ('A', 'B', 'X', 'Y', 'LB', 'RB', 'LT', 'RT', 'BACK', 'START')
            duration: Tempo que o botão fica pressionado
            context: Contexto para delay ('in_game' ou 'menu_navigation')
        """
        try:
            if not self.use_vgamepad or not self.gamepad:
                self.logger.warning("Gamepad não disponível")
                return False
            
            # Delay antes de pressionar
            self._human_delay(context)
            
            # Mapeia botões
            button_map = {
                'A': self.gamepad.press_button,
                'B': self.gamepad.press_button,
                'X': self.gamepad.press_button,
                'Y': self.gamepad.press_button,
                'LB': self.gamepad.press_button,
                'RB': self.gamepad.press_button,
                'BACK': self.gamepad.press_button,
                'START': self.gamepad.press_button,
            }
            
            # Mapeia para constantes do vgamepad
            vg_buttons = {
                'A': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
                'B': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
                'X': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
                'Y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
                'LB': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
                'RB': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
                'BACK': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
                'START': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            }
            
            if button not in vg_buttons:
                self.logger.warning(f"Botão '{button}' não reconhecido")
                return False
            
            # Pressiona botão
            self.gamepad.press_button(vg_buttons[button])
            self.gamepad.update()
            
            # Mantém pressionado
            time.sleep(duration)
            
            # Solta botão
            self.gamepad.release_button(vg_buttons[button])
            self.gamepad.update()
            
            # Delay após soltar
            self._human_delay(context)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao pressionar botão {button}: {e}")
            return False
    
    def press_trigger(self, trigger, value, context="in_game"):
        """
        Pressiona trigger (gatilho) do gamepad
        
        Args:
            trigger: 'LT' (esquerdo) ou 'RT' (direito)
            value: Valor de 0.0 a 1.0
            context: Contexto para delay
        """
        try:
            if not self.use_vgamepad or not self.gamepad:
                return False
            
            self._human_delay(context)
            
            value = max(0.0, min(1.0, value))
            
            if trigger == 'LT':
                self.gamepad.left_trigger_float(value_float=value)
            elif trigger == 'RT':
                self.gamepad.right_trigger_float(value_float=value)
            else:
                return False
            
            self.gamepad.update()
            self._human_delay(context)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao pressionar trigger {trigger}: {e}")
            return False
    
    def release_all(self):
        """Solta todos os botões e retorna analógicos ao centro"""
        try:
            if not self.use_vgamepad or not self.gamepad:
                return False
            
            # Retorna analógicos ao centro
            self.gamepad.left_joystick_float(x_value_float=0.0, y_value_float=0.0)
            self.gamepad.right_joystick_float(x_value_float=0.0, y_value_float=0.0)
            
            # Solta todos os botões
            self.gamepad.reset()
            self.gamepad.update()
            
            # Reseta estado
            self.analog_state = {
                "left_x": 0.0,
                "left_y": 0.0,
                "right_x": 0.0,
                "right_y": 0.0
            }
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao soltar todos os controles: {e}")
            return False
    
    def should_make_error(self):
        """Verifica se deve cometer erro (1-3% de chance)"""
        if self.anti_detection:
            return self.anti_detection.should_make_error()
        return random.random() < 0.02  # 2% padrão
    
    def cancel_action(self):
        """Cancela ação atual (simula hesitação)"""
        self.release_all()
        time.sleep(random.uniform(0.1, 0.3))
        return True
    
    def move_left_stick(self, direction_degrees, intensity=1.0, duration=0.0):
        """Move o analógico esquerdo (alias para move_analog_left)"""
        return self.move_analog_left(direction_degrees, intensity, duration)
    
    def move_right_stick(self, direction_degrees, intensity=1.0, duration=0.0):
        """Move o analógico direito (alias para move_analog_right)"""
        return self.move_analog_right(direction_degrees, intensity, duration)

