"""
Script para Iniciar Servidor Appium
Encontra Appium e inicia servidor automaticamente
"""

import subprocess
import sys
import os
import shutil

def find_appium():
    """Encontra Appium no sistema"""
    # Locais comuns
    common_paths = [
        os.path.expanduser(r"~\AppData\Roaming\npm\appium.cmd"),
        r"C:\Program Files\nodejs\appium.cmd",
        r"C:\Program Files (x86)\nodejs\appium.cmd",
    ]
    
    # Tenta encontrar no PATH
    appium_path = shutil.which("appium")
    if appium_path:
        return appium_path
    
    # Tenta locais comuns
    for path in common_paths:
        if os.path.exists(path):
            return path
    
    return None

def start_appium_server():
    """Inicia servidor Appium"""
    appium_path = find_appium()
    
    if not appium_path:
        print("❌ Appium não encontrado no PATH!")
        print("\n💡 SOLUÇÕES:")
        print("1. Use Appium Desktop (mais fácil):")
        print("   https://github.com/appium/appium-desktop/releases")
        print("   - Baixe, instale e execute")
        print("   - Clique em 'Start Server'")
        print()
        print("2. Ou adicione Appium ao PATH:")
        print("   - Geralmente: C:\\Users\\SeuUsuario\\AppData\\Roaming\\npm")
        print("   - Adicione ao PATH do Windows")
        return False
    
    print(f"✅ Appium encontrado: {appium_path}")
    print("\n🚀 Iniciando servidor Appium...")
    print("💡 Deixe este terminal aberto enquanto usar o bot")
    print("   Pressione Ctrl+C para parar o servidor\n")
    print("="*70)
    
    try:
        # Inicia servidor
        subprocess.run([appium_path], check=True)
    except KeyboardInterrupt:
        print("\n\n⏹️  Servidor Appium parado")
    except Exception as e:
        print(f"\n❌ Erro: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("="*70)
    print("INICIAR SERVIDOR APPIUM")
    print("="*70)
    print()
    
    start_appium_server()

