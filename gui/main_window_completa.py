"""
Interface Gráfica Completa do Bot - EA FC 26
Com todas as funcionalidades: Trading, Squad Battles, Objetivos, Transferência de Coins
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import threading
import queue
import sys
import os
import json
import time
from datetime import datetime

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import EAFCBot
from utils.risk_scanner import RiskScanner

class BotGUICompleta:
    """Interface gráfica completa do bot com todas as funcionalidades"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("EA FC 26 Bot - Interface Completa")
        self.root.geometry("1200x900")
        self.root.resizable(True, True)
        
        # Aplica tema dark
        self.setup_dark_theme()
        
        # Variáveis
        self.bot = None
        self.bot_thread = None
        self.is_running = False
        self.is_paused = False
        self.risk_info_var = tk.StringVar(value="Risco: desconhecido")
        
        # Queue para comunicação entre threads
        self.log_queue = queue.Queue()
        
        # Variáveis de configuração
        self.email_var = tk.StringVar()
        self.password_var = tk.StringVar()
        self.secondary_email_var = tk.StringVar()  # Conta secundária para coins
        self.remember_var = tk.BooleanVar()
        
        # Variáveis de módulos
        self.trading_enabled = tk.BooleanVar(value=True)
        self.squad_battles_enabled = tk.BooleanVar(value=True)
        self.objectives_enabled = tk.BooleanVar(value=True)
        self.coin_transfer_enabled = tk.BooleanVar(value=False)
        self.comfort_trade_enabled = tk.BooleanVar(value=False)
        self.risk_mode_var = tk.StringVar(value="safe")
        
        # Variáveis de Comfort Trade
        self.comfort_client_email_var = tk.StringVar()
        self.comfort_client_password_var = tk.StringVar()
        self.comfort_target_coins_var = tk.StringVar(value="0")
        self.comfort_method_var = tk.StringVar(value="market")
        
        # Variáveis de configuração avançada
        self.min_profit_var = tk.StringVar(value="500")
        self.max_price_var = tk.StringVar(value="10000")
        self.difficulty_var = tk.StringVar(value="World Class")
        self.auto_claim_rewards = tk.BooleanVar(value=True)
        
        # Carrega configurações
        self.load_config()
        
        # Cria interface
        self.create_widgets()
        
        # Inicia atualização
        self.update_logs()
        self.update_stats()
        self.update_risk_preview()
    
    def setup_dark_theme(self):
        """Configura tema dark para a interface"""
        # Paleta de cores moderna e vibrante
        self.bg_color = "#1a1a2e"  # Fundo principal (azul escuro profundo)
        self.fg_color = "#eaeaea"  # Texto principal (branco suave)
        self.entry_bg = "#16213e"  # Fundo de campos (azul escuro)
        self.entry_fg = "#ffffff"  # Texto de campos
        self.frame_bg = "#0f3460"  # Fundo de frames (azul médio escuro)
        self.border_color = "#533483"  # Cor de bordas (roxo)
        self.select_bg = "#00d4ff"  # Cor de seleção (ciano vibrante)
        self.select_fg = "#000000"  # Texto selecionado
        self.button_bg = "#533483"  # Fundo de botões (roxo)
        self.button_hover = "#6a4c93"  # Hover de botões (roxo claro)
        self.tab_bg = "#16213e"  # Fundo de tabs
        self.tab_active = "#1a1a2e"  # Tab ativa
        self.accent_color = "#00d4ff"  # Cor de destaque (ciano)
        self.success_color = "#00ff88"  # Verde sucesso
        self.warning_color = "#ffaa00"  # Laranja aviso
        self.error_color = "#ff3366"  # Vermelho erro
        
        # Configura root
        self.root.configure(bg=self.bg_color)
        
        # Configura estilo ttk
        style = ttk.Style()
        style.theme_use('clam')  # Base para customização
        
        # Configura cores dos componentes ttk
        style.configure('TFrame', background=self.frame_bg, borderwidth=0)
        style.configure('TLabel', background=self.frame_bg, foreground=self.fg_color)
        style.configure('TLabelFrame', background=self.frame_bg, foreground=self.fg_color, 
                       bordercolor=self.accent_color, borderwidth=2, relief='solid')
        style.configure('TLabelFrame.Label', background=self.frame_bg, foreground=self.accent_color, 
                       font=('', 9, 'bold'))
        style.configure('TButton', background=self.button_bg, foreground=self.fg_color, 
                       borderwidth=2, bordercolor=self.accent_color, focuscolor='none',
                       font=('', 9, 'bold'))
        style.map('TButton', 
                 background=[('active', self.button_hover), ('pressed', self.entry_bg)],
                 bordercolor=[('active', self.accent_color), ('pressed', self.accent_color)])
        style.configure('TEntry', fieldbackground=self.entry_bg, foreground=self.entry_fg, 
                       borderwidth=2, bordercolor=self.border_color, insertcolor=self.accent_color)
        style.map('TEntry', bordercolor=[('focus', self.accent_color)])
        style.configure('TCheckbutton', background=self.frame_bg, foreground=self.fg_color, 
                       focuscolor='none', font=('', 9))
        style.map('TCheckbutton', background=[('active', self.frame_bg)])
        style.configure('TCombobox', fieldbackground=self.entry_bg, foreground=self.entry_fg, 
                       borderwidth=2, bordercolor=self.border_color, arrowcolor=self.accent_color)
        style.map('TCombobox', 
                 fieldbackground=[('readonly', self.entry_bg)],
                 bordercolor=[('focus', self.accent_color)])
        style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', background=self.tab_bg, foreground=self.fg_color, 
                       padding=[15, 10], borderwidth=2, bordercolor=self.border_color,
                       font=('', 9, 'bold'))
        style.map('TNotebook.Tab', 
                 background=[('selected', self.tab_active), ('active', self.button_hover)],
                 bordercolor=[('selected', self.accent_color), ('active', self.border_color)],
                 expand=[('selected', [1, 1, 1, 0])])
        style.configure('TScrollbar', background=self.button_bg, troughcolor=self.bg_color, 
                       borderwidth=1, bordercolor=self.border_color, arrowcolor=self.accent_color, 
                       darkcolor=self.button_bg, lightcolor=self.button_bg)
        style.map('TScrollbar', background=[('active', self.accent_color)])
        
    def create_widgets(self):
        """Cria todos os widgets da interface"""
        
        # Notebook principal (abas)
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Aba 1: Controle Principal
        control_frame = ttk.Frame(notebook, padding="10")
        notebook.add(control_frame, text="🎮 Controle Principal")
        self.create_control_tab(control_frame)
        
        # Aba 2: Configurações
        config_frame = ttk.Frame(notebook, padding="10")
        notebook.add(config_frame, text="⚙️ Configurações")
        self.create_config_tab(config_frame)
        
        # Aba 3: Estatísticas
        stats_frame = ttk.Frame(notebook, padding="10")
        notebook.add(stats_frame, text="📊 Estatísticas")
        self.create_stats_tab(stats_frame)
        
        # Aba 4: Ganhar Coins
        coins_frame = ttk.Frame(notebook, padding="10")
        notebook.add(coins_frame, text="💰 Ganhar Coins")
        self.create_coins_tab(coins_frame)
        
        # Aba 5: Logs
        logs_frame = ttk.Frame(notebook, padding="10")
        notebook.add(logs_frame, text="📝 Logs")
        self.create_logs_tab(logs_frame)
    
    def create_control_tab(self, parent):
        """Cria aba de controle principal"""
        
        # ========== LOGIN ==========
        login_frame = ttk.LabelFrame(parent, text="🔐 Login - Conta Principal", padding="10")
        login_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(login_frame, text="Email:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(login_frame, textvariable=self.email_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(login_frame, text="Senha:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(login_frame, textvariable=self.password_var, width=50, show="*").grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Checkbutton(login_frame, text="Lembrar credenciais", 
                       variable=self.remember_var).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # ========== CONTA SECUNDÁRIA (Para receber coins) ==========
        secondary_frame = ttk.LabelFrame(parent, text="💎 Conta Secundária (Para Receber Coins)", padding="10")
        secondary_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(secondary_frame, text="Email Conta Secundária:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(secondary_frame, textvariable=self.secondary_email_var, width=50).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(secondary_frame, text="ℹ️ Esta conta receberá as coins transferidas", 
                 foreground=self.accent_color).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # ========== MÓDULOS ATIVOS ==========
        modules_frame = ttk.LabelFrame(parent, text="🎯 Módulos Ativos (Pode ativar todos ao mesmo tempo)", padding="10")
        modules_frame.pack(fill=tk.X, pady=5)
        
        # Trading
        trading_check = ttk.Checkbutton(modules_frame, text="💰 Trading Automático", 
                                       variable=self.trading_enabled)
        trading_check.grid(row=0, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(modules_frame, text="Compra/vende jogadores automaticamente", 
                 foreground=self.accent_color, font=("", 8)).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # Squad Battles
        sb_check = ttk.Checkbutton(modules_frame, text="⚽ Squad Battles", 
                                  variable=self.squad_battles_enabled)
        sb_check.grid(row=1, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(modules_frame, text="Joga partidas automaticamente", 
                 foreground=self.accent_color, font=("", 8)).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # Objetivos
        obj_check = ttk.Checkbutton(modules_frame, text="🎯 Objetivos Diários", 
                                    variable=self.objectives_enabled)
        obj_check.grid(row=2, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(modules_frame, text="Completa objetivos e reivindica recompensas", 
                 foreground=self.accent_color, font=("", 8)).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # Transferência de Coins
        transfer_check = ttk.Checkbutton(modules_frame, text="💸 Transferência de Coins", 
                                         variable=self.coin_transfer_enabled)
        transfer_check.grid(row=3, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(modules_frame, text="Transfere coins para conta secundária", 
                 foreground=self.accent_color, font=("", 8)).grid(row=3, column=1, sticky=tk.W, padx=5)
        
        # Comfort Trade
        comfort_check = ttk.Checkbutton(modules_frame, text="⚠️ Comfort Trade", 
                                       variable=self.comfort_trade_enabled)
        comfort_check.grid(row=4, column=0, sticky=tk.W, padx=10, pady=5)
        ttk.Label(modules_frame, text="⚠️ RISCOS: Banimento, Reset de Coins, Roubo de Credenciais", 
                 foreground=self.error_color, font=("", 8, "bold")).grid(row=4, column=1, sticky=tk.W, padx=5)

        # ========== RISCO / PERFIL ========== 
        risk_frame = ttk.LabelFrame(parent, text="🛡️ Risco e Perfil", padding="10")
        risk_frame.pack(fill=tk.X, pady=5)

        ttk.Label(risk_frame, text="Perfil de risco:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        risk_combo = ttk.Combobox(risk_frame, textvariable=self.risk_mode_var,
                                  values=["safe", "normal", "aggressive"], width=15, state="readonly")
        risk_combo.grid(row=0, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(risk_frame, text="safe = mais seguro (recomendado)", foreground=self.accent_color, font=("", 8)).grid(row=0, column=2, sticky=tk.W, padx=5)
        risk_combo.bind("<<ComboboxSelected>>", lambda e: self.update_risk_preview())

        self.risk_label = ttk.Label(risk_frame, textvariable=self.risk_info_var, foreground=self.success_color, 
                                   font=('', 9, 'bold'))
        self.risk_label.grid(row=1, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        # ========== CONTROLES ==========
        control_buttons_frame = ttk.Frame(parent)
        control_buttons_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(control_buttons_frame, text="▶ Iniciar Bot", 
                                    command=self.start_bot, width=20)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = ttk.Button(control_buttons_frame, text="⏸ Pausar", 
                                   command=self.pause_bot, width=20, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_buttons_frame, text="⏹ Parar", 
                                  command=self.stop_bot, width=20, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        # ========== STATUS ==========
        status_frame = ttk.LabelFrame(parent, text="📊 Status em Tempo Real", padding="10")
        status_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # Grid de status
        self.status_label = ttk.Label(status_frame, text="Status: Parado", 
                                      font=("", 12, "bold"), foreground=self.error_color)
        self.status_label.grid(row=0, column=0, columnspan=2, pady=5)
        
        # Estatísticas rápidas
        stats_grid = ttk.Frame(status_frame)
        stats_grid.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=5)
        
        ttk.Label(stats_grid, text="Partidas Jogadas:").grid(row=0, column=0, sticky=tk.W, padx=5)
        self.matches_label = ttk.Label(stats_grid, text="0", font=("", 10, "bold"))
        self.matches_label.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="Trades Realizados:").grid(row=0, column=2, sticky=tk.W, padx=5)
        self.trades_label = ttk.Label(stats_grid, text="0", font=("", 10, "bold"))
        self.trades_label.grid(row=0, column=3, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="Objetivos Completos:").grid(row=1, column=0, sticky=tk.W, padx=5)
        self.objectives_label = ttk.Label(stats_grid, text="0", font=("", 10, "bold"))
        self.objectives_label.grid(row=1, column=1, sticky=tk.W, padx=5)
        
        ttk.Label(stats_grid, text="Coins Ganhas:").grid(row=1, column=2, sticky=tk.W, padx=5)
        self.coins_label = ttk.Label(stats_grid, text="0", font=("", 10, "bold"), foreground=self.success_color)
        self.coins_label.grid(row=1, column=3, sticky=tk.W, padx=5)
    
    def create_config_tab(self, parent):
        """Cria aba de configurações"""
        
        # Scrollable frame
        canvas = tk.Canvas(parent, bg=self.frame_bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # ========== TRADING ==========
        trading_config = ttk.LabelFrame(scrollable_frame, text="💰 Configurações de Trading", padding="10")
        trading_config.pack(fill=tk.X, pady=5)
        
        ttk.Label(trading_config, text="Lucro Mínimo (coins):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(trading_config, textvariable=self.min_profit_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(trading_config, text="Preço Máximo (coins):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(trading_config, textvariable=self.max_price_var, width=20).grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(trading_config, text="Usar Futbin:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.use_futbin_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(trading_config, variable=self.use_futbin_var).grid(row=2, column=1, sticky=tk.W, padx=5)
        
        # ========== SQUAD BATTLES ==========
        sb_config = ttk.LabelFrame(scrollable_frame, text="⚽ Configurações de Squad Battles", padding="10")
        sb_config.pack(fill=tk.X, pady=5)
        
        ttk.Label(sb_config, text="Dificuldade:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        difficulty_combo = ttk.Combobox(sb_config, textvariable=self.difficulty_var, 
                                        values=["Beginner", "Amateur", "Semi-Pro", "Professional", 
                                               "World Class", "Legendary", "Ultimate"], width=17)
        difficulty_combo.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(sb_config, text="Garantir Vitória:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.guarantee_win_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sb_config, variable=self.guarantee_win_var).grid(row=1, column=1, sticky=tk.W, padx=5)
        
        # ========== OBJETIVOS ==========
        obj_config = ttk.LabelFrame(scrollable_frame, text="🎯 Configurações de Objetivos", padding="10")
        obj_config.pack(fill=tk.X, pady=5)
        
        ttk.Label(obj_config, text="Reivindicar Recompensas Automaticamente:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Checkbutton(obj_config, variable=self.auto_claim_rewards).grid(row=0, column=1, sticky=tk.W, padx=5)
        
        # ========== TRANSFERÊNCIA ==========
        transfer_config = ttk.LabelFrame(scrollable_frame, text="💸 Configurações de Transferência", padding="10")
        transfer_config.pack(fill=tk.X, pady=5)
        
        ttk.Label(transfer_config, text="Máximo por Dia (coins):").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_transfer_var = tk.StringVar(value="100000")
        ttk.Entry(transfer_config, textvariable=self.max_transfer_var, width=20).grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(transfer_config, text="Máximo por Transação (coins):").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.max_transaction_var = tk.StringVar(value="50000")
        ttk.Entry(transfer_config, textvariable=self.max_transaction_var, width=20).grid(row=1, column=1, padx=5, pady=5)

        # ========== COMFORT TRADE ==========
        comfort_config = ttk.LabelFrame(scrollable_frame, text="⚠️ Comfort Trade - Transferência de Coins (RISCOS ALTOS!)", padding="10")
        comfort_config.pack(fill=tk.X, pady=5)
        
        # Aviso de segurança
        warning_label = ttk.Label(comfort_config, 
                                 text="⚠️ ATENÇÃO: Este método envolve RISCOS SIGNIFICATIVOS de banimento, reset de coins e roubo de credenciais!",
                                 foreground=self.error_color, font=("", 9, "bold"), wraplength=600)
        warning_label.grid(row=0, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(comfort_config, text="Email do Cliente:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(comfort_config, textvariable=self.comfort_client_email_var, width=30, show="").grid(row=1, column=1, padx=5, pady=5)
        
        ttk.Label(comfort_config, text="Senha do Cliente:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(comfort_config, textvariable=self.comfort_client_password_var, width=30, show="*").grid(row=2, column=1, padx=5, pady=5)
        
        ttk.Label(comfort_config, text="Coins a Transferir:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        ttk.Entry(comfort_config, textvariable=self.comfort_target_coins_var, width=20).grid(row=3, column=1, padx=5, pady=5)
        
        ttk.Label(comfort_config, text="Método:").grid(row=4, column=0, sticky=tk.W, padx=5, pady=5)
        comfort_method_combo = ttk.Combobox(comfort_config, textvariable=self.comfort_method_var,
                                           values=["market", "farming"], width=17, state="readonly")
        comfort_method_combo.grid(row=4, column=1, padx=5, pady=5, sticky=tk.W)
        ttk.Label(comfort_config, text="market = compra jogadores; farming = joga partidas", 
                 foreground=self.accent_color, font=("", 8)).grid(row=4, column=2, sticky=tk.W, padx=5)

        # Botão salvar
        ttk.Button(scrollable_frame, text="💾 Salvar Configurações", 
                  command=self.save_config).pack(pady=10)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_stats_tab(self, parent):
        """Cria aba de estatísticas detalhadas"""
        
        # Notebook para sub-abas
        stats_notebook = ttk.Notebook(parent)
        stats_notebook.pack(fill=tk.BOTH, expand=True)
        
        # Trading Stats
        trading_stats = ttk.Frame(stats_notebook)
        stats_notebook.add(trading_stats, text="💰 Trading")
        self.create_trading_stats(trading_stats)
        
        # Squad Battles Stats
        sb_stats = ttk.Frame(stats_notebook)
        stats_notebook.add(sb_stats, text="⚽ Squad Battles")
        self.create_sb_stats(sb_stats)
        
        # Objetivos Stats
        obj_stats = ttk.Frame(stats_notebook)
        stats_notebook.add(obj_stats, text="🎯 Objetivos")
        self.create_obj_stats(obj_stats)
        
        # Coins Stats
        coins_stats = ttk.Frame(stats_notebook)
        stats_notebook.add(coins_stats, text="💎 Coins")
        self.create_coins_stats(coins_stats)
    
    def create_trading_stats(self, parent):
        """Estatísticas de trading"""
        text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, height=20,
            bg=self.entry_bg, fg=self.fg_color,
            insertbackground=self.fg_color,
            selectbackground=self.select_bg,
            selectforeground=self.select_fg
        )
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text.insert(tk.END, "Estatísticas de Trading aparecerão aqui quando o bot estiver rodando...")
        text.config(state=tk.DISABLED)
        self.trading_stats_text = text
    
    def create_sb_stats(self, parent):
        """Estatísticas de Squad Battles"""
        text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, height=20,
            bg=self.entry_bg, fg=self.fg_color,
            insertbackground=self.fg_color,
            selectbackground=self.select_bg,
            selectforeground=self.select_fg
        )
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text.insert(tk.END, "Estatísticas de Squad Battles aparecerão aqui quando o bot estiver rodando...")
        text.config(state=tk.DISABLED)
        self.sb_stats_text = text
    
    def create_obj_stats(self, parent):
        """Estatísticas de objetivos"""
        text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, height=20,
            bg=self.entry_bg, fg=self.fg_color,
            insertbackground=self.fg_color,
            selectbackground=self.select_bg,
            selectforeground=self.select_fg
        )
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text.insert(tk.END, "Estatísticas de Objetivos aparecerão aqui quando o bot estiver rodando...")
        text.config(state=tk.DISABLED)
        self.obj_stats_text = text
    
    def create_coins_stats(self, parent):
        """Estatísticas de coins"""
        text = scrolledtext.ScrolledText(
            parent, wrap=tk.WORD, height=20,
            bg=self.entry_bg, fg=self.fg_color,
            insertbackground=self.fg_color,
            selectbackground=self.select_bg,
            selectforeground=self.select_fg
        )
        text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        text.insert(tk.END, "Estatísticas de Coins aparecerão aqui quando o bot estiver rodando...")
        text.config(state=tk.DISABLED)
        self.coins_stats_text = text
    
    def create_coins_tab(self, parent):
        """Cria aba de ganhar coins"""
        
        title = ttk.Label(parent, text="💰 Formas de Ganhar Coins Diariamente", 
                         font=("", 16, "bold"))
        title.pack(pady=10)
        
        # Frame scrollable
        canvas = tk.Canvas(parent, bg=self.frame_bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable = ttk.Frame(canvas)
        
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        methods = [
            ("💰 Trading Automático", "Compra jogadores baratos e vende mais caro usando dados do Futbin", "trading"),
            ("⚽ Squad Battles", "Joga partidas e ganha coins por vitórias", "squad_battles"),
            ("🎯 Objetivos Diários", "Completa objetivos e reivindica recompensas em coins", "objectives"),
            ("🏆 Objetivos Semanais", "Completa objetivos semanais para recompensas maiores", "weekly_objectives"),
            ("📦 SBC (Squad Building Challenges)", "Completa SBCs para ganhar packs e coins", "sbc"),
            ("🎮 Rivals", "Joga Division Rivals para recompensas semanais", "rivals"),
            ("🏅 Champions", "Participa do Weekend League", "champions"),
            ("💸 Transferência de Coins", "Transfere coins da conta principal para secundária", "transfer"),
            ("📊 Análise de Mercado", "Monitora mercado para oportunidades de lucro", "market_analysis"),
        ]
        
        for i, (title_text, desc, method) in enumerate(methods):
            frame = ttk.LabelFrame(scrollable, text=title_text, padding="10")
            frame.pack(fill=tk.X, pady=5, padx=10)
            
            ttk.Label(frame, text=desc, wraplength=800).pack(anchor=tk.W, padx=5, pady=2)
            
            status_label = ttk.Label(frame, text="⏸ Não iniciado", foreground=self.accent_color)
            status_label.pack(anchor=tk.W, padx=5)
            
            # Armazena referência
            setattr(self, f"{method}_status", status_label)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_logs_tab(self, parent):
        """Cria aba de logs"""
        self.log_text = scrolledtext.ScrolledText(
            parent, 
            wrap=tk.WORD, 
            height=30,
            bg=self.entry_bg,
            fg=self.fg_color,
            insertbackground=self.fg_color,
            selectbackground=self.select_bg,
            selectforeground=self.select_fg
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configura cores (ajustadas para dark theme)
        self.log_text.tag_config("error", foreground=self.error_color)
        self.log_text.tag_config("warning", foreground=self.warning_color)
        self.log_text.tag_config("info", foreground=self.accent_color)
        self.log_text.tag_config("success", foreground=self.success_color)
        
        # Botão limpar
        ttk.Button(parent, text="🗑️ Limpar Logs", command=self.clear_logs).pack(pady=5)
    
    def load_config(self):
        """Carrega configurações do arquivo"""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Login
            if "login" in config:
                self.email_var.set(config["login"].get("email", ""))
                self.password_var.set(config["login"].get("password", ""))
            
            # Módulos
            if "trading" in config:
                self.trading_enabled.set(config["trading"].get("enabled", True))
                self.min_profit_var.set(str(config["trading"].get("min_profit", 500)))
                self.max_price_var.set(str(config["trading"].get("max_price", 10000)))
            
            if "squad_battles" in config:
                self.squad_battles_enabled.set(config["squad_battles"].get("enabled", True))
                self.difficulty_var.set(config["squad_battles"].get("difficulty", "World Class"))
            
            if "objectives" in config:
                self.objectives_enabled.set(config["objectives"].get("enabled", True))
            
            if "coin_transfer" in config:
                self.coin_transfer_enabled.set(config["coin_transfer"].get("enabled", False))
                self.secondary_email_var.set(config["coin_transfer"].get("secondary_account", ""))
            
            if "comfort_trade" in config:
                self.comfort_trade_enabled.set(config["comfort_trade"].get("enabled", False))
                comfort_client = config["comfort_trade"].get("client_account", {})
                self.comfort_client_email_var.set(comfort_client.get("email", ""))
                self.comfort_client_password_var.set(comfort_client.get("password", ""))
                self.comfort_target_coins_var.set(str(config["comfort_trade"].get("target_coins", 0)))
                self.comfort_method_var.set(config["comfort_trade"].get("transfer_method", "market"))
            
            if "risk" in config:
                self.risk_mode_var.set(config["risk"].get("mode", "safe"))
        except:
            pass
    
    def save_config(self):
        """Salva configurações"""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            
            # Atualiza configurações
            config["trading"]["enabled"] = self.trading_enabled.get()
            config["trading"]["min_profit"] = int(self.min_profit_var.get())
            config["trading"]["max_price"] = int(self.max_price_var.get())
            config["trading"]["use_futbin"] = self.use_futbin_var.get()
            
            config["squad_battles"]["enabled"] = self.squad_battles_enabled.get()
            config["squad_battles"]["difficulty"] = self.difficulty_var.get()
            config["squad_battles"]["guarantee_win"] = self.guarantee_win_var.get()
            
            config["objectives"]["enabled"] = self.objectives_enabled.get()
            
            config["coin_transfer"]["enabled"] = self.coin_transfer_enabled.get()
            config["coin_transfer"]["secondary_account"] = self.secondary_email_var.get()
            config["coin_transfer"]["max_transfer_per_day"] = int(self.max_transfer_var.get())
            config["coin_transfer"]["max_transfer_per_transaction"] = int(self.max_transaction_var.get())

            # Comfort Trade
            config.setdefault("comfort_trade", {})
            config["comfort_trade"]["enabled"] = self.comfort_trade_enabled.get()
            config["comfort_trade"]["target_coins"] = int(self.comfort_target_coins_var.get() or "0")
            config["comfort_trade"]["transfer_method"] = self.comfort_method_var.get()
            config["comfort_trade"].setdefault("client_account", {})
            config["comfort_trade"]["client_account"]["email"] = self.comfort_client_email_var.get()
            config["comfort_trade"]["client_account"]["password"] = self.comfort_client_password_var.get()

            # Risco
            config.setdefault("risk", {})
            config["risk"]["mode"] = self.risk_mode_var.get()
            
            config["login"]["email"] = self.email_var.get()
            config["login"]["password"] = self.password_var.get()
            
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            messagebox.showinfo("Sucesso", "Configurações salvas com sucesso!")
            self.update_risk_preview()
        except Exception as e:
            messagebox.showerror("Erro", f"Erro ao salvar: {e}")
    
    def log_message(self, message, level="INFO"):
        """Adiciona mensagem aos logs"""
        self.log_queue.put((message, level))
    
    def update_logs(self):
        """Atualiza área de logs"""
        try:
            while True:
                message, level = self.log_queue.get_nowait()
                
                self.log_text.config(state=tk.NORMAL)
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                if level == "ERROR":
                    self.log_text.insert(tk.END, f"[{timestamp}] [ERRO] {message}\n", "error")
                elif level == "WARNING":
                    self.log_text.insert(tk.END, f"[{timestamp}] [AVISO] {message}\n", "warning")
                elif level == "SUCCESS":
                    self.log_text.insert(tk.END, f"[{timestamp}] [SUCESSO] {message}\n", "success")
                else:
                    self.log_text.insert(tk.END, f"[{timestamp}] [INFO] {message}\n", "info")
                
                self.log_text.see(tk.END)
                self.log_text.config(state=tk.DISABLED)
        except queue.Empty:
            pass
        
        self.root.after(100, self.update_logs)
    
    def update_stats(self):
        """Atualiza estatísticas"""
        if self.bot:
            try:
                # Trading
                if hasattr(self.bot, 'trading_bot'):
                    stats = self.bot.trading_bot.get_stats()
                    self.trades_label.config(text=f"{stats.get('bought', 0) + stats.get('sold', 0)}")
                
                # Squad Battles
                if hasattr(self.bot, 'squad_battles_bot'):
                    stats = self.bot.squad_battles_bot.get_stats()
                    self.matches_label.config(text=f"{stats.get('matches_played', 0)}")
                
                # Objetivos
                if hasattr(self.bot, 'objectives_bot'):
                    stats = self.bot.objectives_bot.get_stats()
                    self.objectives_label.config(text=f"{stats.get('objectives_completed', 0)}")
                
                # Status
                if self.is_running:
                    if self.is_paused:
                        self.status_label.config(text="Status: Pausado", foreground=self.warning_color)
                    else:
                        self.status_label.config(text="Status: Rodando", foreground=self.success_color)
                else:
                    self.status_label.config(text="Status: Parado", foreground=self.error_color)
            except:
                pass
        
        self.root.after(1000, self.update_stats)
    
    def clear_logs(self):
        """Limpa logs"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state=tk.DISABLED)

    def update_risk_preview(self):
        """Atualiza visualização de risco baseada no config + perfil selecionado"""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                cfg = json.load(f)
            cfg.setdefault("risk", {})
            cfg["risk"]["mode"] = self.risk_mode_var.get()
            # Aplica perfil selecionado para prévia (melhor refletir mitigação)
            profile = RiskScanner.DEFAULT_PROFILES.get(cfg["risk"]["mode"], RiskScanner.DEFAULT_PROFILES["safe"])
            anti = cfg.setdefault("anti_detection", {})
            safety = cfg.setdefault("safety", {})
            coin = cfg.setdefault("coin_transfer", {})
            anti["max_daily_trades"] = min(anti.get("max_daily_trades", 50), profile.get("max_daily_trades", 50))
            anti["max_daily_matches"] = min(anti.get("max_daily_matches", 20), profile.get("max_daily_matches", 20))
            safety["min_delay"] = max(safety.get("min_delay", 0.5), profile.get("min_delay", 0.5))
            safety["max_delay"] = max(safety.get("max_delay", 2.0), profile.get("max_delay", 2.0))
            safety["random_delays"] = True
            coin["enabled"] = coin.get("enabled", False) and profile.get("coin_transfer_enabled", False)

            report = RiskScanner.assess(cfg)
            risk = report.get("risk", "unknown")
            reasons = ", ".join(report.get("reasons", [])) or "sem alertas"
            self.risk_info_var.set(f"Risco: {risk} | Motivos: {reasons}")
            color = self.success_color if risk == "low" else self.warning_color if risk == "medium" else self.error_color
            self.risk_label.configure(foreground=color)
        except Exception:
            self.risk_info_var.set("Risco: desconhecido")
            self.risk_label.configure(foreground=self.accent_color)
    
    def start_bot(self):
        """Inicia o bot"""
        if not self.email_var.get():
            messagebox.showerror("Erro", "Digite o email da conta principal")
            return
        
        if self.is_running:
            messagebox.showwarning("Aviso", "Bot já está rodando!")
            return
        
        # Salva configurações antes de iniciar
        self.save_config()
        
        # Verifica se pelo menos um módulo está ativo
        if not (self.trading_enabled.get() or self.squad_battles_enabled.get() or 
                self.objectives_enabled.get() or self.coin_transfer_enabled.get() or 
                self.comfort_trade_enabled.get()):
            messagebox.showwarning("Aviso", "Ative pelo menos um módulo!")
            return
        
        # Aviso especial para Comfort Trade
        if self.comfort_trade_enabled.get():
            response = messagebox.askyesno(
                "⚠️ AVISO DE SEGURANÇA - COMFORT TRADE",
                "⚠️ ATENÇÃO: Comfort Trade envolve RISCOS SIGNIFICATIVOS:\n\n"
                "• Banimento do Mercado de Transferências\n"
                "• Reset de Coins\n"
                "• Banimento da Conta\n"
                "• Roubo de Credenciais\n\n"
                "Deseja continuar mesmo assim?",
                icon="warning"
            )
            if not response:
                return
        
        self.is_running = True
        self.is_paused = False
        
        self.bot_thread = threading.Thread(target=self.run_bot, daemon=True)
        self.bot_thread.start()
        
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        
        self.log_message("Bot iniciado!", "SUCCESS")
        self.log_message(f"Módulos ativos: Trading={self.trading_enabled.get()}, "
                        f"SB={self.squad_battles_enabled.get()}, "
                        f"Objetivos={self.objectives_enabled.get()}, "
                        f"Transfer={self.coin_transfer_enabled.get()}, "
                        f"Comfort Trade={self.comfort_trade_enabled.get()}", "INFO")
    
    def run_bot(self):
        """Executa bot em thread separada"""
        try:
            self.bot = EAFCBot()

            # Atualiza info de risco
            try:
                if getattr(self.bot, "risk_report", None):
                    risk = self.bot.risk_report.get("risk", "desconhecido")
                    reasons = ", ".join(self.bot.risk_report.get("reasons", [])) or "sem alertas"
                    self.risk_info_var.set(f"Risco: {risk} | Motivos: {reasons}")
                    self.risk_label.configure(foreground=self.success_color if risk == "low" else self.warning_color if risk == "medium" else self.error_color)
            except Exception:
                pass
            
            # Redireciona logs
            original_info = self.bot.logger.info
            original_warning = self.bot.logger.warning
            original_error = self.bot.logger.error
            
            def log_info(msg, *args, **kwargs):
                self.log_message(str(msg), "INFO")
                original_info(msg, *args, **kwargs)
            
            def log_warning(msg, *args, **kwargs):
                self.log_message(str(msg), "WARNING")
                original_warning(msg, *args, **kwargs)
            
            def log_error(msg, *args, **kwargs):
                self.log_message(str(msg), "ERROR")
                original_error(msg, *args, **kwargs)
            
            self.bot.logger.info = log_info
            self.bot.logger.warning = log_warning
            self.bot.logger.error = log_error
            
            self.bot.run()
        except Exception as e:
            self.log_message(f"Erro: {e}", "ERROR")
            self.is_running = False
    
    def pause_bot(self):
        """Pausa/retoma bot"""
        if self.bot:
            self.bot.toggle_pause()
            self.is_paused = self.bot.paused
            
            if self.is_paused:
                self.pause_btn.config(text="▶ Retomar")
                self.log_message("Bot pausado", "WARNING")
            else:
                self.pause_btn.config(text="⏸ Pausar")
                self.log_message("Bot retomado", "SUCCESS")
    
    def stop_bot(self):
        """Para bot"""
        if self.bot:
            self.bot.stop()
            self.is_running = False
            self.is_paused = False
            
            self.start_btn.config(state=tk.NORMAL)
            self.pause_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.DISABLED)
            
            self.log_message("Bot parado", "WARNING")
    
    def on_closing(self):
        """Ao fechar"""
        if self.is_running:
            if messagebox.askokcancel("Sair", "Bot está rodando. Deseja parar e sair?"):
                self.stop_bot()
                self.root.destroy()
        else:
            self.root.destroy()

def main():
    """Função principal"""
    root = tk.Tk()
    # Traz para frente na abertura para evitar janela escondida
    try:
        root.attributes("-topmost", True)
        root.after(1200, lambda: root.attributes("-topmost", False))
    except Exception:
        pass
    app = BotGUICompleta(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()

