"""
Automação do EA Companion via Appium
"""

import time
import random
from appium import webdriver
from appium.options.android import UiAutomator2Options
from appium.webdriver.common.appiumby import AppiumBy

class EACompanionAutomation:
    """Automatiza o app EA Companion usando Appium"""
    
    def __init__(self, logger, device_config=None):
        self.logger = logger
        self.driver = None
        self.device_config = device_config or self.get_default_config()
        
    def get_default_config(self):
        """Retorna configuração padrão do Appium"""
        return {
            "platformName": "Android",
            "platformVersion": "11.0",
            "deviceName": "Android Device",
            "appPackage": "com.ea.gp.fifacompanion",
            "appActivity": ".MainActivity",
            "automationName": "UiAutomator2",
            "noReset": True,
            "fullReset": False,
            "newCommandTimeout": 300,
            "appium_server_url": "http://localhost:4723"
        }
    
    def connect(self):
        """Conecta ao dispositivo e inicia app"""
        try:
            self.logger.info("📱 Conectando ao dispositivo via Appium...")
            
            options = UiAutomator2Options()
            for key, value in self.device_config.items():
                if key != "appium_server_url":
                    options.set_capability(key, value)
            
            server_url = self.device_config.get("appium_server_url", "http://localhost:4723")
            
            self.driver = webdriver.Remote(server_url, options=options)
            
            self.logger.info("✅ Conectado ao dispositivo!")
            
            # Verifica se já está logado
            if self.is_logged_in():
                self.logger.info("✅ App já está logado! Usando sessão existente.")
                return True
            else:
                self.logger.info("⚠️  App não está logado. Será necessário fazer login.")
                return True  # Retorna True mesmo assim, login pode ser feito depois
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao conectar: {e}")
            self.logger.info("💡 Certifique-se de que:")
            self.logger.info("   1. Appium server está rodando (appium)")
            self.logger.info("   2. Dispositivo está conectado (adb devices)")
            self.logger.info("   3. EA Companion está instalado")
            return False
    
    def is_logged_in(self):
        """Verifica se já está logado no app"""
        try:
            # Aguarda app carregar
            time.sleep(2)
            
            # Procura por elementos que indicam que está logado
            # Se encontrar elementos da tela principal (não tela de login), está logado
            
            logged_in_indicators = [
                "//android.widget.TextView[@text='Ultimate Team']",
                "//android.widget.TextView[@text='Transfer Market']",
                "//android.widget.TextView[@text='My Club']",
                "//android.widget.TextView[@text='Squad']",
                "//android.widget.TextView[@content-desc='Ultimate Team']"
            ]
            
            for indicator in logged_in_indicators:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, indicator)
                    if element:
                        self.logger.info(f"✅ Indicador de login encontrado: {indicator}")
                        return True
                except:
                    continue
            
            # Se não encontrou indicadores, verifica se está na tela de login
            login_indicators = [
                "//android.widget.EditText[@content-desc='Email']",
                "//android.widget.EditText[@content-desc='Password']",
                "//android.widget.Button[@text='Login']",
                "//android.widget.TextView[@text='Sign In']"
            ]
            
            for indicator in login_indicators:
                try:
                    element = self.driver.find_element(AppiumBy.XPATH, indicator)
                    if element:
                        self.logger.info("⚠️  Tela de login detectada. Não está logado.")
                        return False
                except:
                    continue
            
            # Se não encontrou nem login nem logado, assume que está logado
            # (pode estar em outra tela do app)
            self.logger.info("⚠️  Não foi possível determinar status de login. Assumindo que está logado.")
            return True
            
        except Exception as e:
            self.logger.debug(f"Erro ao verificar login: {e}")
            # Em caso de erro, assume que não está logado (mais seguro)
            return False
    
    def disconnect(self):
        """Desconecta do dispositivo"""
        try:
            if self.driver:
                self.driver.quit()
                self.logger.info("✅ Desconectado do dispositivo")
        except Exception as e:
            self.logger.debug(f"Erro ao desconectar: {e}")
    
    def login(self, email=None, password=None):
        """Faz login no EA Companion (só se não estiver logado)"""
        try:
            # Verifica se já está logado
            if self.is_logged_in():
                self.logger.info("✅ Já está logado! Não precisa fazer login novamente.")
                return True
            
            if not email or not password:
                self.logger.warning("⚠️  Email/senha não fornecidos e não está logado.")
                self.logger.info("💡 Faça login manualmente no app ou forneça credenciais.")
                return False
            
            self.logger.info("🔐 Fazendo login no EA Companion...")
            
            # Aguarda app carregar
            time.sleep(3)
            
            # Procura campo de email
            # (IDs podem variar - precisa inspecionar app)
            try:
                email_field = self.driver.find_element(
                    AppiumBy.ID, 
                    "com.ea.gp.fifacompanion:id/email_input"
                )
                email_field.send_keys(email)
                time.sleep(1)
            except:
                # Tenta método alternativo
                email_field = self.driver.find_element(
                    AppiumBy.XPATH,
                    "//android.widget.EditText[@content-desc='Email']"
                )
                email_field.send_keys(email)
                time.sleep(1)
            
            # Procura campo de senha
            try:
                password_field = self.driver.find_element(
                    AppiumBy.ID,
                    "com.ea.gp.fifacompanion:id/password_input"
                )
                password_field.send_keys(password)
                time.sleep(1)
            except:
                password_field = self.driver.find_element(
                    AppiumBy.XPATH,
                    "//android.widget.EditText[@content-desc='Password']"
                )
                password_field.send_keys(password)
                time.sleep(1)
            
            # Clica em login
            try:
                login_button = self.driver.find_element(
                    AppiumBy.ID,
                    "com.ea.gp.fifacompanion:id/login_button"
                )
                login_button.click()
            except:
                login_button = self.driver.find_element(
                    AppiumBy.XPATH,
                    "//android.widget.Button[@text='Login']"
                )
                login_button.click()
            
            time.sleep(5)  # Aguarda login
            
            self.logger.info("✅ Login realizado!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro no login: {e}")
            self.logger.info("💡 Pode precisar inspecionar o app para encontrar IDs corretos")
            return False
    
    def navigate_to_transfer_market(self):
        """Navega para Transfer Market no app"""
        try:
            self.logger.info("🧭 Navegando para Transfer Market...")
            
            # Aguarda carregar
            time.sleep(2)
            
            # Procura menu ou botão Transfer Market
            # (IDs precisam ser inspecionados no app)
            try:
                transfer_market = self.driver.find_element(
                    AppiumBy.XPATH,
                    "//android.widget.TextView[@text='Transfer Market']"
                )
                transfer_market.click()
            except:
                # Tenta método alternativo
                transfer_market = self.driver.find_element(
                    AppiumBy.ID,
                    "com.ea.gp.fifacompanion:id/transfer_market"
                )
                transfer_market.click()
            
            time.sleep(3)
            self.logger.info("✅ Chegou ao Transfer Market")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao navegar: {e}")
            return False
    
    def list_player(self, player_name, price):
        """Lista jogador no mercado"""
        return self.list_player_for_sale(price)
    
    def list_player_for_sale(self, price):
        """Lista jogador para venda por preço específico"""
        try:
            self.logger.info(f"📝 Listando jogador por {price} coins...")
            
            # Navega para My Club -> Transfer List se necessário
            # (Pode já estar na tela correta)
            
            # Procura botão "List for Transfer" ou "Sell"
            list_button_found = False
            try:
                list_button = self.driver.find_element(
                    AppiumBy.XPATH,
                    "//android.widget.Button[@text='List for Transfer']"
                )
                list_button.click()
                list_button_found = True
                time.sleep(2)
            except:
                try:
                    list_button = self.driver.find_element(
                        AppiumBy.XPATH,
                        "//android.widget.Button[@text='Sell']"
                    )
                    list_button.click()
                    list_button_found = True
                    time.sleep(2)
                except:
                    # Tenta por ID
                    try:
                        list_button = self.driver.find_element(
                            AppiumBy.ID,
                            "com.ea.gp.fifacompanion:id/list_for_transfer"
                        )
                        list_button.click()
                        list_button_found = True
                        time.sleep(2)
                    except:
                        self.logger.warning("Botão List for Transfer não encontrado. Tentando método alternativo...")
            
            if not list_button_found:
                # Tenta tocar em coordenadas padrão (fallback)
                self.driver.tap([(500, 800)], 100)  # Coordenadas aproximadas
                time.sleep(2)
            
            # Preenche preço
            price_filled = False
            try:
                price_field = self.driver.find_element(
                    AppiumBy.ID,
                    "com.ea.gp.fifacompanion:id/price_input"
                )
                price_field.clear()
                price_field.send_keys(str(price))
                price_filled = True
                time.sleep(1)
            except:
                try:
                    # Tenta por XPATH
                    price_field = self.driver.find_element(
                        AppiumBy.XPATH,
                        "//android.widget.EditText[@content-desc='Price']"
                    )
                    price_field.clear()
                    price_field.send_keys(str(price))
                    price_filled = True
                    time.sleep(1)
                except:
                    self.logger.warning("Campo de preço não encontrado. Pode precisar inspecionar app.")
            
            if not price_filled:
                # Tenta digitar diretamente (pode funcionar se campo estiver focado)
                from appium.webdriver.common.appiumby import AppiumBy
                self.driver.execute_script("mobile: type", {"text": str(price)})
                time.sleep(1)
            
            # Confirma
            confirm_found = False
            try:
                confirm_button = self.driver.find_element(
                    AppiumBy.XPATH,
                    "//android.widget.Button[@text='Confirm']"
                )
                confirm_button.click()
                confirm_found = True
                time.sleep(2)
            except:
                try:
                    confirm_button = self.driver.find_element(
                        AppiumBy.XPATH,
                        "//android.widget.Button[@text='List']"
                    )
                    confirm_button.click()
                    confirm_found = True
                    time.sleep(2)
                except:
                    try:
                        confirm_button = self.driver.find_element(
                            AppiumBy.ID,
                            "com.ea.gp.fifacompanion:id/confirm_button"
                        )
                        confirm_button.click()
                        confirm_found = True
                        time.sleep(2)
                    except:
                        self.logger.warning("Botão de confirmação não encontrado")
            
            if confirm_found:
                self.logger.info("✅ Jogador listado!")
                return True
            else:
                self.logger.warning("⚠️  Não foi possível confirmar listagem")
                return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao listar jogador: {e}")
            return False
    
    def buy_player(self, max_price):
        """Compra jogador do mercado"""
        try:
            self.logger.info(f"🛒 Buscando jogador até {max_price} coins...")
            
            # Busca jogadores
            # (Implementação depende da estrutura do app)
            
            # Clica no primeiro jogador encontrado
            try:
                player = self.driver.find_element(
                    AppiumBy.XPATH,
                    "//android.widget.RecyclerView/android.view.ViewGroup[1]"
                )
                player.click()
                time.sleep(2)
            except:
                self.logger.warning("Jogador não encontrado")
                return False
            
            # Clica em Buy Now
            try:
                buy_button = self.driver.find_element(
                    AppiumBy.XPATH,
                    "//android.widget.Button[@text='Buy Now']"
                )
                buy_button.click()
                time.sleep(2)
            except:
                self.logger.warning("Botão Buy Now não encontrado")
                return False
            
            # Confirma compra
            try:
                confirm_button = self.driver.find_element(
                    AppiumBy.XPATH,
                    "//android.widget.Button[@text='Confirm']"
                )
                confirm_button.click()
                time.sleep(2)
            except:
                self.logger.warning("Botão de confirmação não encontrado")
            
            self.logger.info("✅ Jogador comprado!")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao comprar jogador: {e}")
            return False
    
    def take_screenshot(self, filename="screenshot.png"):
        """Tira screenshot do app"""
        try:
            if self.driver:
                self.driver.save_screenshot(filename)
                self.logger.info(f"📸 Screenshot salvo: {filename}")
                return True
        except Exception as e:
            self.logger.debug(f"Erro ao tirar screenshot: {e}")
        return False
    
    def inspect_app(self):
        """Inspeciona estrutura do app (útil para encontrar IDs)"""
        try:
            self.logger.info("🔍 Inspecionando estrutura do app...")
            
            # Obtém XML da página atual
            page_source = self.driver.page_source
            
            # Salva em arquivo para análise
            with open("app_structure.xml", "w", encoding="utf-8") as f:
                f.write(page_source)
            
            self.logger.info("✅ Estrutura salva em app_structure.xml")
            self.logger.info("💡 Use este arquivo para encontrar IDs dos elementos")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao inspecionar: {e}")
            return False

