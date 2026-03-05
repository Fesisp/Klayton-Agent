#!/usr/bin/env python3
"""
Validador de Secrets - Verifica se há credenciais sendo commitadas
Uso: python tools/check_secrets.py
"""

import re
import subprocess
import sys
from pathlib import Path

# Padrões de credenciais conhecidos
SECRET_PATTERNS = {
    'telegram_token': r'\d{10}:[A-Za-z0-9_-]{35}',
    'discord_webhook': r'https://discord\.com/api/webhooks/\d+/[A-Za-z0-9_-]+',
    'openai_key': r'sk-[A-Za-z0-9]{48}',
    'google_api_key': r'AIza[0-9A-Za-z\-_]{35}',
    'github_token': r'ghp_[A-Za-z0-9]{36}',
    'aws_key': r'AKIA[0-9A-Z]{16}',
    'generic_api_key': r'api[_-]?key["\']?\s*[:=]\s*["\'][A-Za-z0-9_\-]{20,}["\']',
}

# Arquivos que NUNCA devem ser commitados
BLOCKED_FILES = [
    'config/settings.yaml',
    'config/secrets.yaml',
    '.env',
    'local_settings.yaml',
    'local_config.yaml',
]

# Arquivos permitidos (templates sem credenciais)
ALLOWED_FILES = [
    'config/settings.example.yaml',
    '.env.example',
]


def get_staged_files():
    """Retorna lista de arquivos no staging area."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True,
            text=True,
            check=True
        )
        return [f.strip() for f in result.stdout.split('\n') if f.strip()]
    except subprocess.CalledProcessError:
        return []


def get_staged_content():
    """Retorna o conteúdo completo do diff staged."""
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached'],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore',
            check=True
        )
        return result.stdout if result.stdout else ""
    except subprocess.CalledProcessError:
        return ""


def check_blocked_files(staged_files):
    """Verifica se há arquivos bloqueados no staging."""
    violations = []
    
    for staged_file in staged_files:
        # Normalizar path para comparação
        staged_normalized = staged_file.replace('\\', '/')
        
        for blocked in BLOCKED_FILES:
            blocked_normalized = blocked.replace('\\', '/')
            
            if staged_normalized == blocked_normalized:
                violations.append(f"❌ Arquivo bloqueado: {staged_file}")
    
    return violations


def check_secret_patterns(content):
    """Verifica padrões de credenciais no conteúdo."""
    violations = []
    
    if not content:
        return violations
    
    for name, pattern in SECRET_PATTERNS.items():
        matches = re.findall(pattern, content)
        if matches:
            # Não mostrar o segredo completo
            safe_preview = matches[0][:10] + '...' if len(matches[0]) > 10 else matches[0]
            violations.append(f"🔑 {name.replace('_', ' ').title()} detectado: {safe_preview}")
    
    return violations


def check_yaml_credentials(staged_files, content):
    """Verifica se YAMLs têm credenciais reais (não placeholders)."""
    violations = []
    
    yaml_files = [f for f in staged_files if f.endswith(('.yaml', '.yml'))]
    
    for yaml_file in yaml_files:
        # Pular arquivos permitidos (templates)
        if any(allowed in yaml_file for allowed in ALLOWED_FILES):
            continue
        
        # Verificar se tem campos de credenciais com valores reais
        cred_fields = ['telegram_bot_token', 'telegram_chat_id', 'discord_webhook_url', 'api_key']
        
        for field in cred_fields:
            # Buscar linhas com o campo
            pattern = rf'{field}\s*:\s*"([^"]+)"'
            matches = re.findall(pattern, content)
            
            for match in matches:
                # Verificar se NÃO é placeholder
                if not any(placeholder in match.upper() for placeholder in ['YOUR_', 'SEU_', 'EXAMPLE', 'TESTE']):
                    # Verificar se parece ser valor real (mais de 10 caracteres)
                    if len(match) > 10:
                        violations.append(f"⚠️  Possível credencial real em {yaml_file}: {field}")
    
    return violations


def main():
    """Função principal."""
    print("🔍 Verificando segurança do commit...\n")
    
    staged_files = get_staged_files()
    
    if not staged_files:
        print("ℹ️  Nenhum arquivo no staging area")
        return 0
    
    print(f"📁 Arquivos a commitar: {len(staged_files)}")
    for f in staged_files:
        print(f"   - {f}")
    print()
    
    all_violations = []
    
    # Check 1: Arquivos bloqueados
    print("🔍 Verificando arquivos bloqueados...")
    blocked_violations = check_blocked_files(staged_files)
    all_violations.extend(blocked_violations)
    
    if blocked_violations:
        print("❌ Encontrados arquivos bloqueados!")
        for v in blocked_violations:
            print(f"   {v}")
    else:
        print("✅ Nenhum arquivo bloqueado")
    print()
    
    # Check 2: Padrões de secrets
    print("🔍 Verificando padrões de credenciais...")
    content = get_staged_content()
    secret_violations = check_secret_patterns(content)
    all_violations.extend(secret_violations)
    
    if secret_violations:
        print("❌ Encontrados padrões de credenciais!")
        for v in secret_violations:
            print(f"   {v}")
    else:
        print("✅ Nenhum padrão suspeito")
    print()
    
    # Check 3: Credenciais em YAMLs
    print("🔍 Verificando YAMLs...")
    yaml_violations = check_yaml_credentials(staged_files, content)
    all_violations.extend(yaml_violations)
    
    if yaml_violations:
        print("⚠️  Avisos em arquivos YAML:")
        for v in yaml_violations:
            print(f"   {v}")
    else:
        print("✅ YAMLs parecem seguros")
    print()
    
    # Resultado final
    if all_violations:
        print("=" * 60)
        print("❌ COMMIT BLOQUEADO - Problemas de segurança detectados!")
        print("=" * 60)
        print("\n📋 Resumo dos problemas:")
        for v in all_violations:
            print(f"   {v}")
        print("\n✅ Solução:")
        print("   1. Remova credenciais reais dos arquivos")
        print("   2. Use placeholders (YOUR_TOKEN_HERE)")
        print("   3. Mantenha credenciais apenas em arquivos locais ignorados")
        print(f"\n   git reset HEAD <arquivo>")
        return 1
    else:
        print("=" * 60)
        print("✅ SEGURO - Nenhuma credencial detectada!")
        print("=" * 60)
        return 0


if __name__ == '__main__':
    sys.exit(main())
