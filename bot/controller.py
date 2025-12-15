"""
Módulo de controle de mouse e teclado com movimentos humanos
"""

import time
import random
import math
import pyautogui
import keyboard
from pynput import mouse, keyboard as kb

class Controller:
    """Controla mouse e teclado para interagir com o jogo de forma humana"""
    
    def __init__(self, config, logger, anti_detection=None):
        self.config = config
        self.logger = logger
        self.anti_detection = anti_detection  # Sistema anti-detecção
        
        # Tenta importar kernel bypass (opcional)
        try:
            from bot.kernel_bypass import KernelBypass
            self.kernel_bypass = KernelBypass(config, logger)
            self.use_kernel_bypass = config.get("kernel_bypass", {}).get("enabled", False)
        except Exception as e:
            self.logger.debug(f"Kernel bypass não disponível: {e}")
            self.kernel_bypass = None
            self.use_kernel_bypass = False
        
        self.safety = config.get("safety", {})
        self.human_config = config.get("human_behavior", {})
        
        # Configurações de segurança do pyautogui
        # FAILSAFE desabilitado para evitar interrupções quando mouse vai para canto
        # ATENÇÃO: Mantenha o bot monitorado quando em uso
        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0.05  # Reduzido para movimentos mais suaves
        
        # Delays aleatórios
        self.random_delays = self.safety.get("random_delays", True)
        self.min_delay = self.safety.get("min_delay", 0.3)
        self.max_delay = self.safety.get("max_delay", 1.5)
        
        # Comportamento humano
        self.occasional_pauses = self.human_config.get("occasional_pauses", True)
        self.pause_probability = self.human_config.get("pause_probability", 0.05)  # 5% chance
        self.pause_duration_min = self.human_config.get("pause_duration_min", 2.0)
        self.pause_duration_max = self.human_config.get("pause_duration_max", 8.0)
        
        # Movimentos de mouse humanos
        self.human_mouse_movements = self.human_config.get("human_mouse_movements", True)
        self.mouse_curve_intensity = self.human_config.get("mouse_curve_intensity", 0.3)
        
        # Última ação para evitar repetição
        self.last_action_time = 0
        
    def random_delay(self, base_min=None, base_max=None, context="general"):
        """Adiciona um delay aleatório entre ações com variação humana e anti-detecção"""
        if self.random_delays:
            # Usa sistema anti-detecção se disponível
            if self.anti_detection:
                delay = self.anti_detection.get_human_like_delay(context)
            else:
                min_delay = base_min if base_min is not None else self.min_delay
                max_delay = base_max if base_max is not None else self.max_delay
                
                # Adiciona variação mais natural (distribuição normal)
                delay = random.gauss(
                    (min_delay + max_delay) / 2,
                    (max_delay - min_delay) / 4
                )
                delay = max(min_delay, min(max_delay, delay))  # Limita aos extremos
            
            time.sleep(delay)
            
            # Micro-pausas anti-detecção
            if self.anti_detection:
                self.anti_detection.add_micro_pauses()
            
            # Pausa ocasional (simula distração humana)
            if self.occasional_pauses and random.random() < self.pause_probability:
                pause_time = random.uniform(self.pause_duration_min, self.pause_duration_max)
                self.logger.debug(f"Pausa ocasional: {pause_time:.2f}s (comportamento humano)")
                time.sleep(pause_time)
    
    def human_mouse_move(self, start_x, start_y, end_x, end_y, duration=None):
        """Move o mouse de forma humana (com curvas suaves e anti-detecção)"""
        if not self.human_mouse_movements:
            return pyautogui.moveTo(end_x, end_y, duration=duration or 0.5)
        
        # Usa caminho aleatório do anti-detecção se disponível
        if self.anti_detection:
            points = self.anti_detection.randomize_mouse_path(start_x, start_y, end_x, end_y)
        else:
            # Calcula distância
            distance = math.sqrt((end_x - start_x)**2 + (end_y - start_y)**2)
            
            # Duração baseada na distância (mais natural)
            if duration is None:
                duration = min(0.8, max(0.2, distance / 1000))
            
            # Adiciona variação na duração
            duration *= random.uniform(0.8, 1.2)
            
            # Cria pontos intermediários com curva suave (bezier-like)
            steps = max(10, int(distance / 10))
            points = []
            
            for i in range(steps + 1):
                t = i / steps
                
                # Curva suave (ease-in-out)
                eased_t = t * t * (3 - 2 * t)
                
                # Adiciona pequena variação aleatória para parecer mais humano
                curve_offset = random.uniform(-self.mouse_curve_intensity, self.mouse_curve_intensity) * distance * 0.1
                
                x = start_x + (end_x - start_x) * eased_t + curve_offset * math.sin(t * math.pi)
                y = start_y + (end_y - start_y) * eased_t + curve_offset * math.cos(t * math.pi)
                
                points.append((int(x), int(y)))
        
        # Move através dos pontos com variação de intensidade
        intensity = self.anti_detection.vary_action_intensity() if self.anti_detection else 1.0
        total_duration = duration if duration else 0.5
        total_duration *= intensity
        
        step_duration = total_duration / len(points)
        for point in points:
            pyautogui.moveTo(point[0], point[1], duration=step_duration)
            time.sleep(step_duration * 0.1 * random.uniform(0.5, 1.5))  # Variação no delay
    
    def click(self, x, y, button='left', delay=True, human_movement=True):
        """Clica em uma coordenada com movimento humano e anti-detecção"""
        try:
            # Usa kernel bypass se disponível e habilitado
            if self.use_kernel_bypass and self.kernel_bypass:
                return self.kernel_bypass.send_mouse_input(x, y, button, 'click')
            
            # Verifica se deve cometer erro (anti-detecção)
            if self.anti_detection and self.anti_detection.should_make_error():
                error_type = self.anti_detection.get_error_type()
                if error_type == "miss_click":
                    # Erra o clique (clica perto mas não exatamente)
                    offset = self.anti_detection.get_click_offset()
                    x += offset[0] * 3  # Erro maior
                    y += offset[1] * 3
                    self.logger.debug(f"Erro simulado: miss_click em ({x}, {y})")
                elif error_type == "cancel_action":
                    # Cancela a ação (simula mudança de ideia)
                    self.logger.debug("Erro simulado: cancel_action")
                    time.sleep(random.uniform(0.2, 0.5))
                    return False
            
            if delay:
                # Usa tempo de reação variável
                if self.anti_detection:
                    reaction_time = self.anti_detection.get_reaction_time()
                    time.sleep(reaction_time)
                else:
                    self.random_delay()
            
            # Move o mouse de forma humana antes de clicar
            if human_movement:
                current_x, current_y = pyautogui.position()
                self.human_mouse_move(current_x, current_y, x, y)
                
                # Offset baseado em precisão (anti-detecção)
                if self.anti_detection:
                    offset = self.anti_detection.get_click_offset()
                    x += offset[0]
                    y += offset[1]
                else:
                    offset_x = random.randint(-2, 2)
                    offset_y = random.randint(-2, 2)
                    x += offset_x
                    y += offset_y
                
                pyautogui.moveTo(x, y, duration=0.1)
                
                # Tempo de reação variável
                if self.anti_detection:
                    time.sleep(self.anti_detection.get_reaction_time())
                else:
                    time.sleep(random.uniform(0.05, 0.15))
            
            pyautogui.click(x, y, button=button)
            self.logger.debug(f"Click em ({x}, {y}) com botão {button}")
            
            # Delay variado após clique
            if self.anti_detection:
                delay_time = self.anti_detection.get_varied_action_timing(
                    random.uniform(0.1, 0.3), "click"
                )
                time.sleep(delay_time)
            else:
                time.sleep(random.uniform(0.1, 0.3))
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao clicar: {e}")
            return False
    
    def double_click(self, x, y, delay=True, human_movement=True):
        """Duplo clique em uma coordenada com movimento humano"""
        try:
            if delay:
                self.random_delay()
            
            # Move o mouse de forma humana antes de clicar
            if human_movement:
                current_x, current_y = pyautogui.position()
                self.human_mouse_move(current_x, current_y, x, y)
                time.sleep(random.uniform(0.05, 0.15))
            
            pyautogui.doubleClick(x, y)
            self.logger.debug(f"Duplo clique em ({x}, {y})")
            
            # Pequeno delay após clique
            time.sleep(random.uniform(0.1, 0.3))
            
            return True
        except Exception as e:
            self.logger.error(f"Erro no duplo clique: {e}")
            return False
    
    def right_click(self, x, y, delay=True):
        """Clique direito em uma coordenada"""
        return self.click(x, y, button='right', delay=delay)
    
    def move_to(self, x, y, duration=None, human=True):
        """Move o mouse para uma coordenada de forma humana"""
        try:
            if human:
                current_x, current_y = pyautogui.position()
                self.human_mouse_move(current_x, current_y, x, y, duration)
            else:
                if duration is None:
                    duration = 0.5
                pyautogui.moveTo(x, y, duration=duration)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao mover mouse: {e}")
            return False
    
    def type_text(self, text, interval=None, human_typing=True):
        """Digita texto com velocidade humana variável"""
        try:
            self.random_delay(0.2, 0.5)
            
            if human_typing:
                # Intervalo variável entre caracteres (mais humano)
                if interval is None:
                    interval = random.uniform(0.08, 0.25)
                
                # Digita caractere por caractere com variação
                for char in text:
                    pyautogui.write(char, interval=0)
                    # Variação no tempo entre caracteres
                    time.sleep(interval + random.uniform(-0.03, 0.05))
                    
                    # Ocasionalmente "pausa" mais tempo (simula pensamento)
                    if random.random() < 0.1:  # 10% chance
                        time.sleep(random.uniform(0.2, 0.5))
            else:
                if interval is None:
                    interval = 0.1
                pyautogui.write(text, interval=interval)
            
            self.logger.debug(f"Texto digitado: {text}")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao digitar: {e}")
            return False
    
    def press_key(self, key, presses=1, interval=None, human_timing=True):
        """Pressiona uma tecla com timing humano e anti-detecção"""
        try:
            # Verifica se deve errar a tecla (anti-detecção)
            if self.anti_detection and self.anti_detection.should_make_error():
                if self.anti_detection.get_error_type() == "wrong_key":
                    # Pressiona tecla errada e corrige
                    wrong_key = random.choice(['a', 's', 'd', 'w', 'q', 'e'])
                    pyautogui.press(wrong_key)
                    time.sleep(random.uniform(0.1, 0.3))
                    self.logger.debug(f"Erro simulado: wrong_key ({wrong_key}), corrigindo para {key}")
            
            if human_timing:
                if self.anti_detection:
                    reaction_time = self.anti_detection.get_reaction_time()
                    time.sleep(reaction_time)
                else:
                    self.random_delay(0.1, 0.3)
            
            # Intervalo entre teclas mais humano
            if interval is None:
                if self.anti_detection:
                    interval = self.anti_detection.get_varied_action_timing(
                        random.uniform(0.08, 0.25) if presses > 1 else 0.1,
                        "key_press"
                    )
                else:
                    interval = random.uniform(0.08, 0.25) if presses > 1 else 0.1
            
            # Pressiona cada tecla individualmente para mais controle
            for i in range(presses):
                # Ocasionalmente "erra" a tecla (anti-detecção)
                actual_key = key
                if self.anti_detection and self.anti_detection.should_miss_key() and i == 0:
                    # Erra mas corrige imediatamente
                    wrong_key = random.choice(['a', 's', 'd', 'w'])
                    pyautogui.press(wrong_key)
                    time.sleep(0.05)
                    actual_key = key
                
                pyautogui.press(actual_key)
                if i < presses - 1:  # Não espera após a última tecla
                    sleep_time = interval + random.uniform(-0.02, 0.02)
                    if self.anti_detection:
                        sleep_time = self.anti_detection.get_varied_action_timing(
                            sleep_time, "key_interval"
                        )
                    time.sleep(sleep_time)
            
            self.logger.debug(f"Tecla pressionada: {key} ({presses}x)")
            
            # Delay variado após pressionar
            if human_timing:
                if self.anti_detection:
                    delay_time = self.anti_detection.get_varied_action_timing(
                        random.uniform(0.05, 0.15), "key_after"
                    )
                    time.sleep(delay_time)
                else:
                    time.sleep(random.uniform(0.05, 0.15))
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao pressionar tecla: {e}")
            return False
    
    def key_combination(self, *keys):
        """Pressiona combinação de teclas"""
        try:
            self.random_delay()
            pyautogui.hotkey(*keys)
            self.logger.debug(f"Combinação de teclas: {'+'.join(keys)}")
            return True
        except Exception as e:
            self.logger.error(f"Erro na combinação de teclas: {e}")
            return False
    
    def scroll(self, x, y, clicks=3, direction='down'):
        """Rola a tela"""
        try:
            self.random_delay()
            if direction == 'down':
                pyautogui.scroll(-clicks, x=x, y=y)
            else:
                pyautogui.scroll(clicks, x=x, y=y)
            self.logger.debug(f"Scroll {direction} em ({x}, {y})")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao rolar: {e}")
            return False
    
    def wait_for_image(self, image_path, timeout=10, confidence=0.8):
        """Aguarda uma imagem aparecer na tela"""
        try:
            location = pyautogui.locateOnScreen(image_path, timeout=timeout, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                self.logger.debug(f"Imagem encontrada: {image_path} em {center}")
                return center
            return None
        except pyautogui.ImageNotFoundException:
            self.logger.debug(f"Imagem não encontrada: {image_path}")
            return None
        except Exception as e:
            self.logger.error(f"Erro ao procurar imagem: {e}")
            return None
    
    def find_image(self, image_path, confidence=0.8):
        """Procura uma imagem na tela"""
        try:
            location = pyautogui.locateOnScreen(image_path, confidence=confidence)
            if location:
                center = pyautogui.center(location)
                return center
            return None
        except pyautogui.ImageNotFoundException:
            return None
        except Exception as e:
            self.logger.error(f"Erro ao procurar imagem: {e}")
            return None
    
    def get_screen_size(self):
        """Retorna o tamanho da tela"""
        return pyautogui.size()
    
    def screenshot(self, region=None):
        """Tira uma captura de tela"""
        try:
            if region:
                return pyautogui.screenshot(region=region)
            return pyautogui.screenshot()
        except Exception as e:
            self.logger.error(f"Erro ao capturar tela: {e}")
            return None

