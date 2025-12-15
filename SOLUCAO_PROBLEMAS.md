# 🔧 Solução de Problemas Comuns

## ✅ Problema 1: Erro SSL no Futbin (CORRIGIDO)

**Erro:**
```
[ERRO] Erro ao buscar jogador: SSL: CERTIFICATE_VERIFY_FAILED
```

**Solução:** ✅ Já corrigido! O bot agora ignora a verificação SSL do Futbin.

---

## ⚠️ Problema 2: Navegação não funciona (Botões não encontrados)

**Erro:**
```
[AVISO] ❌ Não foi possível encontrar botão 'Ultimate Team'
[AVISO] ❌ Não foi possível encontrar botão 'Transfer Market'
```

**Causa:** As coordenadas da tela não estão calibradas.

**Solução:**

### Opção 1: Calibração Automática (Recomendado)

1. **Abra o jogo EA FC 26** e deixe na tela principal
2. Execute:
   ```powershell
   python calibrar_automatico.py
   ```
3. Siga as instruções na tela
4. O script vai encontrar automaticamente os botões usando OCR

### Opção 2: Verificar Pré-requisitos

Execute o diagnóstico:
```powershell
python diagnostico_bot.py
```

Isso vai verificar:
- ✅ Jogo está aberto?
- ✅ Resolução correta (1920x1080)?
- ✅ Tesseract instalado?
- ✅ Coordenadas calibradas?

---

## ⚠️ Problema 3: Time não foi criado

**Aviso:**
```
[AVISO] Não foi possível determinar se time existe. Tentando criar...
```

**Solução:**

1. **Verifique manualmente no app do celular** se o time foi criado
2. Se não aparecer, você pode:
   - Criar manualmente no jogo
   - Ou tentar novamente com o bot

**Nota:** O bot tenta criar automaticamente, mas pode falhar se:
- O jogo não estiver na tela correta
- Houver problemas de conexão
- A navegação não estiver calibrada

---

## 📋 Checklist Antes de Usar o Bot

Antes de iniciar o bot, certifique-se:

- [ ] **Jogo EA FC 26 está aberto** e visível na tela
- [ ] **Resolução: 1920x1080** (ou ajuste no `config.json`)
- [ ] **Tesseract OCR instalado** (para detecção de texto)
- [ ] **Coordenadas calibradas** (`python calibrar_automatico.py`)
- [ ] **Time criado** na conta (ou `auto_create: true` no config)
- [ ] **Conta logada** no jogo

---

## 🚀 Como Executar Corretamente

1. **Abra o jogo EA FC 26** e deixe na tela principal
2. **Execute a calibração:**
   ```powershell
   python calibrar_automatico.py
   ```
3. **Execute o bot:**
   ```powershell
   python run_gui.py
   ```
4. **Na interface gráfica:**
   - Configure a conta secundária (se necessário)
   - Selecione os módulos (Trading, Squad Battles, Objectives)
   - Clique em "Iniciar Bot"

---

## 💡 Dicas

- **Sempre calibre as coordenadas** antes de usar o bot pela primeira vez
- **Use a resolução 1920x1080** para melhor compatibilidade
- **Mantenha o jogo visível** na tela (não minimize)
- **Verifique os logs** na interface gráfica para ver o que está acontecendo

---

## 🆘 Ainda com Problemas?

Se os problemas persistirem:

1. Execute `python diagnostico_bot.py` e envie o resultado
2. Verifique os logs em `bot_log.txt`
3. Certifique-se que está usando a versão mais recente do código

