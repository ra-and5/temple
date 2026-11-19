#!/usr/bin/env bash
# Quita lo que instalo instalar.sh.
#
#   bash desinstalar.sh        pregunta antes de borrar cada cosa
#   bash desinstalar.sh -y     no pregunta (borra tambien el progreso)
#
# Borra el entorno "temple" y los modelos. El progreso (datos/) solo si se
# confirma. Miniconda solo si la instalo Temple (instalar.sh deja una marca),
# nunca una que ya tuvieras. La carpeta del juego se borra a mano al final.

set -euo pipefail

ENTORNO="${TEMPLE_ENTORNO:-temple}"  # se cambia solo para probar los scripts
SI=0
[[ "${1:-}" == "-y" ]] && SI=1
cd "$(dirname "$0")"

paso() { printf '\n\033[1;33m==> %s\033[0m\n' "$1"; }
pregunta() {
  [[ $SI -eq 1 ]] && return 0
  read -r -p "$1 [s/N] " respuesta
  [[ "$respuesta" =~ ^[sSyY]$ ]]
}

CONDA=""
if command -v conda >/dev/null 2>&1; then
  CONDA="$(command -v conda)"
else
  for c in "$HOME/miniconda3/bin/conda" "$HOME/anaconda3/bin/conda" "$HOME/miniforge3/bin/conda" \
           "/opt/miniconda3/bin/conda" "/opt/homebrew/Caskroom/miniconda/base/bin/conda"; do
    if [[ -x "$c" ]]; then CONDA="$c"; break; fi
  done
fi

paso "Entorno \"$ENTORNO\""
if [[ -n "$CONDA" ]] && "$CONDA" env list | awk '{print $1}' | grep -qx "$ENTORNO"; then
  "$CONDA" env remove -y -q -n "$ENTORNO" >/dev/null
  echo "Borrado."
else
  echo "No estaba."
fi

paso "Modelos de MediaPipe"
rm -rf models
echo "Borrados."

paso "Tu progreso (lotos, racha y niveles)"
if [[ -d datos ]] && pregunta "¿Borrar también tu progreso?"; then
  rm -rf datos
  echo "Borrado."
else
  echo "Se queda en datos/."
fi

if [[ -f "$HOME/miniconda3/.instalada_por_temple" ]]; then
  paso "Miniconda (la instaló Temple en $HOME/miniconda3)"
  if pregunta "¿Borrar Miniconda? Si la usas para otras cosas, di que no."; then
    rm -rf "$HOME/miniconda3"
    echo "Borrada."
  else
    echo "Se queda."
  fi
fi

printf '\n\033[1;32mTemple está desinstalado.\033[0m Ya puedes borrar esta carpeta.\n\n'
