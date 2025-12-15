"""
Script para executar a interface gráfica completa do bot
"""

import sys
import os

# Adiciona diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Usa interface completa
if __name__ == "__main__":
    try:
        from gui.main_window_completa import BotGUICompleta
        import tkinter as tk
        
        print("🚀 Iniciando interface gráfica...")
        print("💡 Aguarde a janela abrir...")
        
        root = tk.Tk()
        root.title("EA FC 26 Bot - Interface Completa")
        
        # Força janela na frente
        try:
            root.attributes("-topmost", True)
            root.lift()
            root.focus_force()
        except:
            pass
        
        # Cria aplicação
        app = BotGUICompleta(root)
        
        # Remove topmost após 1 segundo
        root.after(1000, lambda: root.attributes("-topmost", False))
        
        # Protocolo de fechamento
        root.protocol("WM_DELETE_WINDOW", app.on_closing)
        
        print("✅ Interface gráfica iniciada!")
        print("💡 Se a janela não aparecer, verifique se está minimizada na barra de tarefas")
        
        # Inicia loop
        root.mainloop()
        
    except Exception as e:
        print(f"❌ Erro ao iniciar interface gráfica: {e}")
        import traceback
        traceback.print_exc()
        input("\nPressione Enter para sair...")

