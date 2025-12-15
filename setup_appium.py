"""
Script de Configuração do Appium para EA Companion
"""

import subprocess
import sys
import os

def check_node_installed():
    """Verifica se Node.js está instalado"""
    try:
        result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Node.js encontrado: {result.stdout.strip()}")
            return True
        return False
    except FileNotFoundError:
        return False

def check_appium_installed():
    """Verifica se Appium está instalado"""
    try:
        result = subprocess.run(['appium', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Appium encontrado: {result.stdout.strip()}")
            return True
        return False
    except FileNotFoundError:
        return False

def install_appium():
    """Instala Appium globalmente"""
    print("\n📦 Instalando Appium...")
    try:
        subprocess.run(['npm', 'install', '-g', 'appium'], check=True)
        print("✅ Appium instalado com sucesso!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar Appium: {e}")
        return False
    except FileNotFoundError:
        print("❌ npm não encontrado. Instale Node.js primeiro.")
        return False

def install_appium_driver(driver_name="uiautomator2"):
    """Instala driver do Appium (Android)"""
    print(f"\n📦 Instalando driver {driver_name}...")
    try:
        subprocess.run(['appium', 'driver', 'install', driver_name], check=True)
        print(f"✅ Driver {driver_name} instalado!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Erro ao instalar driver: {e}")
        return False

def create_appium_config():
    """Cria arquivo de configuração do Appium"""
    config_content = """{
  "platformName": "Android",
  "platformVersion": "11.0",
  "deviceName": "Android Device",
  "appPackage": "com.ea.gp.fifacompanion",
  "appActivity": ".MainActivity",
  "automationName": "UiAutomator2",
  "noReset": true,
  "fullReset": false,
  "newCommandTimeout": 300
}
"""
    
    try:
        with open("appium_config.json", "w", encoding="utf-8") as f:
            f.write(config_content)
        print("✅ Arquivo appium_config.json criado!")
        return True
    except Exception as e:
        print(f"❌ Erro ao criar config: {e}")
        return False

def main():
    print("="*70)
    print("CONFIGURAÇÃO DO APPIUM PARA EA COMPANION")
    print("="*70)
    print()
    
    # 1. Verifica Node.js
    print("1️⃣ Verificando Node.js...")
    if not check_node_installed():
        print("❌ Node.js não encontrado!")
        print("\n📥 Instale Node.js em: https://nodejs.org/")
        print("   Depois execute este script novamente.")
        return False
    print()
    
    # 2. Verifica Appium
    print("2️⃣ Verificando Appium...")
    if not check_appium_installed():
        print("⚠️  Appium não encontrado. Instalando...")
        if not install_appium():
            return False
    print()
    
    # 3. Instala driver Android
    print("3️⃣ Verificando driver Android...")
    install_appium_driver("uiautomator2")
    print()
    
    # 4. Cria configuração
    print("4️⃣ Criando configuração...")
    create_appium_config()
    print()
    
    # 5. Instruções
    print("="*70)
    print("✅ CONFIGURAÇÃO CONCLUÍDA!")
    print("="*70)
    print("\n📱 PRÓXIMOS PASSOS:")
    print("\n1. Conecte seu dispositivo Android ou inicie emulador")
    print("2. Instale o app EA Companion no dispositivo")
    print("3. Ative 'Depuração USB' no dispositivo")
    print("4. Verifique conexão:")
    print("   adb devices")
    print("\n5. Inicie servidor Appium:")
    print("   appium")
    print("\n6. Em outro terminal, execute o bot:")
    print("   python main.py")
    print("\n" + "="*70)
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Configuração cancelada")
    except Exception as e:
        print(f"\n\n❌ Erro: {e}")
        import traceback
        traceback.print_exc()

