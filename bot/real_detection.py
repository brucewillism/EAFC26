"""
Módulo de Detecção Real - Detecta informações reais do jogo usando múltiplas técnicas
"""

import cv2
import numpy as np
import time
import pyautogui
from PIL import Image
import pytesseract

class RealDetection:
    """Detecta informações reais do jogo usando análise de imagem e OCR"""
    
    def __init__(self, screen_capture, logger, controller):
        self.screen_capture = screen_capture
        self.logger = logger
        self.controller = controller
        
        # Configura Tesseract
        self.setup_tesseract()
        
        # Cache de detecções
        self.detection_cache = {}
        self.cache_timeout = 5  # 5 segundos
        
    def setup_tesseract(self):
        """Configura Tesseract OCR"""
        try:
            pytesseract.get_tesseract_version()
            self.tesseract_available = True
        except:
            try:
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                pytesseract.get_tesseract_version()
                self.tesseract_available = True
            except:
                self.tesseract_available = False
                self.logger.warning("Tesseract não disponível. Detecção de texto limitada.")
    
    def capture_and_process(self, region=None):
        """Captura e processa tela"""
        try:
            screenshot = self.screen_capture.capture_screen(region)
            if screenshot is None:
                return None
            
            # Converte para escala de cinza
            gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            
            # Aplica threshold para melhorar OCR
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            return thresh
        except Exception as e:
            self.logger.error(f"Erro ao processar tela: {e}")
            return None
    
    def read_text_from_region(self, region, config='--psm 7'):
        """Lê texto de uma região específica"""
        try:
            if not self.tesseract_available:
                return None
            
            # Captura região
            screenshot = pyautogui.screenshot(region=region)
            img = np.array(screenshot)
            gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
            
            # Melhora contraste
            _, thresh = cv2.threshold(gray, 150, 255, cv2.THRESH_BINARY)
            
            # Lê com OCR
            text = pytesseract.image_to_string(thresh, config=config)
            
            # Limpa texto
            text = text.strip()
            text = ' '.join(text.split())  # Remove espaços extras
            
            return text if text else None
        except Exception as e:
            self.logger.debug(f"Erro ao ler texto: {e}")
            return None
    
    def check_team_exists(self):
        """Verifica se o time já existe na conta"""
        try:
            self.logger.info("Verificando se time existe...")
            
            # Aguarda carregar
            time.sleep(2)
            
            # Captura tela completa
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return False
            
            # Procura por indicadores de que o time existe
            # 1. Procura por texto "Ultimate Team" ou "My Club"
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            # Região onde geralmente aparece informação do time
            team_info_region = (screen_width//4, screen_height//4, screen_width//2, screen_height//2)
            
            text = self.read_text_from_region(team_info_region)
            
            if text:
                # Procura por palavras-chave
                keywords = ["Ultimate Team", "My Club", "Squad", "Team", "Clube"]
                text_lower = text.lower()
                
                for keyword in keywords:
                    if keyword.lower() in text_lower:
                        self.logger.info(f"Time encontrado! Indicador: {keyword}")
                        return True
            
            # 2. Procura por botões específicos
            # Se encontrar botão "Create Squad" ou similar, não tem time
            create_buttons = ["Create", "Criar", "New Squad", "Novo Time"]
            if text:
                for button in create_buttons:
                    if button.lower() in text.lower():
                        self.logger.info("Time não encontrado. Precisa criar.")
                        return False
            
            # Se não encontrou nada, assume que precisa criar
            self.logger.warning("Não foi possível determinar se time existe. Tentando criar...")
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar time: {e}")
            return False
    
    def detect_match_info_real(self):
        """Detecta informações reais da partida"""
        try:
            # Captura tela
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return None
            
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            match_info = {
                "our_team": None,
                "opponent_team": None,
                "score_us": None,
                "score_opponent": None
            }
            
            # Tenta múltiplas regiões para o placar (diferentes layouts)
            score_regions = [
                (screen_width//2 - 150, 50, screen_width//2 + 150, 150),  # Centro superior
                (screen_width//2 - 100, screen_height//2 - 50, screen_width//2 + 100, screen_height//2 + 50),  # Centro
                (screen_width//2 - 200, 30, screen_width//2 + 200, 130),  # Centro superior ampliado
                (screen_width//2 - 120, 40, screen_width//2 + 120, 140),  # Centro superior médio
                (screen_width//2 - 80, screen_height//2 - 30, screen_width//2 + 80, screen_height//2 + 30),  # Centro compacto
                (screen_width//2 - 180, 60, screen_width//2 + 180, 160),  # Centro superior extra ampliado
                (screen_width//2 - 100, 20, screen_width//2 + 100, 120),  # Muito superior
            ]
            
            # Múltiplas configurações OCR para melhor detecção
            ocr_configs = [
                '--psm 8 -c tessedit_char_whitelist=0123456789-:',  # Palavra única
                '--psm 7 -c tessedit_char_whitelist=0123456789-: ',  # Linha única
                '--psm 6 -c tessedit_char_whitelist=0123456789-: ',  # Bloco único
                '--psm 11',  # Texto esparso
                '--psm 13',  # Linha única bruta
            ]
            
            import re
            
            # Tenta também detecção por processamento de imagem (análise de contornos)
            score_detected = self._detect_score_by_image_processing(screenshot)
            if score_detected:
                match_info["score_us"] = score_detected.get("us")
                match_info["score_opponent"] = score_detected.get("opponent")
                self.logger.info(f"✅ Placar detectado por processamento de imagem: {score_detected['us']}-{score_detected['opponent']}")
            
            # Se não detectou por imagem, tenta OCR
            if match_info.get("score_us") is None:
                for score_region in score_regions:
                    for ocr_config in ocr_configs:
                        score_text = self.read_text_from_region(score_region, config=ocr_config)
                        if score_text:
                            # Limpa texto
                            score_text = score_text.strip()
                            
                            # Procura padrão de placar (múltiplos formatos)
                            patterns = [
                                r'(\d+)[-:\s]+(\d+)',  # Formato padrão: "2-1" ou "2:1"
                                r'(\d+)\s*[-:]\s*(\d+)',  # Com espaços: "2 - 1"
                                r'^(\d+)\s+(\d+)$',  # Apenas números: "2 1"
                                r'(\d+)\s*[xX]\s*(\d+)',  # Formato "2 x 1"
                                r'(\d+)\s*/\s*(\d+)',  # Formato "2/1"
                            ]
                            
                            for pattern in patterns:
                                score_match = re.search(pattern, score_text)
                                if score_match:
                                    try:
                                        score_us = int(score_match.group(1))
                                        score_opponent = int(score_match.group(2))
                                        
                                        # Validação: placares razoáveis (0-20)
                                        if 0 <= score_us <= 20 and 0 <= score_opponent <= 20:
                                            match_info["score_us"] = score_us
                                            match_info["score_opponent"] = score_opponent
                                            self.logger.info(f"✅ Placar detectado por OCR: {score_us}-{score_opponent}")
                                            break
                                    except (ValueError, IndexError):
                                        continue
                            
                            if match_info.get("score_us") is not None:
                                break
                    
                    if match_info.get("score_us") is not None:
                        break
            
            # Tenta múltiplas regiões para o time da esquerda
            left_team_regions = [
                (50, 100, 400, 200),  # Esquerda padrão
                (50, 80, 500, 180),  # Esquerda ampliada
                (30, 120, 450, 220),  # Esquerda ajustada
            ]
            
            for left_team_region in left_team_regions:
                our_team_text = self.read_text_from_region(left_team_region, config='--psm 7')
                if our_team_text and len(our_team_text.strip()) > 2:
                    # Limpa texto (remove caracteres inválidos)
                    our_team_text = ' '.join(our_team_text.split())
                    
                    # Filtra texto inválido (botões, símbolos, etc)
                    invalid_patterns = ['parar', 'stop', 'pausar', 'pause', '—', '=', '-', '|', '_', 
                                       'botao', 'button', 'menu', 'voltar', 'back', 'esc']
                    text_lower = our_team_text.lower()
                    
                    # Verifica se contém padrões inválidos
                    if any(pattern in text_lower for pattern in invalid_patterns):
                        continue
                    
                    # Verifica se tem pelo menos uma letra
                    if not any(c.isalpha() for c in our_team_text):
                        continue
                    
                    if len(our_team_text) > 2 and len(our_team_text) < 50:  # Nome razoável
                        match_info["our_team"] = our_team_text
                        self.logger.info(f"Nosso time detectado: {our_team_text}")
                        break
            
            # Tenta múltiplas regiões para o time da direita
            right_team_regions = [
                (screen_width - 400, 100, screen_width - 50, 200),  # Direita padrão
                (screen_width - 500, 80, screen_width - 30, 180),  # Direita ampliada
                (screen_width - 450, 120, screen_width - 30, 220),  # Direita ajustada
            ]
            
            for right_team_region in right_team_regions:
                opponent_team_text = self.read_text_from_region(right_team_region, config='--psm 7')
                if opponent_team_text and len(opponent_team_text.strip()) > 2:
                    # Limpa texto
                    opponent_team_text = ' '.join(opponent_team_text.split())
                    
                    # Filtra texto inválido (botões, símbolos, etc)
                    invalid_patterns = ['parar', 'stop', 'pausar', 'pause', '—', '=', '-', '|', '_', 
                                       'botao', 'button', 'menu', 'voltar', 'back', 'esc']
                    text_lower = opponent_team_text.lower()
                    
                    # Verifica se contém padrões inválidos
                    if any(pattern in text_lower for pattern in invalid_patterns):
                        continue
                    
                    # Verifica se tem pelo menos uma letra
                    if not any(c.isalpha() for c in opponent_team_text):
                        continue
                    
                    if len(opponent_team_text) > 2 and len(opponent_team_text) < 50:
                        match_info["opponent_team"] = opponent_team_text
                        self.logger.info(f"Adversário detectado: {opponent_team_text}")
                        break
            
            # Se detectou placar ou pelo menos um time válido, retorna
            if match_info.get("score_us") is not None or match_info.get("score_opponent") is not None:
                # Tem placar, retorna mesmo sem nomes dos times
                return match_info
            
            if match_info.get("our_team") or match_info.get("opponent_team"):
                # Tem pelo menos um time válido, retorna
                return match_info
            
            # Se não detectou nada válido, retorna None (não salva screenshot para não encher o disco)
            self.logger.debug("Não foi possível detectar informações válidas da partida.")
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao detectar informações da partida: {e}")
            return None
    
    def detect_player_in_market(self, region=None):
        """Detecta jogador no mercado de transferências"""
        try:
            if region is None:
                # Região padrão (ajustar conforme necessário)
                screenshot = self.screen_capture.capture_screen()
                if screenshot is None:
                    return None
                
                screen_width = screenshot.shape[1]
                screen_height = screenshot.shape[0]
                
                # Região onde aparecem jogadores (ajustar)
                region = (
                    screen_width//4,
                    screen_height//3,
                    screen_width*3//4,
                    screen_height*2//3
                )
            
            # Detecta nome do jogador (tenta múltiplas configurações OCR)
            player_name = None
            ocr_configs = [
                '--psm 7',  # Linha única
                '--psm 6',  # Bloco único
                '--psm 8',  # Palavra única
            ]
            
            for config in ocr_configs:
                player_name = self.read_text_from_region(region, config=config)
                if player_name and len(player_name.strip()) > 2:
                    player_name = ' '.join(player_name.split())  # Limpa espaços
                    if 3 <= len(player_name) <= 40:  # Nome razoável
                        break
                player_name = None
            
            # Detecta preço (tenta múltiplas regiões)
            price = None
            price_regions = [
                (region[0], region[3] + 10, region[2], region[3] + 50),  # Logo abaixo
                (region[0], region[3] + 20, region[2], region[3] + 70),  # Um pouco mais abaixo
                (region[0] + region[2]//2, region[1], region[2], region[3]),  # Lado direito do slot
            ]
            
            for price_region in price_regions:
                price_text = self.read_text_from_region(price_region, config='--psm 8 -c tessedit_char_whitelist=0123456789,')
                
                if price_text:
                    # Remove vírgulas, pontos e espaços
                    price_clean = price_text.replace(',', '').replace('.', '').replace(' ', '').strip()
                    if price_clean.isdigit():
                        price = int(price_clean)
                        if 100 <= price <= 10000000:  # Preço razoável
                            break
                price = None
            
            if player_name or price:
                result = {}
                if player_name:
                    result["name"] = player_name
                if price:
                    result["price"] = price
                return result
            
            return None
            
        except Exception as e:
            self.logger.error(f"Erro ao detectar jogador: {e}")
            return None
    
    def detect_current_screen(self):
        """Detecta em qual tela do jogo está"""
        try:
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return "unknown"
            
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            # Tenta múltiplas regiões para melhor detecção
            regions_to_check = [
                (screen_width//4, 50, screen_width*3//4, 150),  # Superior central
                (50, 50, screen_width//2, 200),  # Superior esquerda
                (screen_width//2, 50, screen_width-50, 200),  # Superior direita
                (screen_width//4, screen_height//2, screen_width*3//4, screen_height//2 + 100),  # Centro
            ]
            
            all_text = ""
            for region in regions_to_check:
                text = self.read_text_from_region(region, config='--psm 7')
                if text:
                    all_text += " " + text.lower()
            
            if all_text:
                # Identifica tela com palavras-chave mais específicas primeiro
                if any(keyword in all_text for keyword in ["squad battles", "batalhas de esquadrao", "batalhas"]):
                    return "squad_battles"
                elif any(keyword in all_text for keyword in ["transfer market", "mercado de transferencias", "mercado"]):
                    return "transfer_market"
                elif any(keyword in all_text for keyword in ["objectives", "objetivos"]):
                    return "objectives"
                elif any(keyword in all_text for keyword in ["ultimate team", "my club", "meu clube"]):
                    return "ultimate_team"
                elif any(keyword in all_text for keyword in ["match", "partida", "vs", "versus"]):
                    return "match"
                elif any(keyword in all_text for keyword in ["create", "criar", "new squad", "novo time"]):
                    return "team_creation"
            
            return "unknown"
            
        except Exception as e:
            self.logger.debug(f"Erro ao detectar tela: {e}")
            return "unknown"
    
    def wait_for_screen(self, target_screen, timeout=10):
        """Aguarda até estar em uma tela específica"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            current_screen = self.detect_current_screen()
            if current_screen == target_screen:
                return True
            time.sleep(0.5)
        
        return False
    
    def _detect_score_by_image_processing(self, screenshot):
        """Detecta placar usando processamento de imagem (análise de contornos)"""
        try:
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            # Região central superior onde geralmente aparece o placar
            score_region = screenshot[50:150, screen_width//2 - 200:screen_width//2 + 200]
            
            # Converte para escala de cinza
            gray = cv2.cvtColor(score_region, cv2.COLOR_BGR2GRAY)
            
            # Aplica threshold adaptativo para melhorar contraste
            thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
                                         cv2.THRESH_BINARY_INV, 11, 2)
            
            # Encontra contornos
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            # Filtra contornos que podem ser números (por tamanho e posição)
            number_contours = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = cv2.contourArea(contour)
                
                # Filtra por tamanho razoável de número
                if 50 < area < 2000 and 10 < w < 100 and 20 < h < 100:
                    number_contours.append((x, y, w, h))
            
            # Se encontrou contornos que podem ser números, tenta OCR na região processada
            if len(number_contours) >= 2:
                # Ordena por posição X (esquerda para direita)
                number_contours.sort(key=lambda c: c[0])
                
                # Tenta ler os dois primeiros números (placar)
                if len(number_contours) >= 2:
                    # Região do primeiro número (nosso time)
                    x1, y1, w1, h1 = number_contours[0]
                    num1_region = thresh[y1:y1+h1, x1:x1+w1]
                    
                    # Região do segundo número (adversário)
                    x2, y2, w2, h2 = number_contours[1]
                    num2_region = thresh[y2:y2+h2, x2:x2+w2]
                    
                    # Tenta ler com OCR
                    try:
                        num1_text = pytesseract.image_to_string(num1_region, config='--psm 10 -c tessedit_char_whitelist=0123456789')
                        num2_text = pytesseract.image_to_string(num2_region, config='--psm 10 -c tessedit_char_whitelist=0123456789')
                        
                        num1_text = num1_text.strip()
                        num2_text = num2_text.strip()
                        
                        if num1_text.isdigit() and num2_text.isdigit():
                            score_us = int(num1_text)
                            score_opponent = int(num2_text)
                            
                            if 0 <= score_us <= 20 and 0 <= score_opponent <= 20:
                                return {"us": score_us, "opponent": score_opponent}
                    except:
                        pass
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Erro na detecção por processamento de imagem: {e}")
            return None
    
    def take_screenshot_debug(self, filename="debug_screenshot.png"):
        """Tira screenshot para debug"""
        try:
            screenshot = self.screen_capture.capture_screen()
            if screenshot is not None:
                cv2.imwrite(filename, screenshot)
                self.logger.info(f"Screenshot salvo: {filename}")
                return True
        except Exception as e:
            self.logger.error(f"Erro ao salvar screenshot: {e}")
        return False

