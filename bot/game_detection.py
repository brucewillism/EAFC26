"""
Módulo de Detecção de Jogo - Detecta informações reais do jogo
"""

import cv2
import numpy as np
import pytesseract
from PIL import Image
import re

class GameDetection:
    """Detecta informações reais do jogo usando OCR e análise de imagem"""
    
    def __init__(self, screen_capture, logger):
        self.screen_capture = screen_capture
        self.logger = logger
        
        # Configuração do Tesseract (OCR)
        # Descomente e ajuste o caminho se necessário:
        try:
            # Tenta usar Tesseract do PATH primeiro
            pytesseract.get_tesseract_version()
        except:
            # Se não encontrar, tenta caminho padrão do Windows
            try:
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            except:
                self.logger.warning("Tesseract OCR não encontrado. Detecção de texto desabilitada.")
        
    def detect_score(self, screenshot=None):
        """Detecta placar da partida"""
        try:
            if screenshot is None:
                screenshot = self.screen_capture.capture_screen()
            
            # Região onde geralmente aparece o placar (ajustar conforme necessário)
            # Exemplo: centro superior da tela
            height, width = screenshot.shape[:2]
            score_region = screenshot[50:150, width//2-100:width//2+100]
            
            # Converte para escala de cinza
            gray = cv2.cvtColor(score_region, cv2.COLOR_BGR2GRAY)
            
            # Aplica threshold
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # Tenta ler com OCR
            try:
                text = pytesseract.image_to_string(thresh, config='--psm 8 -c tessedit_char_whitelist=0123456789-')
                # Procura padrão de placar (ex: "2-1")
                score_match = re.search(r'(\d+)[-:](\d+)', text)
                if score_match:
                    score_us = int(score_match.group(1))
                    score_opponent = int(score_match.group(2))
                    return {"us": score_us, "opponent": score_opponent}
            except:
                pass
            
            return None
        except Exception as e:
            self.logger.debug(f"Erro ao detectar placar: {e}")
            return None
    
    def detect_team_names(self, screenshot=None):
        """Detecta nomes dos times"""
        try:
            if screenshot is None:
                screenshot = self.screen_capture.capture_screen()
            
            # Regiões onde aparecem nomes dos times
            height, width = screenshot.shape[:2]
            
            # Time da esquerda (nosso time)
            left_team_region = screenshot[100:200, 50:400]
            
            # Time da direita (adversário)
            right_team_region = screenshot[100:200, width-400:width-50]
            
            team_names = {"us": None, "opponent": None}
            
            # Tenta ler nome do time da esquerda
            try:
                gray_left = cv2.cvtColor(left_team_region, cv2.COLOR_BGR2GRAY)
                _, thresh_left = cv2.threshold(gray_left, 150, 255, cv2.THRESH_BINARY)
                text_left = pytesseract.image_to_string(thresh_left, config='--psm 7')
                if text_left.strip():
                    team_names["us"] = text_left.strip()
            except:
                pass
            
            # Tenta ler nome do time da direita
            try:
                gray_right = cv2.cvtColor(right_team_region, cv2.COLOR_BGR2GRAY)
                _, thresh_right = cv2.threshold(gray_right, 150, 255, cv2.THRESH_BINARY)
                text_right = pytesseract.image_to_string(thresh_right, config='--psm 7')
                if text_right.strip():
                    team_names["opponent"] = text_right.strip()
            except:
                pass
            
            return team_names
        except Exception as e:
            self.logger.debug(f"Erro ao detectar nomes dos times: {e}")
            return {"us": None, "opponent": None}
    
    def detect_player_name(self, screenshot=None, region=None):
        """Detecta nome de jogador na tela"""
        try:
            if screenshot is None:
                screenshot = self.screen_capture.capture_screen()
            
            if region:
                player_region = screenshot[region[1]:region[3], region[0]:region[2]]
            else:
                # Região padrão (ajustar conforme necessário)
                height, width = screenshot.shape[:2]
                player_region = screenshot[height//2-50:height//2+50, width//2-200:width//2+200]
            
            # Processa imagem
            gray = cv2.cvtColor(player_region, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Tenta ler com OCR
            try:
                text = pytesseract.image_to_string(thresh, config='--psm 7')
                # Limpa o texto
                player_name = text.strip()
                # Remove caracteres inválidos
                player_name = re.sub(r'[^a-zA-Z0-9\s\-]', '', player_name)
                if len(player_name) > 2:
                    return player_name
            except:
                pass
            
            return None
        except Exception as e:
            self.logger.debug(f"Erro ao detectar nome de jogador: {e}")
            return None
    
    def detect_player_price(self, screenshot=None, region=None):
        """Detecta preço de jogador"""
        try:
            if screenshot is None:
                screenshot = self.screen_capture.capture_screen()
            
            if region:
                price_region = screenshot[region[1]:region[3], region[0]:region[2]]
            else:
                # Região padrão (ajustar)
                height, width = screenshot.shape[:2]
                price_region = screenshot[height-100:height-50, width//2-100:width//2+100]
            
            # Processa imagem
            gray = cv2.cvtColor(price_region, cv2.COLOR_BGR2GRAY)
            _, thresh = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY)
            
            # Tenta ler com OCR
            try:
                text = pytesseract.image_to_string(thresh, config='--psm 8 -c tessedit_char_whitelist=0123456789,')
                # Remove vírgulas e converte
                price_text = text.replace(',', '').strip()
                if price_text.isdigit():
                    return int(price_text)
            except:
                pass
            
            return None
        except Exception as e:
            self.logger.debug(f"Erro ao detectar preço: {e}")
            return None
    
    def detect_match_result(self, screenshot=None):
        """Detecta resultado da partida"""
        try:
            if screenshot is None:
                screenshot = self.screen_capture.capture_screen()
            
            # Detecta placar
            score = self.detect_score(screenshot)
            
            # Detecta nomes dos times
            teams = self.detect_team_names(screenshot)
            
            if score:
                return {
                    "score": score,
                    "teams": teams,
                    "won": score["us"] > score["opponent"],
                    "draw": score["us"] == score["opponent"],
                    "lost": score["us"] < score["opponent"]
                }
            
            return None
        except Exception as e:
            self.logger.error(f"Erro ao detectar resultado: {e}")
            return None

