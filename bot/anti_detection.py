"""
Módulo Anti-Detecção - Torna o bot indetectável
Implementa técnicas avançadas para evitar detecção pela EA
"""

import time
import random
import datetime
from collections import deque

class AntiDetection:
    """Sistema anti-detecção avançado"""
    
    def __init__(self, config, logger, adaptive_system=None):
        self.config = config
        self.logger = logger
        self.adaptive_system = adaptive_system  # Sistema adaptativo
        self.anti_config = config.get("anti_detection", {})
        
        # Histórico de ações para evitar padrões
        self.action_history = deque(maxlen=100)
        self.timing_history = deque(maxlen=50)
        
        # Estatísticas de sessão
        self.session_start = time.time()
        self.actions_count = 0
        self.last_break_time = time.time()
        
        # Configurações anti-detecção
        self.max_session_hours = self.anti_config.get("max_session_hours", 4)
        self.min_break_duration = self.anti_config.get("min_break_duration", 1800)  # 30 min
        self.max_break_duration = self.anti_config.get("max_break_duration", 7200)  # 2 horas
        self.break_probability = self.anti_config.get("break_probability", 0.15)  # 15% chance
        
        # Variação de horários
        self.avoid_peak_hours = self.anti_config.get("avoid_peak_hours", True)
        self.peak_hours_start = self.anti_config.get("peak_hours_start", 18)  # 18:00
        self.peak_hours_end = self.anti_config.get("peak_hours_end", 23)  # 23:00
        
        # Limites diários
        self.max_daily_matches = self.anti_config.get("max_daily_matches", 20)
        self.max_daily_trades = self.anti_config.get("max_daily_trades", 50)
        
        # Contadores diários
        self.daily_matches = 0
        self.daily_trades = 0
        self.last_reset_date = datetime.date.today()
        
        # Análise de sequências (evita padrões repetitivos)
        self.sequence_history = deque(maxlen=20)
        self.last_sequence = []
        
        # Variação de performance (simula dias bons/ruins)
        self.performance_factor = random.uniform(0.85, 1.15)
        self.performance_update_time = time.time()
        
        # Erros ocasionais (humanos cometem erros)
        # Usa parâmetro adaptativo se disponível
        if self.adaptive_system:
            self.error_probability = self.adaptive_system.get_adaptive_parameters("error_probability") or 0.02
        else:
            self.error_probability = self.anti_config.get("error_probability", 0.02)  # 2% chance
        self.error_types = ["miss_click", "wrong_key", "delay_too_long", "cancel_action"]
        
        # Variação de dias da semana
        self.weekday_variation = self.anti_config.get("weekday_variation", True)
        self.weekday_weights = {
            0: 0.6,  # Segunda - menos jogado
            1: 0.7,  # Terça
            2: 0.8,  # Quarta
            3: 0.9,  # Quinta
            4: 1.0,  # Sexta - mais jogado
            5: 0.9,  # Sábado
            6: 0.8   # Domingo
        }
        
        # Variação de precisão (humanos não são 100% precisos)
        # Usa parâmetro adaptativo se disponível
        if self.adaptive_system:
            base_precision = self.adaptive_system.get_adaptive_parameters("precision") or 0.95
            self.click_accuracy = random.uniform(base_precision - 0.03, base_precision)
            self.key_accuracy = random.uniform(base_precision, base_precision + 0.02)
        else:
            self.click_accuracy = random.uniform(0.92, 0.98)  # 92-98% de precisão
            self.key_accuracy = random.uniform(0.95, 0.99)   # 95-99% de precisão
        
        # Tempo de reação variável
        # Usa parâmetro adaptativo se disponível
        if self.adaptive_system:
            self.reaction_time_base = self.adaptive_system.get_adaptive_parameters("reaction_time_base") or 0.20
            self.reaction_time_variation = random.uniform(0.05, 0.15)
        else:
            self.reaction_time_base = random.uniform(0.15, 0.35)  # 150-350ms
            self.reaction_time_variation = random.uniform(0.05, 0.15)
        
        # Padrões de uso realistas
        self.usage_patterns = self.anti_config.get("realistic_usage", True)
        self.skip_days_probability = 0.15  # 15% chance de não jogar em um dia
        
    def reset_daily_counters(self):
        """Reseta contadores diários"""
        today = datetime.date.today()
        if today != self.last_reset_date:
            self.daily_matches = 0
            self.daily_trades = 0
            self.last_reset_date = today
            self.logger.info("Contadores diários resetados")
    
    def should_take_break(self):
        """Decide se deve fazer uma pausa longa"""
        self.reset_daily_counters()
        
        # Verifica tempo de sessão
        session_duration = time.time() - self.session_start
        if session_duration > (self.max_session_hours * 3600):
            self.logger.info(f"Sessão muito longa ({session_duration/3600:.1f}h). Pausa recomendada.")
            return True
        
        # Verifica probabilidade de pausa
        if random.random() < self.break_probability:
            time_since_last_break = time.time() - self.last_break_time
            if time_since_last_break > (self.min_break_duration * 0.5):
                return True
        
        return False
    
    def take_break(self):
        """Faz uma pausa longa (simula jogador humano)"""
        break_duration = random.uniform(self.min_break_duration, self.max_break_duration)
        break_hours = break_duration / 3600
        
        self.logger.warning(f"⏸️ PAUSA ANTI-DETECÇÃO: {break_hours:.1f} horas")
        self.logger.warning("Simulando comportamento humano - jogador fazendo pausa")
        
        self.last_break_time = time.time()
        return break_duration
    
    def is_peak_hour(self):
        """Verifica se está em horário de pico"""
        if not self.avoid_peak_hours:
            return False
        
        current_hour = datetime.datetime.now().hour
        return self.peak_hours_start <= current_hour < self.peak_hours_end
    
    def should_avoid_action(self):
        """Decide se deve evitar ação no momento"""
        # Verifica se deve pular o dia
        if self.should_skip_today():
            self.logger.info("Pulando dia (simula jogador que não joga todos os dias)")
            return True
        
        # Evita horários de pico
        if self.is_peak_hour() and random.random() < 0.3:  # 30% chance de evitar
            return True
        
        # Verifica modificador do dia da semana
        weekday_mod = self.get_weekday_modifier()
        if weekday_mod < 0.7 and random.random() < 0.4:  # 40% chance em dias menos jogados
            return True
        
        return False
    
    def add_action_to_history(self, action_type, timing):
        """Adiciona ação ao histórico para análise de padrões"""
        self.action_history.append({
            "type": action_type,
            "time": time.time(),
            "timing": timing
        })
        self.timing_history.append(timing)
        self.actions_count += 1
    
    def get_varied_timing(self, base_min, base_max, action_type=None):
        """Retorna timing variado baseado no histórico para evitar padrões"""
        # Calcula média do histórico
        if len(self.timing_history) > 10:
            avg_timing = sum(self.timing_history) / len(self.timing_history)
            std_timing = (sum((t - avg_timing)**2 for t in self.timing_history) / len(self.timing_history))**0.5
        else:
            avg_timing = (base_min + base_max) / 2
            std_timing = (base_max - base_min) / 4
        
        # Gera timing com variação baseada no histórico
        timing = random.gauss(avg_timing, std_timing * 0.5)
        
        # Adiciona variação aleatória extra
        timing += random.uniform(-(base_max - base_min) * 0.2, (base_max - base_min) * 0.2)
        
        # Limita aos extremos
        timing = max(base_min * 0.5, min(base_max * 2, timing))
        
        # Adiciona ao histórico
        if action_type:
            self.add_action_to_history(action_type, timing)
        
        return timing
    
    def check_daily_limits(self, action_type):
        """Verifica limites diários"""
        self.reset_daily_counters()
        
        if action_type == "match":
            if self.daily_matches >= self.max_daily_matches:
                self.logger.warning(f"Limite diário de partidas atingido ({self.max_daily_matches})")
                return False
            self.daily_matches += 1
            return True
        
        elif action_type == "trade":
            if self.daily_trades >= self.max_daily_trades:
                self.logger.warning(f"Limite diário de trades atingido ({self.max_daily_trades})")
                return False
            self.daily_trades += 1
            return True
        
        return True
    
    def get_human_like_delay(self, context="general"):
        """Retorna delay que parece humano baseado no contexto"""
        # Delays diferentes para contextos diferentes
        delays = {
            "menu_navigation": (0.8, 2.5),
            "button_click": (0.3, 1.2),
            "text_input": (0.5, 1.8),
            "match_action": (0.2, 0.8),
            "thinking": (1.5, 4.0),
            "general": (0.5, 2.0)
        }
        
        base_min, base_max = delays.get(context, delays["general"])
        
        # Ocasionalmente adiciona delay extra (simula distração)
        if random.random() < 0.1:  # 10% chance
            base_max *= 2
        
        return self.get_varied_timing(base_min, base_max, context)
    
    def randomize_mouse_path(self, start_x, start_y, end_x, end_y):
        """Cria caminho de mouse completamente aleatório"""
        # Adiciona múltiplos pontos intermediários aleatórios
        num_points = random.randint(2, 5)
        points = [(start_x, start_y)]
        
        for i in range(1, num_points):
            t = i / num_points
            # Posição base
            base_x = start_x + (end_x - start_x) * t
            base_y = start_y + (end_y - start_y) * t
            
            # Adiciona variação aleatória
            offset_x = random.randint(-50, 50)
            offset_y = random.randint(-50, 50)
            
            points.append((int(base_x + offset_x), int(base_y + offset_y)))
        
        points.append((end_x, end_y))
        return points
    
    def add_micro_pauses(self):
        """Adiciona micro-pausas aleatórias (simula processamento humano)"""
        if random.random() < 0.15:  # 15% chance
            pause = random.uniform(0.1, 0.5)
            time.sleep(pause)
    
    def vary_action_intensity(self):
        """Varia intensidade das ações (simula cansaço/energia)"""
        # Simula que às vezes o jogador está mais "cansado" ou mais "energético"
        intensity = random.gauss(1.0, 0.3)  # Média 1.0, desvio 0.3
        intensity = max(0.5, min(1.5, intensity))  # Limita entre 0.5 e 1.5
        
        return intensity
    
    def should_skip_today(self):
        """Decide se deve pular o dia (simula jogador que não joga todos os dias)"""
        if not self.usage_patterns:
            return False
        
        # Verifica se já jogou hoje
        if self.daily_matches > 0 or self.daily_trades > 0:
            return False
        
        # Chance de não jogar baseada no dia da semana
        weekday = datetime.date.today().weekday()
        weight = self.weekday_weights.get(weekday, 1.0)
        
        # Menor chance de jogar em dias com menor peso
        skip_chance = (1.0 - weight) * self.skip_days_probability
        
        return random.random() < skip_chance
    
    def get_weekday_modifier(self):
        """Retorna modificador baseado no dia da semana"""
        if not self.weekday_variation:
            return 1.0
        
        weekday = datetime.date.today().weekday()
        return self.weekday_weights.get(weekday, 1.0)
    
    def update_performance_factor(self):
        """Atualiza fator de performance (simula dias bons/ruins)"""
        # Atualiza a cada hora
        if time.time() - self.performance_update_time > 3600:
            # Variação gradual (não muda drasticamente)
            change = random.uniform(-0.1, 0.1)
            self.performance_factor += change
            self.performance_factor = max(0.7, min(1.3, self.performance_factor))
            self.performance_update_time = time.time()
            self.logger.debug(f"Performance factor atualizado: {self.performance_factor:.2f}")
    
    def should_make_error(self):
        """Decide se deve cometer um erro (simula erro humano)"""
        # Atualiza probabilidade de erro do sistema adaptativo
        if self.adaptive_system:
            self.error_probability = self.adaptive_system.get_adaptive_parameters("error_probability") or 0.02
        
        # Erros são mais comuns quando "cansado" (performance baixa)
        error_chance = self.error_probability
        if self.performance_factor < 0.9:
            error_chance *= 1.5  # 50% mais chance de erro
        
        return random.random() < error_chance
    
    def get_error_type(self):
        """Retorna tipo de erro aleatório"""
        return random.choice(self.error_types)
    
    def check_sequence_pattern(self, current_sequence):
        """Verifica se sequência é repetitiva (anti-detecção)"""
        if len(current_sequence) < 3:
            return False
        
        # Verifica se sequência aparece muito no histórico
        sequence_str = "->".join(str(x) for x in current_sequence[-3:])
        
        count = sum(1 for seq in self.sequence_history if sequence_str in seq)
        
        if count > 2:  # Apareceu mais de 2 vezes
            self.logger.warning(f"Sequência repetitiva detectada: {sequence_str}. Variando...")
            return True
        
        self.sequence_history.append(sequence_str)
        return False
    
    def get_reaction_time(self):
        """Retorna tempo de reação variável (simula humano)"""
        # Varia baseado em performance e fadiga
        base = self.reaction_time_base
        variation = self.reaction_time_variation * (2 - self.performance_factor)
        
        reaction_time = random.gauss(base, variation)
        reaction_time = max(0.1, min(0.5, reaction_time))  # Limita entre 100-500ms
        
        return reaction_time
    
    def get_click_offset(self):
        """Retorna offset aleatório para cliques (simula imprecisão humana)"""
        # Humanos não clicam exatamente no centro
        max_offset = int((1.0 - self.click_accuracy) * 10)  # Offset baseado em precisão
        offset_x = random.randint(-max_offset, max_offset)
        offset_y = random.randint(-max_offset, max_offset)
        
        return (offset_x, offset_y)
    
    def should_miss_key(self):
        """Decide se deve errar uma tecla (simula erro de digitação)"""
        miss_chance = 1.0 - self.key_accuracy
        return random.random() < miss_chance
    
    def get_session_stats(self):
        """Retorna estatísticas da sessão"""
        session_duration = time.time() - self.session_start
        weekday = datetime.date.today().weekday()
        weekday_name = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"][weekday]
        
        return {
            "duration_hours": session_duration / 3600,
            "actions_count": self.actions_count,
            "daily_matches": self.daily_matches,
            "daily_trades": self.daily_trades,
            "is_peak_hour": self.is_peak_hour(),
            "performance_factor": self.performance_factor,
            "weekday": weekday_name,
            "click_accuracy": self.click_accuracy,
            "key_accuracy": self.key_accuracy
        }
    
    def add_action_sequence(self, action_type):
        """Adiciona ação à sequência atual"""
        self.last_sequence.append(action_type)
        if len(self.last_sequence) > 5:
            self.last_sequence.pop(0)
        
        # Verifica padrões repetitivos
        if self.check_sequence_pattern(self.last_sequence):
            # Varia a sequência
            self.last_sequence = []
    
    def get_varied_action_timing(self, base_timing, action_type):
        """Retorna timing variado considerando todos os fatores"""
        # Modificadores
        weekday_mod = self.get_weekday_modifier()
        self.update_performance_factor()
        performance_mod = self.performance_factor
        
        # Timing base com modificadores
        varied_timing = base_timing * weekday_mod * performance_mod
        
        # Adiciona variação aleatória
        varied_timing *= random.uniform(0.9, 1.1)
        
        # Adiciona à sequência
        self.add_action_sequence(action_type)
        
        return varied_timing

