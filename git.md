# Guia: Guia de comandos Git

## 1. Subir ajustes

#### 1. Verificar o que mudou:
```bash
git status
```

#### 2. Preparar os arquivos (Stage):
```bash
git add .
```

#### 3. Gravar as alterações (Commit):
```bash
git commit -m "ajuste: ..."
```

#### 4. Enviar para o servidor (Push):
```bash
git push origin master
```

## 2. Descer Ajustes (Baixar do Servidor)

#### 1. Puxar as novidades:
```bash
git pull origin main
```

#### 2. Verificar o histórico recente:
```bash
git log --oneline -n 5
```

## 3. Comandos Úteis de Manutenção

#### * Descartar mudanças locais em um arquivo (Reset):
```bash
git checkout -- nome_do_arquivo.py
```

#### * Ver as diferenças antes de dar o "add":
```bash
git diff
```

#### * Criar uma nova "ramo" (Branch) para testes:
```bash
git checkout -b nova-estrategia
```
