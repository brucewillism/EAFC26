"""
Sistema Adaptativo - Ajusta automaticamente a mudanças de detecção da EA
"""

import time
import random
import json
import os
from datetime import datetime, timedelta
from collections import deque
import statistics

class AdaptiveSystem:
    """Sistema que se adapta automaticamente a mudanças de detecção"""
    
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger
        self.adaptive_config = config.get("adaptive_system", {})
        
        # Arquivo de histórico e aprendizado
        self.learning_file = "adaptive_learning.json"
        self.stats_file = "adaptive_stats.json"
        
        # Carrega histórico de aprendizado
        self.learning_data = self.load_learning_data()
        self.stats = self.load_stats()
        
        # Níveis de risco detectados
        self.risk_levels = {
            "low": 0,
            "medium": 1,
            "high": 2,
            "critical": 3
        }
        self.current_risk = "low"
        
        # Perfis de comportamento
        self.behavior_profiles = {
            "conservative": {
                "error_probability": 0.03,
                "delay_multiplier": 1.5,
                "break_probability": 0.25,
                "max_daily_matches": 15,
                "max_daily_trades": 30,
                "precision": 0.92,
                "reaction_time_base": 0.25
            },
            "normal": {
                "error_probability": 0.02,
                "delay_multiplier": 1.0,
                "break_probability": 0.15,
                "max_daily_matches": 20,
                "max_daily_trades": 50,
                "precision": 0.95,
                "reaction_time_base": 0.20
            },
            "aggressive": {
                "error_probability": 0.01,
                "delay_multiplier": 0.7,
                "break_probability": 0.10,
                "max_daily_matches": 25,
                "max_daily_trades": 70,
                "precision": 0.97,
                "reaction_time_base": 0.15
            }
        }
        
        self.current_profile = self.adaptive_config.get("default_profile", "normal")
        
        # Histórico de detecções e ajustes
        self.detection_history = deque(maxlen=100)
        self.adjustment_history = deque(maxlen=50)
        
        # Métricas de monitoramento
        self.metrics = {
            "session_count": 0,
            "total_matches": 0,
            "total_trades": 0,
            "warnings_received": 0,
            "suspicious_events": 0,
            "last_adjustment": None,
            "adaptation_count": 0
        }
        
        # Sinais de detecção
        self.detection_signals = {
            "warning_received": False,
            "unusual_ban_rate": False,
            "pattern_detected": False,
            "performance_anomaly": False,
            "timing_anomaly": False
        }
        
        # Auto-ajuste ativado
        self.auto_adjust = self.adaptive_config.get("auto_adjust", True)
        self.adaptation_interval = self.adaptive_config.get("adaptation_interval", 3600)  # 1 hora
        self.last_adaptation = time.time()
        
    def load_learning_data(self):
        """Carrega dados de aprendizado anteriores"""
        if os.path.exists(self.learning_file):
            try:
                with open(self.learning_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "successful_profiles": [],
            "failed_profiles": [],
            "parameter_history": [],
            "detection_patterns": []
        }
    
    def save_learning_data(self):
        """Salva dados de aprendizado"""
        try:
            with open(self.learning_file, 'w', encoding='utf-8') as f:
                json.dump(self.learning_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Erro ao salvar dados de aprendizado: {e}")
    
    def load_stats(self):
        """Carrega estatísticas"""
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "sessions": [],
            "detections": [],
            "adjustments": []
        }
    
    def save_stats(self):
        """Salva estatísticas"""
        try:
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.logger.error(f"Erro ao salvar estatísticas: {e}")
    
    def detect_risk_level(self):
        """Detecta nível de risco atual"""
        risk_score = 0
        
        # Analisa histórico recente
        recent_detections = [d for d in self.detection_history if 
                           time.time() - d.get("time", 0) < 86400]  # Últimas 24h
        
        if len(recent_detections) > 5:
            risk_score += 2
        elif len(recent_detections) > 2:
            risk_score += 1
        
        # Verifica sinais de detecção
        if self.detection_signals["warning_received"]:
            risk_score += 2
        if self.detection_signals["unusual_ban_rate"]:
            risk_score += 2
        if self.detection_signals["pattern_detected"]:
            risk_score += 1
        
        # Analisa padrões de uso
        if self.metrics["suspicious_events"] > 3:
            risk_score += 1
        
        # Determina nível de risco
        if risk_score >= 5:
            self.current_risk = "critical"
        elif risk_score >= 3:
            self.current_risk = "high"
        elif risk_score >= 1:
            self.current_risk = "medium"
        else:
            self.current_risk = "low"
        
        return self.current_risk
    
    def register_detection_signal(self, signal_type, severity=1):
        """Registra sinal de possível detecção"""
        detection = {
            "type": signal_type,
            "severity": severity,
            "time": time.time(),
            "profile": self.current_profile,
            "risk_level": self.current_risk
        }
        
        self.detection_history.append(detection)
        self.detection_signals[signal_type] = True
        
        self.logger.warning(f"⚠️ Sinal de detecção: {signal_type} (severidade: {severity})")
        
        # Salva estatísticas
        self.stats["detections"].append(detection)
        self.save_stats()
        
        # Aciona adaptação se necessário
        if self.auto_adjust and severity >= 2:
            self.trigger_adaptation("detection_signal")
    
    def analyze_patterns(self):
        """Analisa padrões de detecção"""
        if len(self.detection_history) < 5:
            return None
        
        # Agrupa detecções por tipo
        detection_types = {}
        for det in self.detection_history:
            det_type = det.get("type", "unknown")
            if det_type not in detection_types:
                detection_types[det_type] = []
            detection_types[det_type].append(det)
        
        # Identifica padrões
        patterns = []
        for det_type, detections in detection_types.items():
            if len(detections) >= 3:
                # Padrão detectado
                avg_severity = statistics.mean([d.get("severity", 1) for d in detections])
                patterns.append({
                    "type": det_type,
                    "frequency": len(detections),
                    "avg_severity": avg_severity,
                    "pattern": True
                })
        
        if patterns:
            self.detection_signals["pattern_detected"] = True
            self.logger.warning(f"Padrão de detecção identificado: {patterns}")
            return patterns
        
        return None
    
    def trigger_adaptation(self, reason="scheduled"):
        """Aciona adaptação do sistema"""
        current_time = time.time()
        
        # Verifica intervalo mínimo
        if current_time - self.last_adaptation < self.adaptation_interval:
            return False
        
        self.logger.info(f"🔄 Iniciando adaptação automática (razão: {reason})")
        
        # Analisa padrões
        patterns = self.analyze_patterns()
        
        # Detecta nível de risco
        risk_level = self.detect_risk_level()
        
        # Decide novo perfil
        new_profile = self.select_optimal_profile(risk_level, patterns)
        
        # Aplica ajustes
        if new_profile != self.current_profile:
            self.apply_profile(new_profile, reason)
            self.metrics["adaptation_count"] += 1
            self.last_adaptation = current_time
            
            # Registra ajuste
            adjustment = {
                "time": current_time,
                "from_profile": self.current_profile,
                "to_profile": new_profile,
                "reason": reason,
                "risk_level": risk_level
            }
            self.adjustment_history.append(adjustment)
            self.stats["adjustments"].append(adjustment)
            self.save_stats()
            
            return True
        
        return False
    
    def select_optimal_profile(self, risk_level, patterns=None):
        """Seleciona perfil ótimo baseado em risco e padrões"""
        # Lógica de seleção baseada em risco
        if risk_level == "critical":
            return "conservative"
        elif risk_level == "high":
            return "conservative"
        elif risk_level == "medium":
            return "normal"
        else:
            # Em baixo risco, pode tentar perfil mais agressivo ocasionalmente
            if random.random() < 0.3:  # 30% chance
                return "aggressive"
            return "normal"
    
    def apply_profile(self, profile_name, reason="auto"):
        """Aplica um perfil de comportamento"""
        if profile_name not in self.behavior_profiles:
            self.logger.error(f"Perfil inválido: {profile_name}")
            return
        
        old_profile = self.current_profile
        self.current_profile = profile_name
        profile = self.behavior_profiles[profile_name]
        
        self.logger.warning(f"📊 Mudando perfil: {old_profile} → {profile_name} (razão: {reason})")
        self.logger.info(f"Parâmetros do novo perfil: {profile}")
        
        # Atualiza configuração
        self.update_config_with_profile(profile)
        
        # Salva aprendizado
        self.learning_data["successful_profiles"].append({
            "profile": profile_name,
            "time": time.time(),
            "reason": reason
        })
        self.save_learning_data()
    
    def update_config_with_profile(self, profile):
        """Atualiza configuração com parâmetros do perfil"""
        # Atualiza anti_detection no config
        if "anti_detection" not in self.config:
            self.config["anti_detection"] = {}
        
        anti_det = self.config["anti_detection"]
        
        # Aplica parâmetros do perfil
        anti_det["error_probability"] = profile.get("error_probability", 0.02)
        anti_det["break_probability"] = profile.get("break_probability", 0.15)
        anti_det["max_daily_matches"] = profile.get("max_daily_matches", 20)
        anti_det["max_daily_trades"] = profile.get("max_daily_trades", 50)
        
        # Salva configuração atualizada
        self.save_updated_config()
    
    def save_updated_config(self):
        """Salva configuração atualizada"""
        try:
            config_file = "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            self.logger.debug("Configuração atualizada salva")
        except Exception as e:
            self.logger.error(f"Erro ao salvar configuração: {e}")
    
    def evolve_parameters(self):
        """Evolui parâmetros baseado em aprendizado"""
        if len(self.learning_data["successful_profiles"]) < 3:
            return
        
        # Analisa quais perfis foram mais bem-sucedidos
        profile_success = {}
        for entry in self.learning_data["successful_profiles"]:
            profile = entry.get("profile", "normal")
            if profile not in profile_success:
                profile_success[profile] = 0
            profile_success[profile] += 1
        
        # Identifica perfil mais bem-sucedido
        if profile_success:
            best_profile = max(profile_success, key=profile_success.get)
            
            # Evolui parâmetros do perfil baseado em sucesso
            if best_profile in self.behavior_profiles:
                base_profile = self.behavior_profiles[best_profile].copy()
                
                # Pequenas variações aleatórias (evolução)
                evolved_profile = {}
                for key, value in base_profile.items():
                    if isinstance(value, (int, float)):
                        # Variação de ±5%
                        variation = random.uniform(-0.05, 0.05)
                        evolved_profile[key] = value * (1 + variation)
                    else:
                        evolved_profile[key] = value
                
                # Cria novo perfil evolutivo
                profile_name = f"{best_profile}_evolved_{int(time.time())}"
                self.behavior_profiles[profile_name] = evolved_profile
                
                self.logger.info(f"🧬 Perfil evolutivo criado: {profile_name}")
    
    def get_adaptive_parameters(self, parameter_name):
        """Retorna parâmetro adaptativo baseado no perfil atual"""
        profile = self.behavior_profiles.get(self.current_profile, self.behavior_profiles["normal"])
        
        if parameter_name == "error_probability":
            return profile.get("error_probability", 0.02)
        elif parameter_name == "delay_multiplier":
            return profile.get("delay_multiplier", 1.0)
        elif parameter_name == "break_probability":
            return profile.get("break_probability", 0.15)
        elif parameter_name == "precision":
            return profile.get("precision", 0.95)
        elif parameter_name == "reaction_time_base":
            return profile.get("reaction_time_base", 0.20)
        else:
            return None
    
    def monitor_and_adapt(self):
        """Monitora e adapta continuamente"""
        current_time = time.time()
        
        # Adaptação agendada
        if current_time - self.last_adaptation >= self.adaptation_interval:
            self.trigger_adaptation("scheduled")
        
        # Análise contínua de padrões
        patterns = self.analyze_patterns()
        if patterns:
            self.trigger_adaptation("pattern_detected")
        
        # Evolução periódica (a cada 24h)
        if current_time - self.learning_data.get("last_evolution", 0) > 86400:
            self.evolve_parameters()
            self.learning_data["last_evolution"] = current_time
            self.save_learning_data()
    
    def register_session_result(self, success=True, warnings=0):
        """Registra resultado de uma sessão"""
        session = {
            "time": time.time(),
            "success": success,
            "warnings": warnings,
            "profile": self.current_profile,
            "risk_level": self.current_risk
        }
        
        self.stats["sessions"].append(session)
        self.metrics["session_count"] += 1
        
        if warnings > 0:
            self.metrics["warnings_received"] += warnings
            self.register_detection_signal("warning_received", warnings)
        
        if not success:
            self.metrics["suspicious_events"] += 1
            self.register_detection_signal("performance_anomaly", 2)
        
        self.save_stats()
    
    def get_current_risk_level(self):
        """Retorna nível de risco atual"""
        return self.current_risk
    
    def get_current_profile(self):
        """Retorna perfil atual"""
        return self.current_profile
    
    def get_adaptation_stats(self):
        """Retorna estatísticas de adaptação"""
        return {
            "current_profile": self.current_profile,
            "current_risk": self.current_risk,
            "adaptation_count": self.metrics["adaptation_count"],
            "detection_signals": dict(self.detection_signals),
            "recent_detections": len([d for d in self.detection_history 
                                    if time.time() - d.get("time", 0) < 86400])
        }

