"""
Classe base para módulos do bot
"""

class BaseModule:
    """Classe base para todos os módulos do bot"""
    
    def __init__(self, config, controller, screen_capture, logger):
        self.config = config
        self.controller = controller
        self.screen_capture = screen_capture
        self.logger = logger
    
    def run_cycle(self):
        """Método abstrato - deve ser implementado pelas subclasses"""
        raise NotImplementedError("Subclasses devem implementar run_cycle()")

