"""
Script auxiliar para calibrar coordenadas do bot
Use este script para encontrar coordenadas de elementos na tela
"""

import pyautogui
import time
import json

def calibrar_coordenada(nome):
    """Solicita ao usuário para posicionar o mouse e retorna as coordenadas"""
    print(f"\n{'='*50}")
    print(f"Calibração: {nome}")
    print(f"{'='*50}")
    print("1. Abra o jogo EA FC 26")
    print("2. Navegue até o elemento que deseja calibrar")
    print("3. Posicione o mouse sobre o elemento")
    print("4. Pressione ENTER para capturar a coordenada")
    print("5. Pressione 's' para pular este elemento")
    print(f"{'='*50}\n")
    
    resposta = input("Pressione ENTER quando estiver pronto (ou 's' para pular): ")
    
    if resposta.lower() == 's':
        return None
    
    x, y = pyautogui.position()
    print(f"✓ Coordenada capturada: ({x}, {y})")
    return (x, y)

def main():
    """Função principal de calibração"""
    print("="*60)
    print("CALIBRAÇÃO DE COORDENADAS - EA FC 26 BOT")
    print("="*60)
    print("\nEste script ajuda você a encontrar as coordenadas")
    print("dos elementos do jogo para o bot funcionar corretamente.\n")
    
    coordenadas = {}
    
    # Calibração de Trading
    print("\n[TRADING]")
    coordenadas['transfer_market'] = calibrar_coordenada("Transfer Market (menu)")
    coordenadas['search_button'] = calibrar_coordenada("Botão Search")
    coordenadas['buy_now'] = calibrar_coordenada("Botão Buy Now")
    coordenadas['confirm_buy'] = calibrar_coordenada("Botão Confirm (comprar)")
    
    # Calibração de Squad Battles
    print("\n[SQUAD BATTLES]")
    coordenadas['squad_battles'] = calibrar_coordenada("Squad Battles (menu)")
    coordenadas['play_match'] = calibrar_coordenada("Botão Play Match")
    coordenadas['difficulty'] = calibrar_coordenada("Seleção de Dificuldade")
    
    # Calibração de Objetivos
    print("\n[OBJETIVOS]")
    coordenadas['objectives'] = calibrar_coordenada("Objectives (menu)")
    coordenadas['claim_reward'] = calibrar_coordenada("Botão Claim Reward")
    
    # Salvar coordenadas
    print("\n" + "="*60)
    print("Coordenadas capturadas:")
    print("="*60)
    for nome, coord in coordenadas.items():
        if coord:
            print(f"{nome}: {coord}")
        else:
            print(f"{nome}: (não capturado)")
    
    # Salvar em arquivo
    salvar = input("\nDeseja salvar em arquivo JSON? (s/n): ")
    if salvar.lower() == 's':
        filename = "coordenadas_calibradas.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(coordenadas, f, indent=2, ensure_ascii=False)
        print(f"✓ Coordenadas salvas em {filename}")
        print("\nVocê pode usar essas coordenadas no código do bot!")
    
    print("\nCalibração concluída!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nCalibração cancelada pelo usuário.")
    except Exception as e:
        print(f"\nErro: {e}")

