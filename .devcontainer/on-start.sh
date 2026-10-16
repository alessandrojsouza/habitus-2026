#!/usr/bin/env bash
# Script executado na inicialização do GitHub Codespaces / Devcontainer.
# Corrige o roteamento da rede bridge do Docker em ambientes containerizados (DinD).

echo "🔧 Configurando rede do Docker para o Codespaces..."

# Permite o encaminhamento de pacotes na tabela legada do iptables
sudo iptables-legacy -P FORWARD ACCEPT 2>/dev/null || true

# Desativa a interceptação de pacotes internos da bridge pelo iptables
sudo sysctl -w net.bridge.bridge-nf-call-iptables=0 2>/dev/null || true
sudo sysctl -w net.bridge.bridge-nf-call-ip6tables=0 2>/dev/null || true
sudo sysctl -w net.bridge.bridge-nf-call-arptables=0 2>/dev/null || true

echo "✅ Rede do Docker configurada com sucesso!"
