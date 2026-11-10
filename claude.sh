#!/usr/bin/env bash
# Instala ou atualiza o Claude Code pelo instalador oficial da Anthropic.
# Uso: bash instalar-claude-code.sh

set -Eeuo pipefail

INSTALL_URL="https://claude.ai/install.sh"

info() { printf '\n==> %s\n' "$*"; }
erro() { printf 'Erro: %s\n' "$*" >&2; exit 1; }

cleanup() {
  [[ -n "${installer:-}" && -f "$installer" ]] && rm -f -- "$installer"
}
trap cleanup EXIT

[[ "$(uname -s)" == "Linux" || "$(uname -s)" == "Darwin" ]] || \
  erro "Este script é destinado a Linux, macOS ou WSL."

if command -v curl >/dev/null 2>&1; then
  downloader=(curl --fail --silent --show-error --location)
elif command -v wget >/dev/null 2>&1; then
  downloader=(wget --quiet --output-document=-)
else
  erro "Instale curl ou wget e execute este script novamente."
fi

if command -v claude >/dev/null 2>&1; then
  info "Claude Code já encontrado: $(claude --version 2>/dev/null || printf 'versão indisponível')"
  info "Atualizando pela origem oficial"
else
  info "Instalando Claude Code"
fi

installer="$(mktemp "${TMPDIR:-/tmp}/claude-code-install.XXXXXX")"
"${downloader[@]}" "$INSTALL_URL" >"$installer"
[[ -s "$installer" ]] || erro "O instalador oficial foi baixado vazio."

# Equivale ao comando oficial: curl -fsSL https://claude.ai/install.sh | bash
bash "$installer"

# O instalador normalmente configura o PATH no arquivo de perfil. Tornamos a
# sessão atual capaz de verificar a instalação sem alterar nenhum perfil aqui.
export PATH="$HOME/.local/bin:$HOME/.claude/bin:$PATH"

if command -v claude >/dev/null 2>&1; then
  info "Concluído: $(claude --version)"
  printf '\nAbra um novo terminal (ou execute: exec "$SHELL" -l) e inicie com: claude\n'
else
  printf '\nInstalação concluída. Abra um novo terminal e execute: claude --version\n'
  printf 'Se o comando não for encontrado, confira as instruções emitidas pelo instalador acima.\n'
fi
