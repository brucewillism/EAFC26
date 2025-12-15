"""
Módulo de Navegação Inteligente - Detecta e clica em botões automaticamente
"""

import cv2
import numpy as np
import time
import pyautogui
from bot.real_detection import RealDetection

class Navigation:
    """Sistema de navegação inteligente que detecta botões e elementos da UI"""
    
    def __init__(self, controller, screen_capture, real_detection, logger):
        self.controller = controller
        self.screen_capture = screen_capture
        self.real_detection = real_detection
        self.logger = logger
        
        # Coordenadas padrão (serão calibradas)
        self.coordinates = {
            "ultimate_team_menu": None,
            "transfer_market": None,
            "squad_battles": None,
            "objectives": None,
            "squad_menu": None,
            "squad_builder": None,
            "club_search": None,
            "apply_filters": None,
            "confirm_substitution": None,
            "clear_filters": None,
            "buy_now": None,
            "confirm": None,
            "search": None,
            "list_for_transfer": None
        }
        
        # Carrega coordenadas salvas se existirem
        self.load_coordinates()
    
    def load_coordinates(self):
        """Carrega coordenadas calibradas do arquivo"""
        try:
            import json
            import os
            if os.path.exists("coordenadas_calibradas.json"):
                with open("coordenadas_calibradas.json", 'r', encoding='utf-8') as f:
                    saved = json.load(f)
                    self.coordinates.update(saved)
                    self.logger.info("Coordenadas calibradas carregadas")
        except Exception as e:
            self.logger.debug(f"Erro ao carregar coordenadas: {e}")
    
    def find_button_by_text(self, text, region=None, timeout=5):
        """
        Encontra botão pelo texto usando OCR
        
        Args:
            text: Texto do botão a procurar
            region: Região da tela para buscar (None = tela toda)
            timeout: Tempo máximo para buscar
            
        Returns:
            (x, y) coordenadas do botão ou None
        """
        try:
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                screenshot = self.screen_capture.capture_screen(region)
                if screenshot is None:
                    continue
                
                # Se região foi especificada, ajusta coordenadas
                if region:
                    x_offset, y_offset = region[0], region[1]
                else:
                    x_offset, y_offset = 0, 0
                
                # Divide tela em regiões para buscar
                screen_height, screen_width = screenshot.shape[:2]
                
                # Regiões comuns onde botões aparecem
                search_regions = [
                    (screen_width//4, screen_height//2, screen_width*3//4, screen_height*3//4),  # Centro inferior
                    (screen_width//4, screen_height//4, screen_width*3//4, screen_height//2),  # Centro
                    (50, screen_height-100, screen_width-50, screen_height-50),  # Barra inferior
                    (screen_width//2-200, screen_height//2-50, screen_width//2+200, screen_height//2+50),  # Centro exato
                ]
                
                for search_region in search_regions:
                    # Ajusta região se offset foi especificado
                    if region:
                        adj_region = (
                            search_region[0] + x_offset,
                            search_region[1] + y_offset,
                            search_region[2] + x_offset,
                            search_region[3] + y_offset
                        )
                    else:
                        adj_region = search_region
                    
                    # Lê texto da região
                    detected_text = self.real_detection.read_text_from_region(adj_region)
                    
                    if detected_text and text.lower() in detected_text.lower():
                        # Encontrou! Calcula centro da região
                        center_x = (adj_region[0] + adj_region[2]) // 2
                        center_y = (adj_region[1] + adj_region[3]) // 2
                        
                        self.logger.info(f"Botão '{text}' encontrado em ({center_x}, {center_y})")
                        return (center_x, center_y)
                
                time.sleep(0.5)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Erro ao buscar botão '{text}': {e}")
            return None
    
    def find_button_by_template(self, template_path, threshold=0.8, region=None):
        """
        Encontra botão usando template matching
        
        Args:
            template_path: Caminho para imagem template
            threshold: Limiar de confiança (0-1)
            region: Região para buscar
            
        Returns:
            (x, y) coordenadas ou None
        """
        try:
            screenshot = self.screen_capture.capture_screen(region)
            if screenshot is None:
                return None
            
            template = cv2.imread(template_path, cv2.IMREAD_COLOR)
            if template is None:
                return None
            
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            
            if max_val >= threshold:
                h, w = template.shape[:2]
                center_x = max_loc[0] + w // 2
                center_y = max_loc[1] + h // 2
                
                if region:
                    center_x += region[0]
                    center_y += region[1]
                
                self.logger.info(f"Template encontrado em ({center_x}, {center_y}) com confiança {max_val:.2f}")
                return (center_x, center_y)
            
            return None
            
        except Exception as e:
            self.logger.debug(f"Erro ao buscar template: {e}")
            return None
    
    def click_button(self, button_name, method="text", fallback_coords=None, timeout=5):
        """
        Clica em um botão usando múltiplos métodos
        
        Args:
            button_name: Nome do botão ou texto a procurar
            method: Método de busca ("text", "template", "coords")
            fallback_coords: Coordenadas de fallback se busca falhar
            timeout: Timeout para busca
            
        Returns:
            True se clicou com sucesso
        """
        try:
            coords = None
            
            # Método 1: Usar coordenadas salvas
            if button_name in self.coordinates and self.coordinates[button_name]:
                coords = self.coordinates[button_name]
                self.logger.debug(f"Usando coordenadas salvas para '{button_name}'")
            
            # Método 2: Buscar por texto
            if not coords and method in ["text", "auto"]:
                coords = self.find_button_by_text(button_name, timeout=timeout)
            
            # Método 3: Buscar por template (se existir)
            if not coords and method in ["template", "auto"]:
                template_path = f"templates/{button_name.lower().replace(' ', '_')}.png"
                import os
                if os.path.exists(template_path):
                    coords = self.find_button_by_template(template_path)
            
            # Método 4: Usar coordenadas de fallback
            if not coords and fallback_coords:
                coords = fallback_coords
                self.logger.debug(f"Usando coordenadas de fallback para '{button_name}'")
            
            if coords:
                self.controller.click(coords[0], coords[1])
                self.logger.info(f"✅ Clicou em '{button_name}' em ({coords[0]}, {coords[1]})")
                return True
            else:
                self.logger.warning(f"❌ Não foi possível encontrar botão '{button_name}'")
                self.logger.warning(f"💡 Dica: Execute 'python calibrar_automatico.py' para calibrar coordenadas")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao clicar em botão '{button_name}': {e}")
            return False
    
    def ensure_main_menu(self, attempts=3, delay=0.8):
        """Tenta voltar ao menu principal pressionando ESC algumas vezes."""
        try:
            for _ in range(attempts):
                self.controller.press_key('esc')
                time.sleep(delay)
            return True
        except Exception as e:
            self.logger.debug(f"Erro ao tentar voltar ao menu: {e}")
            return False

    def navigate_to_squad(self):
        """Navega para a tela de Squad (elenco)"""
        try:
            self.logger.info("🧭 Navegando para Squad (elenco)...")
            current_screen = self.real_detection.detect_current_screen()
            if current_screen == "squad":
                return True
            
            # Volta ao menu principal (reforçado)
            self.ensure_main_menu()

            # Vai para Ultimate Team se não estiver
            if current_screen != "ultimate_team":
                if not self.click_button("Ultimate Team", method="auto",
                                        fallback_coords=self.coordinates.get("ultimate_team_menu")):
                    self.controller.click(960, 400)
                time.sleep(1.5)

            # Clica em Squad / Club
            if not self.click_button("Squad", method="auto",
                                    fallback_coords=self.coordinates.get("squad_menu")):
                # tentativa genérica
                self.controller.click(960, 430)
            
            time.sleep(2)
            # Não temos detecção específica de tela, então apenas logamos
            self.logger.info("Tentativa de navegação para Squad concluída.")
            return True
        except Exception as e:
            self.logger.error(f"Erro ao navegar para Squad: {e}")
            return False

    def open_squad_builder(self):
        """Abre o editor de elenco (Squad Builder)"""
        try:
            self.logger.info("🧭 Abrindo Squad Builder / elenco...")
            # Tenta botão Squad Builder / Club
            if not self.click_button("Squad Builder", method="auto",
                                     fallback_coords=self.coordinates.get("squad_builder")):
                # fallback genérico
                self.controller.click(960, 500)
            time.sleep(1.5)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao abrir Squad Builder: {e}")
            return False

    def open_club_search(self):
        """Abre a busca no clube para substituir jogador"""
        try:
            self.logger.info("🔎 Abrindo busca no clube...")
            if not self.click_button("Club", method="auto",
                                     fallback_coords=self.coordinates.get("club_search")):
                # Tentativa com texto "Search" ou coord fallback
                if not self.click_button("Search", method="auto",
                                         fallback_coords=self.coordinates.get("search")):
                    self.controller.click(960, 600)
            time.sleep(1.5)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao abrir busca no clube: {e}")
            return False

    def apply_filter(self, league=None, nation=None, position=None):
        """Aplica filtros básicos (liga/nação/posição) na busca do clube"""
        try:
            self.logger.info(f"🎛️ Aplicando filtros: league={league}, nation={nation}, position={position}")
            # Abre menu de filtros
            if not self.click_button("Filters", method="auto",
                                     fallback_coords=self.coordinates.get("apply_filters")):
                self.controller.click(1200, 200)  # fallback genérico
            time.sleep(1)

            # Liga
            if league:
                if not self.click_button("League", method="auto"):
                    self.controller.click(600, 300)
                time.sleep(0.5)
                # Digita ou seleciona liga (dependente de OCR); aqui tentamos texto
                self.real_detection.read_text_from_region(None)  # força captura (placeholder)
                # Para simplificar, usa clique genérico
                self.controller.type_text(league)
                time.sleep(0.5)
                self.controller.press_key('enter')
                time.sleep(0.5)

            # Nação
            if nation:
                if not self.click_button("Nation", method="auto"):
                    self.controller.click(600, 360)
                time.sleep(0.5)
                self.controller.type_text(nation)
                time.sleep(0.5)
                self.controller.press_key('enter')
                time.sleep(0.5)

            # Posição
            if position:
                if not self.click_button("Position", method="auto"):
                    self.controller.click(600, 420)
                time.sleep(0.5)
                self.controller.type_text(position)
                time.sleep(0.5)
                self.controller.press_key('enter')
                time.sleep(0.5)

            # Aplicar filtros
            if not self.click_button("Apply", method="auto"):
                self.controller.click(1200, 800)
            time.sleep(1.5)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao aplicar filtros: {e}")
            return False

    def select_first_search_result(self):
        """Seleciona o primeiro jogador do resultado de busca"""
        try:
            self.logger.info("🧩 Selecionando primeiro jogador do resultado...")
            # Fallback: clicar em uma área central onde o primeiro item costuma aparecer
            self.controller.click(960, 400)
            time.sleep(0.8)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao selecionar resultado: {e}")
            return False

    def confirm_substitution(self):
        """Confirma substituição do jogador selecionado"""
        try:
            self.logger.info("✅ Confirmando substituição...")
            if not self.click_button("Select", method="auto",
                                     fallback_coords=self.coordinates.get("confirm_substitution")):
                self.controller.click(1200, 850)
            time.sleep(0.8)
            if not self.click_button("Confirm", method="auto",
                                     fallback_coords=self.coordinates.get("confirm")):
                self.controller.click(1200, 900)
            time.sleep(1.0)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao confirmar substituição: {e}")
            return False

    def clear_filters(self):
        """Limpa filtros aplicados"""
        try:
            self.logger.info("🧹 Limpando filtros...")
            if not self.click_button("Clear", method="auto",
                                     fallback_coords=self.coordinates.get("clear_filters")):
                self.controller.click(1200, 150)
            time.sleep(0.8)
            return True
        except Exception as e:
            self.logger.error(f"Erro ao limpar filtros: {e}")
            return False

    def navigate_to_ultimate_team(self):
        """Navega para Ultimate Team"""
        try:
            self.logger.info("🧭 Navegando para Ultimate Team...")
            
            # Verifica se já está lá
            current_screen = self.real_detection.detect_current_screen()
            if current_screen == "ultimate_team":
                self.logger.info("Já está no Ultimate Team")
                return True
            
            # Volta ao menu principal
            self.ensure_main_menu()
            
            # Clica em Ultimate Team
            if not self.click_button("Ultimate Team", method="auto", 
                                    fallback_coords=self.coordinates.get("ultimate_team_menu")):
                # Tenta coordenadas padrão
                self.controller.click(960, 400)
            
            time.sleep(2)
            
            # Verifica se chegou
            if self.real_detection.wait_for_screen("ultimate_team", timeout=5):
                self.logger.info("✅ Chegou ao Ultimate Team")
                return True
            else:
                self.logger.warning("Não foi possível confirmar navegação para Ultimate Team")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao navegar para Ultimate Team: {e}")
            return False
    
    def navigate_to_transfer_market(self):
        """Navega para Transfer Market"""
        try:
            self.logger.info("🧭 Navegando para Transfer Market...")
            
            # Verifica se já está lá
            current_screen = self.real_detection.detect_current_screen()
            if current_screen == "transfer_market":
                self.logger.info("Já está no Transfer Market")
                return True
            
            # Volta ao menu principal (reforçado)
            self.ensure_main_menu()
            
            # Clica em Ultimate Team (se necessário)
            if current_screen != "ultimate_team":
                if not self.navigate_to_ultimate_team():
                    return False
            
            # Clica em Transfer Market
            if not self.click_button("Transfer Market", method="auto",
                                   fallback_coords=self.coordinates.get("transfer_market")):
                # Tenta coordenadas padrão
                self.controller.click(960, 500)
            
            time.sleep(2)
            
            # Verifica se chegou
            if self.real_detection.wait_for_screen("transfer_market", timeout=5):
                self.logger.info("✅ Chegou ao Transfer Market")
                return True
            else:
                self.logger.warning("Não foi possível confirmar navegação")
                return False
                
        except Exception as e:
            self.logger.error(f"Erro ao navegar para Transfer Market: {e}")
            return False
    
    def navigate_to_squad_battles(self):
        """Navega para Squad Battles"""
        try:
            self.logger.info("🧭 Navegando para Squad Battles...")
            
            current_screen = self.real_detection.detect_current_screen()
            if current_screen == "squad_battles":
                return True
            
            self.ensure_main_menu()
            
            if current_screen != "ultimate_team":
                if not self.click_button("Ultimate Team", method="auto",
                                        fallback_coords=self.coordinates.get("ultimate_team_menu")):
                    self.controller.click(960, 400)
                time.sleep(1.5)
            
            if not self.click_button("Squad Battles", method="auto",
                                   fallback_coords=self.coordinates.get("squad_battles")):
                self.controller.click(960, 450)
            
            time.sleep(2)
            
            if self.real_detection.wait_for_screen("squad_battles", timeout=5):
                self.logger.info("✅ Chegou ao Squad Battles")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao navegar para Squad Battles: {e}")
            return False
    
    def buy_player_at_position(self, x, y):
        """
        Compra jogador na posição especificada
        
        Args:
            x, y: Coordenadas do jogador na lista
        """
        try:
            self.logger.info(f"💰 Tentando comprar jogador em ({x}, {y})...")
            
            # 1. Clica no jogador
            self.controller.click(x, y)
            time.sleep(0.8)
            
            # 2. Clica em "Buy Now"
            if not self.click_button("Buy Now", method="auto",
                                   fallback_coords=self.coordinates.get("buy_now")):
                # Tenta coordenadas padrão (lado direito da tela)
                self.controller.click(1400, 600)
            time.sleep(1)
            
            # 3. Confirma compra
            if not self.click_button("Confirm", method="auto",
                                   fallback_coords=self.coordinates.get("confirm")):
                # Tenta coordenadas padrão (centro)
                self.controller.click(960, 700)
            time.sleep(1.5)
            
            # 4. Fecha diálogo de confirmação (se aparecer)
            self.controller.press_key('esc')
            time.sleep(0.5)
            
            self.logger.info("✅ Processo de compra concluído")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao comprar jogador: {e}")
            return False
    
    def list_player_for_sale_at_position(self, x, y, price):
        """
        Lista jogador para venda na posição especificada
        
        Args:
            x, y: Coordenadas do jogador
            price: Preço para listar
        """
        try:
            self.logger.info(f"💼 Listando jogador em ({x}, {y}) por {price} coins...")
            
            # 1. Clica no jogador
            self.controller.click(x, y)
            time.sleep(0.8)
            
            # 2. Clica em "List for Transfer"
            if not self.click_button("List for Transfer", method="auto",
                                   fallback_coords=self.coordinates.get("list_for_transfer")):
                # Tenta coordenadas padrão
                self.controller.click(1200, 600)
            time.sleep(1)
            
            # 3. Define preço (precisa implementar entrada de texto)
            # Por enquanto, assume que o preço já está definido ou usa setas
            # self.controller.type_price(price)  # Implementar se necessário
            
            # 4. Confirma
            if not self.click_button("Confirm", method="auto",
                                   fallback_coords=self.coordinates.get("confirm")):
                self.controller.click(960, 700)
            time.sleep(1)
            
            self.logger.info("✅ Jogador listado para venda")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao listar jogador: {e}")
            return False

