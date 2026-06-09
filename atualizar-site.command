#!/bin/zsh
cd "$(dirname "$0")"
python3 scripts/build_site.py
echo
echo "Site atualizado em index.html"
echo "Abra index.html no navegador ou publique a pasta em um serviço estático."
echo
read "?Pressione Enter para fechar."

