# ⚠️ AVISO DE SEGURANÇA - COMFORT TRADE

## 🚨 RISCOS CRÍTICOS

O método **Comfort Trade** implementado neste bot envolve **RISCOS SIGNIFICATIVOS**:

### 1. **Banimento do Mercado de Transferências**
- A EA monitora transações suspeitas
- Comprar jogadores baratos por preços altos é facilmente detectável
- **Resultado**: Perda permanente do acesso ao Mercado de Transferências

### 2. **Reset de Coins**
- A EA pode remover todas as coins consideradas "ilegais"
- **Resultado**: Perda de todas as coins da conta

### 3. **Banimento da Conta**
- Em casos graves ou reincidência, a conta pode ser **permanentemente banida**
- **Resultado**: Perda total do acesso ao jogo

### 4. **Roubo de Credenciais**
- Este método requer que você forneça **email, senha e códigos de backup** da sua conta
- **Resultado**: O vendedor pode roubar sua conta completamente

---

## 📋 Como Funciona

### Método 1: Via Mercado (Market)
1. Cliente lista um jogador barato por preço alto (ex: bronze por 100.000 coins)
2. Bot encontra e compra esse jogador
3. Coins são transferidas (menos 5% de taxa da EA)

### Método 2: Via Farming
1. Bot faz login na conta do cliente
2. Joga partidas de Squad Battles
3. Vende cartas não utilizadas
4. Repete até atingir quantidade desejada

---

## ⚠️ RECOMENDAÇÕES DE SEGURANÇA

### Se você for o VENDEDOR:
1. **NUNCA** armazene senhas em texto plano
2. Use contas secundárias apenas
3. Limite quantidade de coins por transação
4. Espalhe transferências ao longo do tempo
5. Use múltiplos jogadores diferentes

### Se você for o COMPRADOR:
1. **NUNCA** forneça credenciais da sua conta principal
2. Use apenas contas secundárias
3. Mude senha e códigos de backup após a transação
4. Monitore sua conta durante e após a transação
5. Use apenas vendedores confiáveis

---

## 🔧 Configuração

No `config.json`:

```json
{
  "comfort_trade": {
    "enabled": false,
    "transfer_method": "market",
    "target_coins": 0,
    "coins_per_transaction": 50000,
    "transfer_delay_min": 300,
    "transfer_delay_max": 600,
    "client_account": {
      "email": "",
      "password": "",
      "backup_codes": []
    }
  }
}
```

### Parâmetros:
- `enabled`: Habilita/desabilita Comfort Trade
- `transfer_method`: "market" ou "farming"
- `target_coins`: Quantidade total de coins a transferir
- `coins_per_transaction`: Máximo por transação (recomendado: 50.000)
- `transfer_delay_min/max`: Delay entre transações (em segundos)

---

## ⚖️ DISCLAIMER

**Este bot é fornecido "como está", sem garantias.**

O uso do Comfort Trade é de **total responsabilidade do usuário**.

O desenvolvedor **NÃO se responsabiliza** por:
- Banimentos de contas
- Perda de coins
- Roubo de credenciais
- Qualquer outro dano resultante do uso deste método

**USE POR SUA CONTA E RISCO!**

---

## 💡 Alternativas Mais Seguras

1. **Trading Normal**: Use o bot de trading normal para ganhar coins legalmente
2. **Squad Battles**: Jogue partidas e ganhe recompensas
3. **Objetivos**: Complete objetivos diários
4. **Paciência**: Ganhe coins gradualmente ao longo do tempo

---

## 📞 Suporte

Se você tiver problemas ou dúvidas, consulte:
- `PROBLEMAS_IDENTIFICADOS.md`
- `SOLUCAO_PROBLEMAS.md`
- Logs do bot: `bot_log.txt`

