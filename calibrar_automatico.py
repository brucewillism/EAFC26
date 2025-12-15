"""
Calibração Automática - Encontra coordenadas automaticamente usando OCR
"""

import json
import time
import pyautogui
from bot.screen_capture import ScreenCapture
from bot.real_detection import RealDetection
from bot.controller import Controller
from utils.logger import setup_logger

def calibrar_automatico():
    """Calibra coordenadas automaticamente usando detecção de texto"""
    
    print("="*60)
    print("CALIBRAÇÃO AUTOMÁTICA - EA FC 26 BOT")
    print("="*60)
    print("\nEste script tenta encontrar coordenadas automaticamente")
    print("usando detecção de texto (OCR).\n")
    
    # Configuração básica
    config = {
        "screen_resolution": {"width": 1920, "height": 1080},
        "logging": {"enabled": True, "level": "INFO"}
    }
    
    logger = setup_logger(config.get("logging", {}))
    screen_capture = ScreenCapture(config, logger)
    controller = Controller(config, logger)
    real_detection = RealDetection(screen_capture, logger, controller)
    
    coordenadas = {}
    
    # Elementos para calibrar (expandido)
    elementos = {
        "Ultimate Team": "ultimate_team_menu",
        "Transfer Market": "transfer_market",
        "Squad Battles": "squad_battles",
        "Objectives": "objectives",
        "My Club": "my_club",
        "Transfer List": "transfer_list",
        "Buy Now": "buy_now",
        "Confirm": "confirm",
        "Search": "search",
        "List for Transfer": "list_for_transfer",
        "Squad": "squad_menu",
        "Squad Builder": "squad_builder",
        "Club": "club_search",
        "Apply": "apply_filters",
        "Clear": "clear_filters",
        "Select": "confirm_substitution"
    }
    
    print("\n📋 INSTRUÇÕES:")
    print("1. Abra o jogo EA FC 26")
    print("2. Navegue até a tela onde o elemento aparece")
    print("3. Pressione ENTER quando estiver pronto para cada elemento\n")
    
    input("Pressione ENTER para começar...")
    
    for texto, chave in elementos.items():
        print(f"\n{'='*60}")
        print(f"Calibrando: {texto}")
        print(f"{'='*60}")
        print(f"1. Navegue até a tela onde '{texto}' aparece")
        print("2. Certifique-se de que o elemento está visível")
        print("3. Pressione ENTER quando estiver pronto")
        
        input()
        
        print(f"🔍 Buscando '{texto}' na tela...")
        
        # Tenta encontrar usando OCR
        from bot.navigation import Navigation
        nav = Navigation(controller, screen_capture, real_detection, logger)
        
        # Tenta múltiplos métodos de busca
        coords = None
        
        # Método 1: Busca por texto (OCR)
        coords = nav.find_button_by_text(texto, timeout=10)
        
        # Método 2: Se não encontrou, tenta template matching (se existir)
        if not coords:
            template_path = f"templates/{texto.lower().replace(' ', '_')}.png"
            import os
            if os.path.exists(template_path):
                coords = nav.find_button_by_template(template_path)
        
        if coords:
            coordenadas[chave] = coords
            print(f"✅ Encontrado em: {coords}")
        else:
            print(f"❌ Não encontrado automaticamente")
            print("Tentando método manual...")
            
            # Método manual de fallback
            print(f"\nMova o mouse sobre '{texto}' e pressione ESPAÇO")
            print("Ou pressione ENTER para pular este elemento")
            
            import keyboard
            import sys
            
            def on_space():
                x, y = pyautogui.position()
                coordenadas[chave] = (x, y)
                print(f"✅ Coordenada capturada: ({x}, {y})")
                keyboard.unhook_all()
                sys.exit(0)
            
            keyboard.on_press_key('space', lambda _: on_space())
            
            try:
                input()  # Aguarda ENTER para pular
                keyboard.unhook_all()
                print("⏭️ Elemento pulado")
            except:
                pass
    
    # Salva coordenadas
    print("\n" + "="*60)
    print("Coordenadas encontradas:")
    print("="*60)
    for chave, coord in coordenadas.items():
        if coord:
            print(f"{chave}: {coord}")
        else:
            print(f"{chave}: (não encontrado)")
    
    # Salva em arquivo
    salvar = input("\n💾 Deseja salvar em arquivo? (s/n): ")
    if salvar.lower() == 's':
        filename = "coordenadas_calibradas.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(coordenadas, f, indent=2, ensure_ascii=False)
        print(f"✅ Coordenadas salvas em {filename}")
        print("\nO bot usará essas coordenadas automaticamente!")
    
    print("\n✅ Calibração concluída!")

if __name__ == "__main__":
    try:
        calibrar_automatico()
    except KeyboardInterrupt:
        print("\n\n❌ Calibração cancelada pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")

