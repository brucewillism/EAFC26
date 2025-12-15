"""
Módulo de captura e análise de tela
"""

import cv2
import numpy as np
from PIL import Image
import pyautogui

class ScreenCapture:
    """Captura e analisa a tela do jogo"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.screen_res = config.get("screen_resolution", {})
        self.width = self.screen_res.get("width", 1920)
        self.height = self.screen_res.get("height", 1080)
        
    def capture_screen(self, region=None):
        """Captura a tela completa ou uma região"""
        try:
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            # Converte para numpy array para processamento
            img = np.array(screenshot)
            img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
            return img
        except Exception as e:
            self.logger.error(f"Erro ao capturar tela: {e}")
            return None
    
    def find_template(self, screenshot, template_path, threshold=0.8):
        """Encontra um template na captura de tela"""
        try:
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                self.logger.error(f"Template não encontrado: {template_path}")
                return None
            
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                # Retorna o centro do match
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                return (center_x, center_y, max_val)
            
            return None
        except Exception as e:
            self.logger.error(f"Erro ao procurar template: {e}")
            return None
    
    def find_color(self, screenshot, color_range_lower, color_range_upper):
        """Encontra uma cor específica na tela"""
        try:
            hsv = cv2.cvtColor(screenshot, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, color_range_lower, color_range_upper)
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            if contours:
                # Retorna o maior contorno
                largest = max(contours, key=cv2.contourArea)
                M = cv2.moments(largest)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    return (cx, cy)
            
            return None
        except Exception as e:
            self.logger.error(f"Erro ao procurar cor: {e}")
            return None
    
    def get_pixel_color(self, x, y):
        """Obtém a cor de um pixel específico"""
        try:
            screenshot = pyautogui.screenshot()
            pixel = screenshot.getpixel((x, y))
            return pixel
        except Exception as e:
            self.logger.error(f"Erro ao obter cor do pixel: {e}")
            return None
    
    def save_screenshot(self, filename, region=None):
        """Salva uma captura de tela"""
        try:
            screenshot = self.capture_screen(region)
            if screenshot is not None:
                cv2.imwrite(filename, screenshot)
                self.logger.debug(f"Screenshot salvo: {filename}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Erro ao salvar screenshot: {e}")
            return False
    
    def is_screen_ready(self, check_region=None):
        """Verifica se a tela está pronta (não está carregando)"""
        # Implementação básica - pode ser melhorada
        # Verifica se há movimento ou mudanças na tela
        screenshot1 = self.capture_screen(check_region)
        if screenshot1 is None:
            return False
        
        import time
        time.sleep(0.5)
        
        screenshot2 = self.capture_screen(check_region)
        if screenshot2 is None:
            return False
        
        # Compara as duas capturas
        diff = cv2.absdiff(screenshot1, screenshot2)
        mean_diff = np.mean(diff)
        
        # Se a diferença for muito pequena, a tela está estável
        return mean_diff < 5

