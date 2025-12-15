"""
Lógica de jogo inteligente para garantir vitórias
Com estratégias específicas: passes curtos, posse de bola, "cera"
"""

import time
import random
import cv2
import numpy as np
import math

class GameLogic:
    """Lógica de jogo que garante vitórias com estratégias específicas"""
    
    def __init__(self, controller, screen_capture, logger, config, bot_instance=None, gamepad=None):
        self.controller = controller
        self.screen_capture = screen_capture
        self.logger = logger
        self.config = config.get("game_logic", {})
        self.bot_instance = bot_instance
        
        # Usa gamepad passado ou tenta inicializar um novo
        if gamepad is not None:
            self.gamepad = gamepad
            self.use_gamepad = getattr(gamepad, 'use_vgamepad', False)
            if self.use_gamepad:
                self.logger.info("✅ Gamepad disponível - usando controles de gamepad")
            else:
                self.logger.warning("⚠️ Gamepad não disponível - usando fallback de teclado")
        else:
            # Tenta inicializar gamepad
            try:
                from bot.gamepad_controller import GamepadController
                self.gamepad = GamepadController(config, logger, None)
                self.use_gamepad = getattr(self.gamepad, 'use_vgamepad', False)
                if self.use_gamepad:
                    self.logger.info("✅ Gamepad disponível - usando controles de gamepad")
                else:
                    self.logger.warning("⚠️ Gamepad não disponível - usando fallback de teclado")
            except Exception as e:
                self.logger.warning(f"Erro ao inicializar gamepad: {e}")
                self.gamepad = None
                self.use_gamepad = False
        
        # Estratégias de jogo
        self.aggressive_mode = self.config.get("aggressive_mode", True)
        self.defensive_mode = self.config.get("defensive_mode", False)
        self.min_goals_ahead = self.config.get("min_goals_ahead", 2)
        
        # Estado do jogo
        self.game_state = {
            "score_us": 0,
            "score_opponent": 0,
            "possession": 50,
            "time_elapsed": 0,  # Em minutos
            "is_attacking": False,
            "is_defending": False,
            "has_ball": False
        }
        
        # Mapeamento de botões do gamepad (EA FC padrão)
        self.gamepad_controls = {
            "pass": "X",              # X no Xbox, Square no PS
            "through_pass": "Y",     # Y no Xbox, Triangle no PS
            "shoot": "B",            # B no Xbox, Circle no PS
            "sprint": "RT",          # Trigger direito
            "skill_move": "RB",      # Bumper direito (PROIBIDO 4-5 estrelas)
            "tackle": "X",           # X no Xbox
            "contain": "A",          # A no Xbox, X no PS
            "slide_tackle": "B",     # B no Xbox
            "clear": "Y",            # Y no Xbox
            "call_player": "LB"      # Bumper esquerdo
        }
        
        # Controles de fallback (teclado)
        self.keyboard_controls = {
            "pass": "x",
            "through_pass": "q",
            "shoot": "c",
            "sprint": "shift",
            "skill_move": "space",
            "tackle": "x",
            "contain": "a",
            "slide_tackle": "s",
            "clear": "c",
            "call_player": "q"
        }
        
        # Flag para proibir skill moves 4-5 estrelas
        self.prohibit_skill_moves = True
        
    def _get_delay(self, context="in_game"):
        """Retorna delay apropriado baseado no contexto"""
        if context == "in_game":
            return random.uniform(0.05, 0.2)  # 50-200ms
        elif context == "menu":
            return random.uniform(1.0, 4.0)  # 1-4s
        else:
            return random.uniform(0.05, 0.2)
    
    def _press_button(self, button, context="in_game"):
        """Pressiona botão usando gamepad ou teclado"""
        if self.use_gamepad and self.gamepad:
            return self.gamepad.press_button(button, duration=0.1, context=context)
        else:
            # Fallback para teclado
            key = self.keyboard_controls.get(button, button)
            self.controller.press_key(key, human_timing=True)
            self._get_delay(context)
            return True
    
    def _move_analog(self, direction_degrees, intensity=0.7, duration=None):
        """Move analógico esquerdo com oscilação"""
        if self.use_gamepad and self.gamepad:
            return self.gamepad.move_analog_left(direction_degrees, intensity, duration)
        else:
            # Fallback: simula com teclas WASD
            # Mapeia direção para teclas
            if 315 <= direction_degrees or direction_degrees < 45:
                self.controller.press_key("d")  # Direita
            elif 45 <= direction_degrees < 135:
                self.controller.press_key("s")  # Baixo
            elif 135 <= direction_degrees < 225:
                self.controller.press_key("a")  # Esquerda
            else:
                self.controller.press_key("w")  # Cima
            
            if duration:
                time.sleep(duration)
            else:
                self._get_delay("in_game")
            return True
    
    def update_game_state(self, screenshot=None):
        """Atualiza o estado do jogo analisando a tela"""
        try:
            if screenshot is None:
                screenshot = self.screen_capture.capture_screen()
            
            # Detecta placar (implementar OCR)
            # Por enquanto, mantém valores atuais
            
            # Detecta minuto do jogo (implementar OCR)
            # self.detect_game_minute(screenshot)
            
            # Detecta fase
            self.detect_phase(screenshot)
            
        except Exception as e:
            self.logger.error(f"Erro ao atualizar estado do jogo: {e}")
    
    def detect_phase(self, screenshot):
        """Detecta se está atacando ou defendendo"""
        try:
            score_us = self.game_state.get("score_us", 0)
            score_opponent = self.game_state.get("score_opponent", 0)
            
            if score_us > score_opponent:
                self.game_state["is_attacking"] = False
                self.game_state["is_defending"] = True
            else:
                self.game_state["is_attacking"] = True
                self.game_state["is_defending"] = False
                
        except Exception as e:
            self.logger.debug(f"Erro ao detectar fase: {e}")
    
    def detect_game_minute(self, screenshot):
        """Detecta minuto do jogo usando OCR"""
        try:
            # Região onde aparece o tempo (geralmente canto superior)
            # TODO: Implementar OCR para ler minuto
            # Por enquanto, estima baseado em tempo decorrido
            pass
        except Exception as e:
            self.logger.debug(f"Erro ao detectar minuto: {e}")
    
    def play_offensive(self):
        """
        Joga de forma ofensiva com estratégia específica:
        - Passes curtos e rasteiros
        - Sem skill moves 4-5 estrelas
        - Chutes simples dentro da área
        """
        try:
            self.logger.debug("⚽ Modo ofensivo ativado")
            
            # Verifica se deve cometer erro (1-3% chance)
            if random.random() < 0.02:  # 2% chance
                self.logger.debug("❌ Erro simulado: hesitação")
                time.sleep(random.uniform(0.1, 0.3))
                return True
            
            # 1. Passa a bola (passe curto e rasteiro)
            # Passe curto = botão X pressionado brevemente
            self._press_button(self.gamepad_controls["pass"], "in_game")
            self._get_delay("in_game")
            
            # 2. Move jogador em direção ao gol (com oscilação)
            # Direção aleatória mas geralmente para frente
            direction = random.uniform(0, 45)  # 0-45 graus (direita/frente)
            self._move_analog(direction, intensity=0.6)
            
            # 3. Se está perto do gol, chuta (30% chance)
            if random.random() < 0.3:
                self._press_button(self.gamepad_controls["shoot"], "in_game")
                self._get_delay("in_game")
            
            # 4. Usa sprint ocasionalmente (40% chance)
            if random.random() < 0.4:
                if self.use_gamepad and self.gamepad:
                    self.gamepad.press_trigger("RT", 0.8, "in_game")
                else:
                    self.controller.press_key("shift")
                self._get_delay("in_game")
            
            # NUNCA usa skill moves 4-5 estrelas (proibido)
            # Apenas movimentos básicos de corpo
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro no modo ofensivo: {e}")
            return False
    
    def play_defensive(self):
        """Joga de forma defensiva"""
        try:
            self.logger.debug("🛡️ Modo defensivo ativado")
            
            # Contém o adversário
            self._press_button(self.gamepad_controls["contain"], "in_game")
            self._get_delay("in_game")
            
            # Tenta roubar a bola (50% chance)
            if random.random() < 0.5:
                self._press_button(self.gamepad_controls["tackle"], "in_game")
                self._get_delay("in_game")
            
            # Se pressionado, chuta para longe (30% chance)
            if random.random() < 0.3:
                self._press_button(self.gamepad_controls["clear"], "in_game")
                self._get_delay("in_game")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro no modo defensivo: {e}")
            return False
    
    def play_possession_extreme(self):
        """
        Estratégia de posse de bola extrema (após 2+ gols de vantagem):
        - Prioriza passes na defesa e meio-campo
        - Não busca ataque ativamente
        - Mantém posse de bola
        """
        try:
            self.logger.info("🎯 Modo: Posse de Bola Extrema (2+ gols de vantagem)")
            
            # 1. Passa para trás/lateral (não para frente)
            # Escolhe direção que não avança muito
            directions = [180, 225, 135, 270, 90]  # Esquerda, diagonal esquerda/baixo, etc.
            direction = random.choice(directions)
            
            # 2. Passa a bola (passe curto)
            self._press_button(self.gamepad_controls["pass"], "in_game")
            self._get_delay("in_game")
            
            # 3. Move jogador para manter posse (movimento lateral/para trás)
            self._move_analog(direction, intensity=0.4)  # Intensidade menor = mais controle
            
            # 4. Aguarda antes de passar novamente (paciência)
            time.sleep(random.uniform(0.5, 1.5))
            
            # 5. Passa novamente (troca de passes)
            if random.random() < 0.7:  # 70% chance de passar novamente
                self._press_button(self.gamepad_controls["pass"], "in_game")
                self._get_delay("in_game")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na posse de bola extrema: {e}")
            return False
    
    def play_time_wasting(self):
        """
        Estratégia "cera" (minuto 80+):
        - Mantém posse de bola
        - Move bola lateralmente
        - Consome tempo
        """
        try:
            self.logger.info("⏰ Modo: Cera (80+ minutos)")
            
            # 1. Move bola lateralmente (esquerda/direita)
            lateral_directions = [90, 270]  # Esquerda ou direita
            direction = random.choice(lateral_directions)
            
            # 2. Move analógico lateralmente
            self._move_analog(direction, intensity=0.3, duration=random.uniform(1.0, 2.0))
            
            # 3. Passa lateralmente (se necessário)
            if random.random() < 0.4:  # 40% chance
                self._press_button(self.gamepad_controls["pass"], "in_game")
                self._get_delay("in_game")
            
            # 4. Mantém posse sem avançar
            # Move para trás se pressionado
            if random.random() < 0.3:
                self._move_analog(180, intensity=0.2, duration=0.5)  # Para trás
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro na estratégia de cera: {e}")
            return False
    
    def ensure_victory(self):
        """Garante que está ganhando com estratégias específicas"""
        try:
            score_us = self.game_state.get("score_us", 0) or 0
            score_opponent = self.game_state.get("score_opponent", 0) or 0
            time_elapsed = self.game_state.get("time_elapsed", 0) or 0
            
            # Converte para int
            try:
                score_us = int(score_us)
                score_opponent = int(score_opponent)
                time_elapsed = int(time_elapsed)
            except (ValueError, TypeError):
                score_us = 0
                score_opponent = 0
                time_elapsed = 0
            
            goal_difference = score_us - score_opponent
            
            # Estratégia baseada no minuto do jogo
            if time_elapsed >= 80:
                # Minuto 80+: Estratégia "cera"
                return self.play_time_wasting()
            
            # Estratégia baseada na vantagem
            if goal_difference >= self.min_goals_ahead:
                # 2+ gols de vantagem: Posse de bola extrema
                if random.random() < 0.8:  # 80% do tempo
                    return self.play_possession_extreme()
                else:
                    return self.play_defensive()
            elif goal_difference < 0:
                # Perdendo: Joga ofensivo
                return self.play_offensive()
            elif goal_difference == 0:
                # Empatado: Joga ofensivo para fazer gol
                return self.play_offensive()
            else:
                # 1 gol de vantagem: Balanceado
                if self.game_state.get("is_attacking", False):
                    return self.play_offensive()
                else:
                    return self.play_defensive()
                    
        except Exception as e:
            self.logger.error(f"Erro ao garantir vitória: {e}")
            return self.play_offensive()
    
    def play_match_intelligently(self, match_duration_seconds):
        """Joga a partida de forma inteligente com todas as estratégias"""
        try:
            self.logger.info("🎮 Iniciando jogo inteligente com gamepad...")
            
            start_time = time.time()
            elapsed = 0
            last_action_time = 0
            action_interval = random.uniform(0.5, 1.5)  # Ações mais frequentes (50-200ms delays)
            
            while elapsed < match_duration_seconds:
                # Verifica se bot foi parado
                if self.bot_instance and not self.bot_instance.running:
                    self.logger.warning("Bot parado durante partida")
                    break
                
                current_time = time.time()
                elapsed = current_time - start_time
                self.game_state["time_elapsed"] = int(elapsed / 60)  # Converte para minutos
                
                # Atualiza estado periodicamente
                if elapsed - last_action_time >= action_interval:
                    if self.bot_instance and not self.bot_instance.running:
                        break
                    
                    self.update_game_state()
                    self.ensure_victory()
                    
                    last_action_time = elapsed
                    action_interval = random.uniform(0.5, 1.5)
                
                # Delay curto entre iterações (50-200ms)
                time.sleep(random.uniform(0.05, 0.2))
            
            # Retorna resultado
            return {
                "result": "completed",
                "score": f"{self.game_state.get('score_us', 0)}-{self.game_state.get('score_opponent', 0)}",
                "won": (self.game_state.get("score_us", 0) or 0) > (self.game_state.get("score_opponent", 0) or 0),
                "goals_scored": self.game_state.get("score_us", 0) or 0,
                "goals_conceded": self.game_state.get("score_opponent", 0) or 0
            }
            
        except Exception as e:
            self.logger.error(f"Erro ao jogar partida: {e}")
            return {"result": "error"}
