"""
Script de Diagnóstico - Verifica por que o bot não está executando ações
"""

import json
import sys
import os
from pathlib import Path

def check_game_running():
    """Verifica se o jogo está rodando"""
    print("="*70)
    print("DIAGNÓSTICO DO BOT - EA FC 26")
    print("="*70)
    print()
    
    print("1️⃣ Verificando se o jogo está aberto...")
    try:
        import pyautogui
        screenshot = pyautogui.screenshot()
        print(f"   ✅ Captura de tela funcionando ({screenshot.size})")
    except Exception as e:
        print(f"   ❌ Erro na captura: {e}")
        return False
    
    print("\n2️⃣ Verificando configuração...")
    if not os.path.exists("config.json"):
        print("   ❌ config.json não encontrado!")
        return False
    
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        print("   ✅ Config carregado")
        
        # Verifica módulos habilitados
        print("\n   📋 Módulos habilitados:")
        trading_enabled = config.get("trading", {}).get("enabled", False)
        sb_enabled = config.get("squad_battles", {}).get("enabled", False)
        obj_enabled = config.get("objectives", {}).get("enabled", False)
        
        print(f"      {'✅' if trading_enabled else '❌'} Trading: {trading_enabled}")
        print(f"      {'✅' if sb_enabled else '❌'} Squad Battles: {sb_enabled}")
        print(f"      {'✅' if obj_enabled else '❌'} Objetivos: {obj_enabled}")
        
        if not (trading_enabled or sb_enabled or obj_enabled):
            print("\n   ⚠️  NENHUM MÓDULO HABILITADO!")
            print("   💡 Habilite pelo menos um módulo no config.json")
            return False
        
    except Exception as e:
        print(f"   ❌ Erro ao ler config: {e}")
        return False
    
    print("\n3️⃣ Verificando coordenadas calibradas...")
    if os.path.exists("coordenadas_calibradas.json"):
        print("   ✅ Coordenadas encontradas")
        try:
            with open("coordenadas_calibradas.json", "r", encoding="utf-8") as f:
                coords = json.load(f)
            print(f"   📍 {len(coords)} coordenadas salvas")
        except:
            print("   ⚠️  Arquivo existe mas está corrompido")
    else:
        print("   ⚠️  Coordenadas NÃO calibradas!")
        print("   💡 Execute: python calibrar_automatico.py")
    
    print("\n4️⃣ Verificando detecção de tela...")
    try:
        from bot.screen_capture import ScreenCapture
        from utils.logger import setup_logger
        
        logger = setup_logger(config.get("logging", {}))
        screen_capture = ScreenCapture(config, logger)
        
        screenshot = screen_capture.capture_screen()
        if screenshot is not None:
            print(f"   ✅ Captura funcionando ({screenshot.shape})")
        else:
            print("   ❌ Erro na captura de tela")
            return False
    except Exception as e:
        print(f"   ❌ Erro: {e}")
        return False
    
    print("\n5️⃣ Testando detecção de texto (OCR)...")
    try:
        from bot.real_detection import RealDetection
        from bot.controller import Controller
        
        controller = Controller(config, logger, None)
        real_detection = RealDetection(screen_capture, logger, controller)
        
        # Tenta detectar texto na tela
        screenshot = screen_capture.capture_screen()
        if screenshot is not None:
            # Testa OCR em uma região central
            import cv2
            h, w = screenshot.shape[:2]
            test_region = (w//4, h//4, w*3//4, h*3//4)
            text = real_detection.read_text_from_region(test_region)
            
            if text:
                print(f"   ✅ OCR funcionando (detectou: '{text[:50]}...')")
            else:
                print("   ⚠️  OCR não detectou texto (pode ser normal se tela estiver vazia)")
        else:
            print("   ❌ Não conseguiu capturar tela")
    except Exception as e:
        print(f"   ⚠️  Erro no teste OCR: {e}")
    
    print("\n6️⃣ Verificando navegação...")
    try:
        from bot.navigation import Navigation
        
        navigation = Navigation(controller, screen_capture, real_detection, logger)
        
        # Tenta encontrar botão comum
        print("   🔍 Tentando encontrar botão 'Ultimate Team'...")
        button = navigation.find_button_by_text("Ultimate Team", timeout=3)
        
        if button:
            print(f"   ✅ Botão encontrado em {button}")
        else:
            print("   ⚠️  Botão não encontrado")
            print("   💡 Possíveis causas:")
            print("      - Jogo não está aberto")
            print("      - Jogo não está na tela principal")
            print("      - Resolução diferente da configurada")
            print("      - Precisa calibrar coordenadas")
    except Exception as e:
        print(f"   ⚠️  Erro no teste de navegação: {e}")
    
    print("\n7️⃣ Verificando logs recentes...")
    if os.path.exists("bot_log.txt"):
        try:
            with open("bot_log.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
                if lines:
                    print("   📄 Últimas 5 linhas do log:")
                    for line in lines[-5:]:
                        print(f"      {line.strip()}")
        except:
            pass
    
    print("\n" + "="*70)
    print("RECOMENDAÇÕES:")
    print("="*70)
    print()
    print("1. ✅ Certifique-se que o jogo EA FC 26 está ABERTO e VISÍVEL")
    print("2. ✅ Deixe o jogo na tela principal do Ultimate Team")
    print("3. ✅ Execute calibração: python calibrar_automatico.py")
    print("4. ✅ Verifique se pelo menos um módulo está habilitado no config.json")
    print("5. ✅ Certifique-se que está usando a CONTA PRINCIPAL (não secundária)")
    print("6. ✅ A conta principal DEVE ter um time criado")
    print()
    print("⚠️  IMPORTANTE:")
    print("   - O bot trabalha na CONTA PRINCIPAL (onde você está logado)")
    print("   - A conta secundária só recebe coins via transferência")
    print("   - Se a conta principal não tem time, o bot não consegue jogar")
    print()
    print("="*70)
    
    return True

if __name__ == "__main__":
    try:
        check_game_running()
    except KeyboardInterrupt:
        print("\n\n❌ Diagnóstico cancelado")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

