"""
Risk Scanner - Avalia configuração e aplica mitigação de risco de banimento.
"""

from copy import deepcopy


class RiskScanner:
    """Avalia e aplica mitigação de risco."""

    ABS_MAX_TRADES = 60
    ABS_MAX_MATCHES = 12
    DEFAULT_PROFILES = {
        "safe": {
            "max_daily_trades": 30,
            "max_daily_matches": 6,
            "min_delay": 1.0,
            "max_delay": 3.0,
            "coin_transfer_enabled": False,
        },
        "normal": {
            "max_daily_trades": 40,
            "max_daily_matches": 8,
            "min_delay": 0.8,
            "max_delay": 2.5,
            "coin_transfer_enabled": False,
        },
        "aggressive": {
            "max_daily_trades": 50,
            "max_daily_matches": 10,
            "min_delay": 0.5,
            "max_delay": 2.0,
            "coin_transfer_enabled": False,
        },
    }

    @classmethod
    def assess(cls, config: dict) -> dict:
        """Retorna avaliação de risco sem alterar config."""
        cfg = deepcopy(config)
        risk = "low"
        reasons = []
        suggestions = []

        anti = cfg.get("anti_detection", {})
        trading = cfg.get("trading", {})
        squad = cfg.get("squad_battles", {})
        coin = cfg.get("coin_transfer", {})
        safety = cfg.get("safety", {})
        risk_cfg = cfg.get("risk", {})

        max_trades = anti.get("max_daily_trades", 50)
        max_matches = anti.get("max_daily_matches", 20)
        coin_enabled = coin.get("enabled", False)
        random_delays = safety.get("random_delays", True)
        min_delay = safety.get("min_delay", 0.5)
        max_delay = safety.get("max_delay", 2.0)
        risk_mode = risk_cfg.get("mode", "normal")

        # Heurísticas simples de risco
        if coin_enabled:
            reasons.append("Transferência de coins ligada")
        if max_trades > 50:
            reasons.append(f"Muitos trades/dia ({max_trades})")
        if max_matches > 10:
            reasons.append(f"Muitas partidas/dia ({max_matches})")
        if not random_delays or min_delay < 0.5:
            reasons.append("Delays muito baixos/pouco aleatórios")
        if risk_mode == "aggressive":
            reasons.append("Perfil agressivo selecionado")

        # Classificação
        if reasons:
            risk = "high" if any([
                coin_enabled,
                max_trades > 50,
                max_matches > 10,
                risk_mode == "aggressive",
            ]) else "medium"
        else:
            risk = "low"

        # Sugestões
        safe_profile = cls.DEFAULT_PROFILES["safe"]
        if max_trades > safe_profile["max_daily_trades"]:
            suggestions.append("Reduzir trades/dia para <= 30 (safe)")
        if max_matches > safe_profile["max_daily_matches"]:
            suggestions.append("Reduzir partidas/dia para <= 6 (safe)")
        if coin_enabled:
            suggestions.append("Desativar transferência de coins ou usar valores baixos")
        if min_delay < safe_profile["min_delay"]:
            suggestions.append("Aumentar min_delay para >= 1.0s")
        if max_delay < safe_profile["max_delay"]:
            suggestions.append("Aumentar max_delay para >= 3.0s")

        return {
            "risk": risk,
            "reasons": reasons,
            "suggestions": suggestions,
            "risk_mode": risk_mode,
        }

    @classmethod
    def apply_mitigations(cls, config: dict, logger=None) -> tuple[dict, dict]:
        """
        Aplica mitigação (hard caps + modo safe) e retorna (config_atualizada, report).
        """
        cfg = deepcopy(config)
        report = cls.assess(cfg)
        risk_cfg = cfg.setdefault("risk", {})
        risk_mode = risk_cfg.get("mode", "safe")
        profiles = risk_cfg.get("profiles", cls.DEFAULT_PROFILES)
        profile = profiles.get(risk_mode, cls.DEFAULT_PROFILES["safe"])

        anti = cfg.setdefault("anti_detection", {})
        safety = cfg.setdefault("safety", {})
        coin = cfg.setdefault("coin_transfer", {})

        original_trades = anti.get("max_daily_trades", 50)
        original_matches = anti.get("max_daily_matches", 20)

        # Hard caps absolutos
        anti["max_daily_trades"] = min(original_trades, cls.ABS_MAX_TRADES)
        anti["max_daily_matches"] = min(original_matches, cls.ABS_MAX_MATCHES)

        # Aplica perfil selecionado (limites e delays)
        anti["max_daily_trades"] = min(anti["max_daily_trades"], profile.get("max_daily_trades", anti["max_daily_trades"]))
        anti["max_daily_matches"] = min(anti["max_daily_matches"], profile.get("max_daily_matches", anti["max_daily_matches"]))
        safety["min_delay"] = max(safety.get("min_delay", 0.5), profile.get("min_delay", 0.5))
        safety["max_delay"] = max(safety.get("max_delay", 2.0), profile.get("max_delay", 2.0))
        safety["random_delays"] = True
        # Coin transfer segue perfil
        coin_enabled_profile = profile.get("coin_transfer_enabled", False)
        coin["enabled"] = coin.get("enabled", False) and coin_enabled_profile

        # Reavaliar após mitigação
        mitigated_report = cls.assess(cfg)

        # Log opcional
        if logger:
            logger.info(f"[RISK] Risco detectado: {report['risk']} ({', '.join(report['reasons']) or 'sem alertas'})")
            logger.info(f"[RISK] Modo: {mitigated_report.get('risk_mode', risk_mode)} | "
                        f"Trades/dia: {anti['max_daily_trades']} | Partidas/dia: {anti['max_daily_matches']}")
            if mitigated_report["suggestions"]:
                logger.info(f"[RISK] Sugestões: {mitigated_report['suggestions']}")

        return cfg, mitigated_report

