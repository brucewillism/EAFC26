"""
Script para Executar Bot Completo
Verifica tudo e executa o bot
"""

import sys
import os
import subprocess
import json

def check_dependencies():
    """Verifica dependências"""
    print("="*70)
    print("VERIFICAÇÃO DE DEPENDÊNCIAS")
    print("="*70)
    print()
    
    all_ok = True
    
    # Python
    print("1️⃣ Python...")
    print(f"   ✅ Python {sys.version.split()[0]}")
    
    # Bibliotecas Python
    print("\n2️⃣ Bibliotecas Python...")
    libs = [
        "pyautogui", "cv2", "numpy", "PIL", "pynput", 
        "keyboard", "pytesseract", "requests"
    ]
    
    for lib in libs:
        try:
            if lib == "cv2":
                import cv2
            elif lib == "PIL":
                from PIL import Image
            else:
                __import__(lib)
            print(f"   ✅ {lib}")
        except ImportError:
            print(f"   ❌ {lib} - Execute: pip install {lib}")
            all_ok = False
    
    # Appium (opcional)
    print("\n3️⃣ Appium-Python-Client (opcional)...")
    try:
        from appium import webdriver
        print("   ✅ Appium-Python-Client instalado")
    except ImportError:
        print("   ⚠️  Appium-Python-Client não instalado (opcional)")
        print("   💡 Para transferência de coins: pip install Appium-Python-Client")
    
    # Tesseract
    print("\n4️⃣ Tesseract OCR...")
    try:
        import pytesseract
        try:
            pytesseract.get_tesseract_version()
            print("   ✅ Tesseract encontrado")
        except:
            try:
                pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
                pytesseract.get_tesseract_version()
                print("   ✅ Tesseract encontrado no caminho padrão")
            except:
                print("   ⚠️  Tesseract não encontrado")
                print("   💡 Instale em: https://github.com/UB-Mannheim/tesseract/wiki")
                all_ok = False
    except ImportError:
        print("   ❌ pytesseract não instalado")
        all_ok = False
    
    # Config
    print("\n5️⃣ Configuração...")
    if os.path.exists("config.json"):
        print("   ✅ config.json encontrado")
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            print("   ✅ Config válido")
        except:
            print("   ❌ Config inválido")
            all_ok = False
    else:
        print("   ❌ config.json não encontrado")
        all_ok = False
    
    print("\n" + "="*70)
    if all_ok:
        print("✅ TODAS AS DEPENDÊNCIAS OK!")
    else:
        print("⚠️  ALGUMAS DEPENDÊNCIAS FALTANDO")
    print("="*70)
    
    return all_ok

def main():
    """Função principal"""
    print("\n" + "="*70)
    print("EA FC 26 BOT - EXECUTOR COMPLETO")
    print("="*70)
    print()
    
    # Verifica dependências
    if not check_dependencies():
        print("\n⚠️  Instale as dependências faltantes antes de continuar")
        print("   Execute: pip install -r requirements.txt")
        return
    
    print("\n" + "="*70)
    print("ESCOLHA O MODO DE EXECUÇÃO")
    print("="*70)
    print()
    print("1. Interface Gráfica (Recomendado)")
    print("2. Linha de Comando")
    print("3. Teste Rápido")
    print()
    
    choice = input("Escolha (1/2/3): ").strip()
    
    if choice == "1":
        print("\n🚀 Iniciando Interface Gráfica...")
        try:
            from gui.main_window_completa import main as gui_main
            gui_main()
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    
    elif choice == "2":
        print("\n🚀 Iniciando Bot em Linha de Comando...")
        try:
            from main import EAFCBot
            bot = EAFCBot()
            bot.run()
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    
    elif choice == "3":
        print("\n🧪 Executando Teste Rápido...")
        try:
            # Teste básico
            from bot.screen_capture import ScreenCapture
            from utils.logger import setup_logger
            
            config = json.load(open("config.json", "r", encoding="utf-8"))
            logger = setup_logger(config.get("logging", {}))
            screen_capture = ScreenCapture(config, logger)
            
            screenshot = screen_capture.capture_screen()
            if screenshot is not None:
                print(f"✅ Captura de tela funcionando! (Tamanho: {screenshot.shape})")
            else:
                print("❌ Erro na captura de tela")
        except Exception as e:
            print(f"❌ Erro: {e}")
            import traceback
            traceback.print_exc()
    
    else:
        print("❌ Opção inválida")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Execução cancelada")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

