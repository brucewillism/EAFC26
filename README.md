# EA FC 26 Bot - Farming Bot

Bot automatizado para EA FC 26 que realiza:
- Trading de jogadores (compra e venda)
- Completar objetivos
- Jogar Squad Battles contra a máquina

## ⚠️ AVISOS IMPORTANTES

**USE POR SUA CONTA E RISCO!**

- Este bot pode violar os Termos de Serviço da EA
- Você pode ser banido permanentemente da sua conta
- Use apenas em contas secundárias ou teste
- O desenvolvedor não se responsabiliza por banimentos

## Requisitos

- Python 3.8 ou superior
- Windows 10/11
- EA FC 26 instalado no PC
- Resolução de tela: 1920x1080 (pode precisar ajustes para outras resoluções)

## Instalação

1. Instale as dependências:
```bash
pip install -r requirements.txt
```

2. Configure o arquivo `config.json` com suas preferências

3. Execute o bot:
```bash
python main.py
```

## Funcionalidades

### Trading Bot
- Compra e venda automática de jogadores
- Filtros configuráveis
- Gestão de lucros

### Squad Battles
- Joga partidas automáticas
- Seleção de dificuldade
- Completar objetivos

### Objetivos
- Completa objetivos diários/semanais automaticamente

## Configuração

Edite o arquivo `config.json` para personalizar:
- Intervalos de tempo
- Configurações de trading
- Dificuldade do Squad Battles
- Hotkeys de emergência

## Hotkeys

- `F9`: Pausar/Retomar bot
- `F10`: Parar bot completamente
- `ESC`: Sair do programa

## Estrutura do Projeto

```
EAfc2026/
├── main.py                 # Arquivo principal
├── config.json             # Configurações
├── bot/
│   ├── __init__.py
│   ├── controller.py       # Controle de mouse/teclado
│   ├── screen_capture.py   # Captura e análise de tela
│   ├── trading.py          # Módulo de trading
│   ├── squad_battles.py    # Módulo Squad Battles
│   └── objectives.py       # Módulo de objetivos
└── utils/
    ├── __init__.py
    └── logger.py          # Sistema de logs
```

## Notas

- O bot foi desenvolvido para resolução 1920x1080
- Pode precisar ajustes de coordenadas para outras resoluções
- Teste primeiro em modo seguro antes de usar em produção
- Sempre monitore o bot durante os primeiros usos

