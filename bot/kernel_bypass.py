"""
Módulo de Bypass de Kernel - Técnicas avançadas para evitar detecção em nível de kernel
"""

import time
import random
import ctypes
from ctypes import wintypes
import threading

class KernelBypass:
    """Técnicas avançadas para evitar detecção em nível de kernel"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.kernel_config = config.get("kernel_bypass", {})
        
        # Windows API para input mais "humano"
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
        # Flags para input mais natural
        self.enabled = self.kernel_config.get("enabled", True)
        self.use_hardware_simulation = self.kernel_config.get("use_hardware_simulation", True)
        self.add_jitter = self.kernel_config.get("add_jitter", True)
        
        # Variação de timing em nível de sistema
        self.timing_variation = self.kernel_config.get("timing_variation", True)
        self.min_system_delay = self.kernel_config.get("min_system_delay", 0.001)  # 1ms
        self.max_system_delay = self.kernel_config.get("max_system_delay", 0.005)  # 5ms
        
        # Histórico de eventos do sistema
        self.event_history = []
        self.max_history = 1000
        
        # Thread para simular atividade de background (torna menos suspeito)
        self.background_activity = self.kernel_config.get("background_activity", True)
        self.background_thread = None
        if self.background_activity:
            self.start_background_activity()
    
    def start_background_activity(self):
        """Inicia atividade de background para parecer mais humano"""
        def background_worker():
            while True:
                # Simula atividade ocasional de mouse (movimentos muito pequenos)
                if random.random() < 0.1:  # 10% chance
                    try:
                        current_pos = self.get_cursor_pos()
                        # Move 1-3 pixels aleatoriamente (micro-movimentos)
                        new_x = current_pos[0] + random.randint(-3, 3)
                        new_y = current_pos[1] + random.randint(-3, 3)
                        self.move_cursor_smooth(new_x, new_y, duration=0.01)
                    except:
                        pass
                
                # Aguarda entre 5-30 segundos
                time.sleep(random.uniform(5, 30))
        
        if self.background_thread is None or not self.background_thread.is_alive():
            self.background_thread = threading.Thread(target=background_worker, daemon=True)
            self.background_thread.start()
            self.logger.debug("Atividade de background iniciada")
    
    def get_cursor_pos(self):
        """Obtém posição atual do cursor"""
        class POINT(ctypes.Structure):
            _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]
        
        point = POINT()
        self.user32.GetCursorPos(ctypes.byref(point))
        return (point.x, point.y)
    
    def add_system_jitter(self):
        """Adiciona jitter em nível de sistema (torna menos detectável)"""
        if not self.add_jitter:
            return
        
        # Pequeno delay aleatório em nível de sistema
        jitter = random.uniform(self.min_system_delay, self.max_system_delay)
        time.sleep(jitter)
    
    def move_cursor_smooth(self, x, y, duration=0.1):
        """Move cursor de forma suave usando Windows API diretamente"""
        if not self.use_hardware_simulation:
            return False
        
        try:
            start_pos = self.get_cursor_pos()
            start_x, start_y = start_pos
            
            # Calcula número de steps baseado na distância
            distance = ((x - start_x)**2 + (y - start_y)**2)**0.5
            steps = max(5, int(distance / 2))
            
            # Move em steps suaves com jitter
            for i in range(steps + 1):
                t = i / steps
                # Curva suave (ease-in-out)
                eased_t = t * t * (3 - 2 * t)
                
                # Posição interpolada
                current_x = int(start_x + (x - start_x) * eased_t)
                current_y = int(start_y + (y - start_y) * eased_t)
                
                # Adiciona micro-jitter
                if self.add_jitter:
                    jitter_x = random.randint(-1, 1)
                    jitter_y = random.randint(-1, 1)
                    current_x += jitter_x
                    current_y += jitter_y
                
                # Move usando SetCursorPos (mais "hardware-like")
                self.user32.SetCursorPos(current_x, current_y)
                
                # Delay entre steps com variação
                if i < steps:
                    step_delay = (duration / steps) * random.uniform(0.8, 1.2)
                    self.add_system_jitter()
                    time.sleep(step_delay)
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao mover cursor: {e}")
            return False
    
    def send_mouse_input(self, x, y, button='left', action='click'):
        """Envia input de mouse usando Windows API (mais difícil de detectar)"""
        if not self.enabled:
            return False
        
        try:
            # Move cursor primeiro
            if action == 'click':
                self.move_cursor_smooth(x, y, duration=random.uniform(0.1, 0.3))
                self.add_system_jitter()
            
            # Define flags do mouse
            MOUSEEVENTF_LEFTDOWN = 0x0002
            MOUSEEVENTF_LEFTUP = 0x0004
            MOUSEEVENTF_RIGHTDOWN = 0x0008
            MOUSEEVENTF_RIGHTUP = 0x0010
            
            if button == 'left':
                down_flag = MOUSEEVENTF_LEFTDOWN
                up_flag = MOUSEEVENTF_LEFTUP
            else:
                down_flag = MOUSEEVENTF_RIGHTDOWN
                up_flag = MOUSEEVENTF_RIGHTUP
            
            # Envia evento de mouse usando SendInput (mais "humano")
            class MOUSEINPUT(ctypes.Structure):
                _fields_ = [
                    ("dx", wintypes.LONG),
                    ("dy", wintypes.LONG),
                    ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
                ]
            
            class INPUT(ctypes.Structure):
                class _INPUT(ctypes.Union):
                    _fields_ = [("mi", MOUSEINPUT)]
                _anonymous_ = ("_input",)
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("_input", _INPUT)
                ]
            
            # Cria input de mouse down
            mouse_down = INPUT()
            mouse_down.type = 0  # INPUT_MOUSE
            mouse_down.mi.dx = 0
            mouse_down.mi.dy = 0
            mouse_down.mi.dwFlags = down_flag
            mouse_down.mi.time = 0
            mouse_down.mi.dwExtraInfo = None
            
            # Cria input de mouse up
            mouse_up = INPUT()
            mouse_up.type = 0
            mouse_up.mi.dx = 0
            mouse_up.mi.dy = 0
            mouse_up.mi.dwFlags = up_flag
            mouse_up.mi.time = 0
            mouse_up.mi.dwExtraInfo = None
            
            # Envia eventos
            inputs = (INPUT * 2)(mouse_down, mouse_up)
            
            # Adiciona jitter antes de enviar
            self.add_system_jitter()
            
            # SendInput com timing variável
            self.user32.SendInput(2, inputs, ctypes.sizeof(INPUT))
            
            # Delay após clique
            time.sleep(random.uniform(0.01, 0.05))
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar input de mouse: {e}")
            return False
    
    def send_keyboard_input(self, key_code, press=True):
        """Envia input de teclado usando Windows API"""
        if not self.enabled:
            return False
        
        try:
            KEYEVENTF_KEYUP = 0x0002
            
            class KEYBDINPUT(ctypes.Structure):
                _fields_ = [
                    ("wVk", wintypes.WORD),
                    ("wScan", wintypes.WORD),
                    ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD),
                    ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG))
                ]
            
            class INPUT(ctypes.Structure):
                class _INPUT(ctypes.Union):
                    _fields_ = [("ki", KEYBDINPUT)]
                _anonymous_ = ("_input",)
                _fields_ = [
                    ("type", wintypes.DWORD),
                    ("_input", _INPUT)
                ]
            
            # Cria input de teclado
            keyboard_input = INPUT()
            keyboard_input.type = 1  # INPUT_KEYBOARD
            keyboard_input.ki.wVk = key_code
            keyboard_input.ki.wScan = 0
            keyboard_input.ki.dwFlags = 0 if press else KEYEVENTF_KEYUP
            keyboard_input.ki.time = 0
            keyboard_input.ki.dwExtraInfo = None
            
            inputs = (INPUT * 1)(keyboard_input)
            
            # Adiciona jitter
            self.add_system_jitter()
            
            # SendInput
            self.user32.SendInput(1, inputs, ctypes.sizeof(INPUT))
            
            return True
        except Exception as e:
            self.logger.error(f"Erro ao enviar input de teclado: {e}")
            return False
    
    def add_timing_noise(self, base_delay):
        """Adiciona ruído de timing (torna menos detectável)"""
        if not self.timing_variation:
            return base_delay
        
        # Adiciona variação baseada em distribuição normal
        noise = random.gauss(0, base_delay * 0.1)  # 10% de variação
        noisy_delay = base_delay + noise
        
        # Limita aos extremos
        return max(0, noisy_delay)
    
    def simulate_human_hesitation(self):
        """Simula hesitação humana (micro-pausas)"""
        # Humanos hesitam ocasionalmente
        if random.random() < 0.15:  # 15% chance
            hesitation = random.uniform(0.05, 0.2)
            time.sleep(hesitation)
    
    def get_adaptive_delay(self, base_delay, context="general"):
        """Retorna delay adaptativo com ruído"""
        # Delay base
        delay = base_delay
        
        # Adiciona ruído de timing
        delay = self.add_timing_noise(delay)
        
        # Adiciona hesitação ocasional
        if random.random() < 0.1:  # 10% chance
            delay += random.uniform(0.1, 0.3)
        
        return delay

