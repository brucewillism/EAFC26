# 🎮 Instalação do Gamepad Virtual

## 📦 Dependência Necessária

O bot agora usa **vgamepad** para emular um gamepad virtual (Xbox 360).

### Instalação

```powershell
pip install vgamepad
```

### Requisitos do Sistema

- **Windows**: Funciona nativamente
- **Administrador**: Pode ser necessário executar como administrador na primeira vez

## ✅ Verificação

Após instalar, o bot detectará automaticamente se o gamepad está disponível:

- ✅ **Gamepad disponível**: Usa gamepad com todas as funcionalidades
- ⚠️ **Gamepad não disponível**: Usa teclado como fallback

## 🎯 Funcionalidades do Gamepad

### 1. **Analógico com Oscilações**
- Movimento do analógico com oscilação de 1-5 graus
- Simula movimento humano do polegar

### 2. **Delays Específicos**
- **In-game**: 50-200ms entre ações
- **Menus**: 1-4s entre ações

### 3. **Botões Mapeados**
- **A**: Pass curto
- **B**: Tackle/Clear
- **X**: Chute
- **Y**: Through pass
- **LB**: Call second player
- **RB**: Skill move (proibido 4-5 estrelas)
- **RT**: Sprint
- **LT**: (não usado)

## 🔧 Solução de Problemas

### Erro: "vgamepad não encontrado"

**Solução:**
```powershell
pip install vgamepad
```

### Erro: "Gamepad não inicializado"

**Possíveis causas:**
1. Driver não instalado
2. Permissões insuficientes
3. Outro programa usando gamepad

**Solução:**
- Execute como administrador
- Feche outros programas que usam gamepad
- Reinicie o bot

### Bot usa teclado mesmo com gamepad instalado

**Verifique:**
1. Se `vgamepad` está instalado: `pip list | findstr vgamepad`
2. Se há erros nos logs
3. Se o gamepad foi inicializado (procure por "✅ Gamepad virtual inicializado")

## 📝 Notas

- O bot funciona **com ou sem** gamepad
- Se gamepad não estiver disponível, usa teclado automaticamente
- Todas as estratégias funcionam em ambos os modos
