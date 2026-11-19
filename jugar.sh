#!/usr/bin/env bash
# Arranca Temple con el entorno que crea instalar.sh, sin tener que activarlo.
#
#   bash jugar.sh
#   bash jugar.sh --minutos 1      cualquier opcion de main.py (python main.py --help)

set -euo pipefail
cd "$(dirname "$0")"

CONDA=""
if command -v conda >/dev/null 2>&1; then
  CONDA="$(command -v conda)"
else
  for c in "$HOME/miniconda3/bin/conda" "$HOME/anaconda3/bin/conda" "$HOME/miniforge3/bin/conda" \
           "/opt/miniconda3/bin/conda" "/opt/homebrew/Caskroom/miniconda/base/bin/conda"; do
    if [[ -x "$c" ]]; then CONDA="$c"; break; fi
  done
fi
ENTORNO="${TEMPLE_ENTORNO:-temple}"
if [[ -z "$CONDA" ]] || ! "$CONDA" env list | awk '{print $1}' | grep -qx "$ENTORNO"; then
  echo "Temple no está instalado. Primero ejecuta  bash instalar.sh" >&2
  exit 1
fi
PYTHON="$("$CONDA" run -n "$ENTORNO" python -c 'import sys; print(sys.executable)')"
exec "$PYTHON" main.py "$@"
