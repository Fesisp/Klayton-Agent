# Testes Offline do PokeBot-Pro

Este documento descreve rapidamente como rodar os testes offline do bot, focados em percepção (OCR) e decisão de batalha.

## Pré-requisitos

- Python 3.x
- Dependências do projeto instaladas:

```powershell
cd PokeBot_Pro
python -m pip install -r requirements.txt
python -m pip install pytest
```

> Obs.: os testes atuais não precisam do jogo aberto; usam stubs e funções puramente em memória.

## Como rodar os testes

Na raiz do repositório (`PokeBot-Pro`):

```powershell
cd C:\Users\Spinola\OneDrive\Laboratorio\VSCode\PokeBot-Pro
pytest
```

Para rodar apenas os testes de OCR e estratégia:

```powershell
pytest PokeBot_Pro/tests/test_ocr_and_strategy.py
```

## O que está coberto hoje

- `OCREngine.clean_move_name` – garante que nomes de golpes são limpos corretamente (removendo PP como `23/25`).
- `BattleStrategy.get_best_move` – cenário simples em que um golpe super efetivo (ex.: `Thunderbolt`) é escolhido sobre um golpe fraco (ex.: `Tackle`).

## Próximos passos sugeridos

- Adicionar testes sintéticos para `GameStateDetector.detect_state` usando imagens artificiais.
- Criar fixtures de imagens pequenas para validar outros fluxos de OCR (lista de pokémons, HUD, etc.).
- Cobrir mais métodos de `TeamManager` relacionados a atualização de equipe e golpes.
