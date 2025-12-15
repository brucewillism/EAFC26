"""
Script para calibrar regiões de detecção
"""

import pyautogui
import time
import json
from PIL import Image
import cv2
import numpy as np

def calibrar_regiao(nome_regiao):
    """Calibra uma região de detecção"""
    print(f"\n{'='*60}")
    print(f"CALIBRAÇÃO: {nome_regiao}")
    print(f"{'='*60}")
    print("1. Abra o EA FC 26")
    print("2. Navegue até a tela onde aparece esta informação")
    print("3. Pressione ENTER quando estiver pronto")
    print("4. Mova o mouse para o CANTO SUPERIOR ESQUERDO da região")
    print("5. Pressione ENTER novamente")
    print("6. Mova o mouse para o CANTO INFERIOR DIREITO da região")
    print("7. Pressione ENTER para finalizar")
    print(f"{'='*60}\n")
    
    input("Pressione ENTER quando estiver na tela correta...")
    
    print("\nMova o mouse para o CANTO SUPERIOR ESQUERDO e pressione ENTER...")
    input()
    x1, y1 = pyautogui.position()
    print(f"Canto superior esquerdo: ({x1}, {y1})")
    
    print("\nMova o mouse para o CANTO INFERIOR DIREITO e pressione ENTER...")
    input()
    x2, y2 = pyautogui.position()
    print(f"Canto inferior direito: ({x2}, {y2})")
    
    # Garante ordem correta
    left = min(x1, x2)
    top = min(y1, y2)
    width = abs(x2 - x1)
    height = abs(y2 - y1)
    
    region = (left, top, width, height)
    
    # Tira screenshot da região
    screenshot = pyautogui.screenshot(region=region)
    filename = f"calibracao_{nome_regiao.lower().replace(' ', '_')}.png"
    screenshot.save(filename)
    print(f"\nScreenshot salvo: {filename}")
    
    return region

def main():
    """Função principal"""
    print("="*60)
    print("CALIBRAÇÃO DE REGIÕES DE DETECÇÃO")
    print("="*60)
    print("\nEste script ajuda a calibrar as regiões onde o bot")
    print("deve procurar informações (placares, times, jogadores).\n")
    
    regioes = {}
    
    # Calibrações
    print("\n[PARTIDAS]")
    regioes["placar"] = calibrar_regiao("Placar da Partida")
    regioes["time_esquerda"] = calibrar_regiao("Nome do Time da Esquerda (Nosso Time)")
    regioes["time_direita"] = calibrar_regiao("Nome do Time da Direita (Adversário)")
    
    print("\n[TRADING]")
    regioes["jogador_market"] = calibrar_regiao("Região de Jogador no Mercado")
    regioes["preco_market"] = calibrar_regiao("Região de Preço no Mercado")
    
    print("\n[TIME]")
    regioes["info_time"] = calibrar_regiao("Informações do Time (My Club)")
    
    # Salva calibrações
    calibracao_file = "calibracao_regioes.json"
    with open(calibracao_file, 'w', encoding='utf-8') as f:
        json.dump(regioes, f, indent=2, ensure_ascii=False)
    
    print(f"\n{'='*60}")
    print("Calibração concluída!")
    print(f"{'='*60}")
    print(f"\nRegiões calibradas salvas em: {calibracao_file}")
    print("\nRegiões calibradas:")
    for nome, regiao in regioes.items():
        print(f"  {nome}: {regiao}")
    
    print("\nUse essas coordenadas no código do bot!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCalibração cancelada.")
    except Exception as e:
        print(f"\nErro: {e}")

