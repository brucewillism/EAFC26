"""
Módulo de Gerenciamento de Time - Cria e gerencia time
"""

import time
import random
from bot.controller import Controller
from bot.screen_capture import ScreenCapture
from bot.real_detection import RealDetection

class TeamManager:
    """Gerencia criação e configuração do time"""
    
    def __init__(self, config, controller, screen_capture, logger):
        self.config = config
        self.controller = controller
        self.screen_capture = screen_capture
        self.logger = logger
        
        # Inicializa detecção real
        self.real_detection = RealDetection(screen_capture, logger, controller)
        
        self.team_config = config.get("team", {})
        self.team_name = self.team_config.get("name", "")
        self.auto_create = self.team_config.get("auto_create", True)
        
        # Verifica se time existe
        self.team_exists = None

    def prepare_squad_for_requirement(self, requirement: dict):
        """
        Ajusta elenco para um requisito simples (ex.: liga ou nacionalidade).
        Implementação: navega para Squad, abre busca no clube, aplica filtro (liga/nação/posição) e tenta substituir pelo primeiro resultado.
        """
        try:
            league = requirement.get("league")
            nation = requirement.get("nation")
            position = requirement.get("position")

            if not (league or nation):
                self.logger.info("Nenhum requisito de elenco especificado.")
                return True

            self.logger.info(f"Preparando elenco para requisito: league={league}, nation={nation}, position={position}")

            # Navega para Squad
            from bot.navigation import Navigation
            nav = Navigation(self.controller, self.screen_capture, self.real_detection, self.logger)

            if not nav.navigate_to_squad():
                self.logger.warning("Não foi possível navegar para Squad.")
                return False

            if not nav.open_squad_builder():
                self.logger.warning("Não foi possível abrir Squad Builder.")
                return False

            # Seleciona um slot de jogador (fallback genérico: clique no centro do campo)
            self.controller.click(960, 540)
            time.sleep(0.8)

            if not nav.open_club_search():
                self.logger.warning("Não foi possível abrir busca no clube.")
                return False

            if not nav.apply_filter(league=league, nation=nation, position=position):
                self.logger.warning("Não foi possível aplicar filtros.")
                return False

            if not nav.select_first_search_result():
                self.logger.warning("Não foi possível selecionar resultado.")
                nav.clear_filters()
                return False

            if not nav.confirm_substitution():
                self.logger.warning("Não foi possível confirmar substituição.")
                nav.clear_filters()
                return False

            nav.clear_filters()
            self.logger.info("Substituição concluída (melhor esforço).")
            return True

        except Exception as e:
            self.logger.error(f"Erro ao preparar elenco: {e}")
            return False
        
    def check_and_create_team(self, team_name=None):
        """Verifica se time existe e cria se necessário"""
        try:
            # Se auto_create está desabilitado, apenas tenta detectar o time existente
            if not self.auto_create:
                self.logger.info("Criação automática desabilitada. Tentando detectar time existente...")
                # Aguarda um pouco para garantir que está na tela correta
                time.sleep(3)
                
                # Tenta detectar nome do time
                detected_name = self.detect_existing_team_name()
                if detected_name:
                    self.team_name = detected_name
                    self.team_exists = True
                    self.logger.info(f"Time detectado: {detected_name}")
                    return True
                else:
                    self.logger.info("Time não detectado automaticamente. Continuando sem nome de time.")
                    return True  # Continua mesmo sem detectar
            
            # Se auto_create está habilitado, verifica e cria se necessário
            self.logger.info("Verificando se time já existe...")
            self.team_exists = self.real_detection.check_team_exists()
            
            if self.team_exists:
                self.logger.info("Time já existe! Não precisa criar.")
                # Tenta detectar nome do time existente
                self.detect_existing_team_name()
                return True
            
            # Time não existe, precisa criar
            self.logger.info("Time não encontrado. Criando novo time...")
            return self.create_team(team_name)
            
        except Exception as e:
            self.logger.error(f"Erro ao verificar/criar time: {e}")
            return False
    
    def detect_existing_team_name(self):
        """Tenta detectar nome do time existente"""
        try:
            # Captura tela e procura nome do time
            screenshot = self.screen_capture.capture_screen()
            if screenshot is None:
                return None
            
            screen_width = screenshot.shape[1]
            screen_height = screenshot.shape[0]
            
            # Região onde geralmente aparece nome do time
            team_name_region = (
                screen_width//4,
                screen_height//4,
                screen_width*3//4,
                screen_height//2
            )
            
            team_name = self.real_detection.read_text_from_region(team_name_region)
            if team_name and len(team_name) > 2:
                self.team_name = team_name
                self.logger.info(f"Nome do time detectado: {team_name}")
                return team_name
            
            return None
        except Exception as e:
            self.logger.debug(f"Erro ao detectar nome do time: {e}")
            return None
    
    def create_team(self, team_name=None):
        """Cria um novo time e verifica se foi salvo no servidor"""
        try:
            if team_name is None:
                team_name = self.team_name or self.generate_team_name()
            
            self.logger.info(f"Criando time: {team_name}")
            
            # Navega para criação de time
            if not self.navigate_to_team_creation():
                self.logger.error("Não foi possível navegar para criação de time")
                return False
            
            # Aguarda tela carregar
            time.sleep(2)
            
            # Preenche nome do time
            if not self.enter_team_name(team_name):
                self.logger.error("Não foi possível preencher nome do time")
                return False
            
            # Aguarda um pouco antes de confirmar
            time.sleep(1)
            
            # Confirma criação e aguarda salvamento
            if not self.confirm_team_creation():
                self.logger.error("Falha ao confirmar criação do time")
                return False
            
            # Verifica se o time foi realmente criado (aguarda sincronização)
            self.logger.info("Aguardando sincronização com servidor...")
            time.sleep(10)  # Aguarda sincronização com servidor da EA
            
            # Tenta verificar se o time existe agora
            self.logger.info("Verificando se time foi salvo no servidor...")
            time.sleep(3)
            
            # Verifica novamente se o time existe
            # Nota: A verificação pode falhar se a detecção não estiver calibrada
            # Por isso, assumimos sucesso se não houver erros explícitos
            team_exists_now = self.real_detection.check_team_exists()
            
            if team_exists_now:
                self.team_name = team_name
                self.team_exists = True
                self.logger.info(f"Time '{team_name}' criado e salvo com sucesso no servidor!")
                return True
            else:
                # Se a detecção não funcionou, assume sucesso se não houve erros
                # A verificação manual no app do celular é mais confiável
                self.logger.warning("Não foi possível verificar automaticamente se time foi salvo.")
                self.logger.info("Por favor, verifique manualmente no app do celular se o time foi criado.")
                self.logger.info("Se o time não aparecer, você pode criar manualmente ou tentar novamente.")
                
                # Marca como criado localmente para não tentar criar novamente nesta sessão
                # Mas permite tentar novamente na próxima execução se necessário
                self.team_name = team_name
                self.team_exists = None  # Não confirma, mas não tenta criar novamente agora
                return True  # Retorna True para continuar, mas com aviso
            
        except Exception as e:
            self.logger.error(f"Erro ao criar time: {e}")
            return False
    
    def generate_team_name(self):
        """Gera nome aleatório para o time"""
        prefixes = ["FC", "United", "City", "Athletic", "Sporting", "Real", "Atletico"]
        suffixes = ["United", "City", "FC", "Athletic", "Sporting", "Wanderers", "Rovers"]
        cities = ["London", "Madrid", "Barcelona", "Manchester", "Liverpool", "Milan", "Paris"]
        
        # Gera nome aleatório
        if random.random() < 0.5:
            # Formato: City FC
            name = f"{random.choice(cities)} {random.choice(prefixes)}"
        else:
            # Formato: FC City
            name = f"{random.choice(prefixes)} {random.choice(cities)}"
        
        return name
    
    def navigate_to_team_creation(self):
        """Navega para criação de time"""
        try:
            self.logger.info("Navegando para tela de criação de time...")
            
            # Aguarda um pouco para garantir que está na tela correta
            time.sleep(2)
            
            # Verifica em qual tela está
            current_screen = self.real_detection.detect_current_screen()
            self.logger.info(f"Tela atual detectada: {current_screen}")
            
            # Se já está na tela de criação ou Ultimate Team, pode estar ok
            if current_screen in ["ultimate_team", "unknown"]:
                # Tenta navegar para criação de time
                # No EA FC, geralmente precisa:
                # 1. Ir para "My Club" ou "Ultimate Team"
                # 2. Procurar opção "Create Squad" ou "New Squad"
                
                # Por enquanto, assume que já está na tela correta ou tenta navegar
                # Pressiona algumas teclas de navegação comuns
                self.controller.press_key('enter')
                time.sleep(1)
                
                # Tenta navegar com setas (ajustar conforme necessário)
                # self.controller.press_key('down')
                # time.sleep(0.5)
                # self.controller.press_key('enter')
                # time.sleep(1)
            
            # Aguarda tela carregar
            time.sleep(2)
            
            self.logger.info("Navegação para criação de time concluída")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao navegar para criação de time: {e}")
            return False
    
    def enter_team_name(self, team_name):
        """Preenche nome do time"""
        try:
            self.logger.info(f"Preenchendo nome do time: {team_name}")
            
            # Aguarda campo estar pronto
            time.sleep(1)
            
            # Clica no campo de nome (coordenadas precisam ser calibradas)
            # Por enquanto, assume que o campo já está focado ou tenta focar
            # self.controller.click(name_field_x, name_field_y)
            
            # Limpa campo se necessário (pode ter texto padrão)
            self.controller.key_combination('ctrl', 'a')
            time.sleep(0.5)
            
            # Digita nome do time com velocidade humana
            self.logger.info("Digitando nome do time...")
            self.controller.type_text(team_name, human_typing=True)
            time.sleep(1)  # Aguarda digitação completar
            
            # Verifica se o texto foi digitado (opcional - pode usar OCR)
            # Por enquanto, assume que foi digitado corretamente
            
            self.logger.info("Nome do time preenchido")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao preencher nome do time: {e}")
            return False
    
    def confirm_team_creation(self):
        """Confirma criação do time e aguarda salvamento no servidor"""
        try:
            self.logger.info("Confirmando criação do time...")
            
            # Pressiona ENTER para confirmar
            self.controller.press_key('enter')
            time.sleep(1)
            
            # Aguarda processamento/salvamento (pode demorar)
            self.logger.info("Aguardando salvamento no servidor...")
            time.sleep(5)  # Aguarda sincronização com servidor
            
            # Verifica se houve erro ou confirmação
            # Tenta detectar mensagens de sucesso/erro na tela
            screenshot = self.screen_capture.capture_screen()
            if screenshot is not None:
                # Procura por indicadores de sucesso ou erro
                screen_text = self.real_detection.read_text_from_region(
                    (0, 0, screenshot.shape[1], screenshot.shape[0]//3),
                    config='--psm 7'
                )
                
                if screen_text:
                    text_lower = screen_text.lower()
                    # Verifica se há mensagens de erro
                    error_keywords = ['error', 'erro', 'failed', 'falhou', 'try again', 'tente novamente']
                    if any(keyword in text_lower for keyword in error_keywords):
                        self.logger.warning("Possível erro na criação do time. Tentando novamente...")
                        return False
            
            # Aguarda mais um pouco para garantir sincronização
            time.sleep(3)
            
            # Verifica se o time foi realmente criado
            self.logger.info("Verificando se time foi criado com sucesso...")
            time.sleep(2)
            
            # Tenta verificar se está na tela principal do Ultimate Team (indica sucesso)
            current_screen = self.real_detection.detect_current_screen()
            if current_screen in ["ultimate_team", "squad_battles", "transfer_market"]:
                self.logger.info("Time criado com sucesso! Navegação confirmada.")
                return True
            
            # Se não detectou tela específica, aguarda mais e assume sucesso
            self.logger.info("Aguardando sincronização final...")
            time.sleep(5)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao confirmar criação: {e}")
            return False

