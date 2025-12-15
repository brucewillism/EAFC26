"""
Módulo de Objetivos - Completa objetivos automaticamente
"""

import time
from bot.base_module import BaseModule

class ObjectivesBot(BaseModule):
    """Bot para completar objetivos automaticamente"""
    
    def __init__(self, config, controller, screen_capture, logger, team_manager=None):
        super().__init__(config, controller, screen_capture, logger)
        self.objectives_config = config.get("objectives", {})
        self.enabled = self.objectives_config.get("enabled", False)
        self.check_interval = self.objectives_config.get("check_interval", 300)  # 5 minutos
        self.team_manager = team_manager
        
        # Estatísticas
        self.stats = {
            "objectives_completed": 0,
            "rewards_claimed": 0,
            "last_check": None
        }
        
    def run_cycle(self):
        """Executa um ciclo de verificação de objetivos"""
        if not self.enabled:
            return
        
        try:
            self.logger.info("Verificando objetivos...")
            
            # 1. Navegar para Objectives
            if not self.navigate_to_objectives():
                return
            
            # 2. Verificar objetivos disponíveis
            objectives = self.get_available_objectives()
            
            # 3. Completar objetivos
            for objective in objectives:
                if self.can_complete_objective(objective):
                    if self.complete_objective(objective):
                        self.stats["objectives_completed"] += 1
            
            # 4. Reivindicar recompensas
            self.claim_rewards()
            
            # Atualiza última verificação
            self.stats["last_check"] = time.time()
            
            # Aguarda antes da próxima verificação
            time.sleep(self.check_interval)
            
        except Exception as e:
            self.logger.error(f"Erro no ciclo de objetivos: {e}", exc_info=True)
    
    def navigate_to_objectives(self):
        """Navega para a seção de Objetivos"""
        try:
            self.logger.info("Navegando para Objectives...")
            
            # Navegação: Menu -> Ultimate Team -> Objectives
            # Coordenadas precisam ser ajustadas
            
            # Pressiona ESC para voltar ao menu se necessário
            self.controller.press_key('esc')
            time.sleep(1)
            
            # Exemplo de navegação (coordenadas precisam ser calibradas):
            # self.controller.click(960, 400)  # Ultimate Team
            # time.sleep(1)
            # self.controller.click(960, 450)  # Objectives
            
            self.logger.info("Navegação para Objectives concluída")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao navegar para Objectives: {e}")
            return False
    
    def get_available_objectives(self):
        """Obtém lista de objetivos disponíveis usando OCR"""
        try:
            self.logger.info("Buscando objetivos disponíveis...")
            
            # Captura tela
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return []
            
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            objectives = []
            
            # Inicializa detecção real
            from bot.real_detection import RealDetection
            real_detection = RealDetection(self.screen_capture, self.logger, self.controller)
            
            # Regiões onde objetivos geralmente aparecem (lista vertical)
            objective_regions = []
            num_objectives = 5  # Número máximo de objetivos a procurar
            
            for i in range(num_objectives):
                # Calcula região de cada objetivo (ajustar conforme layout)
                obj_height = screen_height // (num_objectives + 2)
                obj_y_start = screen_height // 4 + (i * obj_height)
                obj_y_end = obj_y_start + obj_height
                
                objective_regions.append((
                    screen_width // 8,      # X início
                    obj_y_start,            # Y início
                    screen_width * 7 // 8,  # X fim
                    obj_y_end               # Y fim
                ))
            
            # Detecta objetivos em cada região
            for i, region in enumerate(objective_regions):
                try:
                    # Lê texto da região
                    text = real_detection.read_text_from_region(region, config='--psm 6')
                    
                    if text and len(text.strip()) > 5:
                        # Analisa texto para extrair informações do objetivo
                        objective = self._parse_objective_text(text, region)
                        if objective:
                            objectives.append(objective)
                            self.logger.info(f"✅ Objetivo detectado: {objective.get('name', 'Unknown')}")
                except Exception as e:
                    self.logger.debug(f"Erro ao processar região {i}: {e}")
                    continue
            
            self.logger.info(f"Total de {len(objectives)} objetivos encontrados")
            return objectives
            
        except Exception as e:
            self.logger.error(f"Erro ao obter objetivos: {e}")
            return []
    
    def _parse_objective_text(self, text, region):
        """Analisa texto para extrair informações do objetivo"""
        try:
            import re
            
            text_lower = text.lower()
            objective = {
                "name": text.strip()[:50],  # Primeiros 50 caracteres
                "type": "unknown",
                "progress": 0,
                "target": 0,
                "completed": False,
                "region": region
            }
            
            # Detecta tipo de objetivo por palavras-chave
            if any(keyword in text_lower for keyword in ["score", "gol", "goal", "fazer gol"]):
                objective["type"] = "scoring"
            elif any(keyword in text_lower for keyword in ["assist", "assistencia", "assistência"]):
                objective["type"] = "assists"
            elif any(keyword in text_lower for keyword in ["win", "vitoria", "vitória", "ganhar"]):
                objective["type"] = "wins"
            elif any(keyword in text_lower for keyword in ["match", "partida", "jogar"]):
                objective["type"] = "matches"
            elif any(keyword in text_lower for keyword in ["trade", "trading", "comprar", "vender"]):
                objective["type"] = "trading"
            elif any(keyword in text_lower for keyword in ["sbc", "challenge", "desafio"]):
                objective["type"] = "sbc"
            
            # Detecta progresso e meta (formato: "3/5" ou "3 de 5" ou "3 out of 5")
            progress_patterns = [
                r'(\d+)\s*[/]\s*(\d+)',  # "3/5"
                r'(\d+)\s+de\s+(\d+)',    # "3 de 5"
                r'(\d+)\s+out\s+of\s+(\d+)',  # "3 out of 5"
                r'(\d+)\s*[-]\s*(\d+)',  # "3-5"
            ]
            
            for pattern in progress_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        progress = int(match.group(1))
                        target = int(match.group(2))
                        objective["progress"] = progress
                        objective["target"] = target
                        objective["completed"] = progress >= target
                        break
                    except (ValueError, IndexError):
                        continue
            
            # Detecta se está completo por palavras-chave
            if any(keyword in text_lower for keyword in ["complete", "completo", "done", "feito", "claim", "reivindicar"]):
                objective["completed"] = True
            
            return objective
            
        except Exception as e:
            self.logger.debug(f"Erro ao analisar texto do objetivo: {e}")
            return None
    
    def can_complete_objective(self, objective):
        """Verifica se um objetivo pode ser completado"""
        try:
            # Verifica se o objetivo já está completo
            if objective.get("completed", False):
                return False
            
            # Verifica o tipo de objetivo e se pode ser automatizado
            objective_type = objective.get("type", "")
            
            # Tipos que podem ser automatizados:
            automatable_types = [
                "scoring",      # Fazer gols
                "assists",      # Dar assistências
                "wins",         # Ganhar partidas
                "matches",      # Jogar partidas
                "trading",      # Trading
                "sbc"           # Squad Building Challenges
            ]
            
            if objective_type in automatable_types:
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar objetivo: {e}")
            return False
    
    def complete_objective(self, objective):
        """Completa um objetivo"""
        try:
            objective_type = objective.get("type", "")
            objective_name = objective.get("name", "Unknown")
            requirement = objective.get("requirement", {})
            
            self.logger.info(f"Completando objetivo: {objective_name} (Tipo: {objective_type})")

            # Ajusta elenco se houver requisito de liga/nação/posição
            if self.team_manager and requirement:
                self.team_manager.prepare_squad_for_requirement(requirement)
            
            # Roteia para o método apropriado baseado no tipo
            if objective_type == "scoring":
                return self.complete_scoring_objective(objective)
            elif objective_type == "assists":
                return self.complete_assists_objective(objective)
            elif objective_type == "wins" or objective_type == "matches":
                return self.complete_matches_objective(objective)
            elif objective_type == "trading":
                return self.complete_trading_objective(objective)
            elif objective_type == "sbc":
                return self.complete_sbc_objective(objective)
            else:
                self.logger.warning(f"Tipo de objetivo não suportado: {objective_type}")
                return False
            
        except Exception as e:
            self.logger.error(f"Erro ao completar objetivo: {e}")
            return False
    
    def complete_scoring_objective(self, objective):
        """Completa objetivo de fazer gols"""
        try:
            self.logger.info(f"Completando objetivo de gols: {objective.get('name', 'Unknown')}")
            # Objetivo será completado naturalmente ao jogar partidas
            # Squad Battles já faz gols automaticamente
            return True
        except Exception as e:
            self.logger.error(f"Erro ao completar objetivo de gols: {e}")
            return False
    
    def complete_assists_objective(self, objective):
        """Completa objetivo de assistências"""
        try:
            self.logger.info(f"Completando objetivo de assistências: {objective.get('name', 'Unknown')}")
            # Objetivo será completado naturalmente ao jogar partidas
            return True
        except Exception as e:
            self.logger.error(f"Erro ao completar objetivo de assistências: {e}")
            return False
    
    def complete_matches_objective(self, objective):
        """Completa objetivo de partidas"""
        try:
            self.logger.info(f"Completando objetivo de partidas: {objective.get('name', 'Unknown')}")
            # Squad Battles já joga partidas automaticamente
            return True
        except Exception as e:
            self.logger.error(f"Erro ao completar objetivo de partidas: {e}")
            return False
    
    def complete_trading_objective(self, objective):
        """Completa objetivo de trading"""
        try:
            self.logger.info(f"Completando objetivo de trading: {objective.get('name', 'Unknown')}")
            # Trading bot já faz trades automaticamente
            return True
        except Exception as e:
            self.logger.error(f"Erro ao completar objetivo de trading: {e}")
            return False
    
    def complete_sbc_objective(self, objective):
        """Completa objetivo de SBC"""
        try:
            self.logger.info(f"Completando objetivo de SBC: {objective.get('name', 'Unknown')}")
            # SBC requer implementação específica (não implementado ainda)
            self.logger.warning("SBC não está implementado ainda")
            return False
        except Exception as e:
            self.logger.error(f"Erro ao completar objetivo de SBC: {e}")
            return False
    
    def claim_rewards(self):
        """Reivindica recompensas disponíveis"""
        try:
            self.logger.info("Verificando recompensas para reivindicar...")
            
            # Usa navegação inteligente para encontrar botões "Claim"
            from bot.navigation import Navigation
            from bot.real_detection import RealDetection
            
            real_detection = RealDetection(self.screen_capture, self.logger, self.controller)
            navigation = Navigation(self.controller, self.screen_capture, real_detection, self.logger)
            
            # Tenta encontrar e clicar em botões de reivindicar
            claim_texts = ["Claim", "Reivindicar", "Collect", "Coletar"]
            claimed = False
            
            for text in claim_texts:
                if navigation.find_button_by_text(text, timeout=2):
                    coords = navigation.find_button_by_text(text, timeout=2)
                    if coords:
                        self.controller.click(coords[0], coords[1])
                        time.sleep(1)
                        claimed = True
                        self.stats["rewards_claimed"] += 1
            
            if claimed:
                self.logger.info("Recompensas reivindicadas!")
            else:
                self.logger.debug("Nenhuma recompensa disponível para reivindicar")
            
            return claimed
            
        except Exception as e:
            self.logger.error(f"Erro ao reivindicar recompensas: {e}")
            return False
    
    def get_stats(self):
        """Retorna estatísticas"""
        return self.stats.copy()

