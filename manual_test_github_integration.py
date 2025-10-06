#!/usr/bin/env python3
"""
Teste da integração GitHub API sem token (usando repo público)
"""

import asyncio
import os
import sys
from datetime import datetime, timedelta

# Adicionar src ao path
sys.path.insert(0, '/home/rootkit/Apps/xsweAgent/src')

from github_monitor.repository import GitHubRepository
from github_monitor.models import SearchCriteria


async def test_github_public_repo():
    """Testa busca em repositório público sem precisar de token."""
    print("🐙 TESTANDO GITHUB API - REPOSITÓRIO PÚBLICO")
    print("=" * 50)

    # Criar instância sem token para testar com repo público
    repo = GitHubRepository(
        repo_name="python/cpython",
        api_token=None,  # Teste sem token (apenas para repos públicos)
        user_agent="xSwE-Agent-Test"
    )
    
    print(f"Repositório: {repo.repo_name}")
    
    # Testar busca simples de issues abertas
    print("\n📃 Buscando primeiras 3 issues abertas:")
    
    criteria = SearchCriteria(
        state="open",
        labels=None,
        since=None,
        max_results=3
    )
    
    try:
        issues = await repo.get_issues(criteria)
        
        if not issues:
            print("❌ Nenhuma issue encontrada!")
        else:
            print(f"✅ Encontradas {len(issues)} issues")
            
            for issue in issues:
                print(f"\n🔖 #{issue.number}: {issue.title}")
                print(f"   Estado: {issue.state}")
                print(f"   Criada: {issue.created_at}")
                if issue.labels:
                    labels = ", ".join([label for label in issue.labels])
                    print(f"   Labels: {labels}")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    # Testar busca com labels específicas
    print("\n\n📋 Buscando issues com label 'bug':")
    
    criteria = SearchCriteria(
        state="all",
        labels=["bug"],
        since=None,
        max_results=2
    )
    
    try:
        issues = await repo.get_issues(criteria)
        
        if not issues:
            print("❌ Nenhuma issue com label 'bug' encontrada!")
        else:
            print(f"✅ Encontradas {len(issues)} issues com label 'bug'")
            
            for issue in issues:
                print(f"\n🐛 #{issue.number}: {issue.title}")
                print(f"   Estado: {issue.state}")
                print(f"   Criada: {issue.created_at}")
                if issue.labels:
                    labels = ", ".join([label for label in issue.labels])
                    print(f"   Labels: {labels}")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    # Testar busca com filtro de data
    one_month_ago = datetime.now() - timedelta(days=30)
    
    print(f"\n\n📅 Buscando issues criadas após {one_month_ago.strftime('%d/%m/%Y')}:")
    
    criteria = SearchCriteria(
        state="all",
        labels=None,
        since=one_month_ago,
        max_results=2
    )
    
    try:
        issues = await repo.get_issues(criteria)
        
        if not issues:
            print(f"❌ Nenhuma issue criada após {one_month_ago.strftime('%d/%m/%Y')}!")
        else:
            print(f"✅ Encontradas {len(issues)} issues recentes")
            
            for issue in issues:
                print(f"\n📌 #{issue.number}: {issue.title}")
                print(f"   Estado: {issue.state}")
                print(f"   Criada: {issue.created_at}")
                if issue.labels:
                    labels = ", ".join([label for label in issue.labels])
                    print(f"   Labels: {labels}")
            
    except Exception as e:
        print(f"❌ ERRO: {e}")
    
    print("\n" + "=" * 50)
    print("✅ TESTE CONCLUÍDO")


if __name__ == "__main__":
    asyncio.run(test_github_public_repo())