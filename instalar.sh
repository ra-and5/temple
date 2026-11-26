#!/usr/bin/env bash
# Instala Temple en un equipo limpio con macOS o Ubuntu.
#
#   bash instalar.sh        pregunta antes de instalar Miniconda
#   bash instalar.sh -y     no pregunta nada (lo usan los tests de GitHub)
#
# Que hace, en orden
#   1. Busca Conda. Si no esta, instala Miniconda en ~/miniconda3 (sin tocar
#      la configuracion de la terminal).
#   2. Crea el entorno "temple" con Python 3.12, porque mediapipe 0.10.21 no
#      tiene version para Python 3.13 o superior.
#   3. Instala las librerias de requirements.txt, con las versiones fijadas.
#   4. Descarga los tres modelos de MediaPipe en models/ y comprueba que son
#      los mismos con los que se probo el juego.
#   5. Pasa los tests para comprobar que todo funciona.
# Se puede repetir sin miedo. Lo que ya esta hecho se salta.

set -euo pipefail

ENTORNO="${TEMPLE_ENTORNO:-temple}"  # se cambia solo para probar los scripts
SI=0
[[ "${1:-}" == "-y" ]] && SI=1
cd "$(dirname "$0")"

paso() { printf '\n\033[1;33m==> %s\033[0m\n' "$1"; }
error() { printf '\n\033[1;31mError. %s\033[0m\n' "$1" >&2; exit 1; }

SISTEMA="$(uname -s)"
ARQUITECTURA="$(uname -m)"
case "$SISTEMA" in
  Darwin) NOMBRE_SO="MacOSX" ;;
  Linux) NOMBRE_SO="Linux" ;;
  *) error "Temple funciona en macOS y en Linux, y este equipo es $SISTEMA." ;;
esac
command -v curl >/dev/null || error "Hace falta curl para descargar. En Ubuntu, sudo apt install curl"

# ---------- 1. Conda ----------
paso "1/5 Buscando Conda"
CONDA=""
if command -v conda >/dev/null 2>&1; then
  CONDA="$(command -v conda)"
else
  for c in "$HOME/miniconda3/bin/conda" "$HOME/anaconda3/bin/conda" "$HOME/miniforge3/bin/conda" \
           "/opt/miniconda3/bin/conda" "/opt/homebrew/Caskroom/miniconda/base/bin/conda"; do
    if [[ -x "$c" ]]; then CONDA="$c"; break; fi
  done
fi

if [[ -z "$CONDA" ]]; then
  echo "No hay Conda en este equipo. Se instalara Miniconda en $HOME/miniconda3 (unos 500 MB)."
  if [[ $SI -eq 0 ]]; then
    read -r -p "¿Seguimos? [s/N] " respuesta
    [[ "$respuesta" =~ ^[sSyY]$ ]] || error "Instalación cancelada."
  fi
  instalador="$(mktemp -d)/miniconda.sh"
  curl -fsSL -o "$instalador" \
    "https://repo.anaconda.com/miniconda/Miniconda3-latest-${NOMBRE_SO}-${ARQUITECTURA}.sh" \
    || error "No se pudo descargar Miniconda para ${NOMBRE_SO} ${ARQUITECTURA}."
  bash "$instalador" -b -p "$HOME/miniconda3"
  rm -f "$instalador"
  # Marca para que desinstalar.sh sepa que esta Miniconda la puso Temple
  touch "$HOME/miniconda3/.instalada_por_temple"
  CONDA="$HOME/miniconda3/bin/conda"
fi
echo "Conda en $CONDA"

# ---------- 2. Entorno ----------
paso "2/5 Entorno \"$ENTORNO\" con Python 3.12"
if "$CONDA" env list | awk '{print $1}' | grep -qx "$ENTORNO"; then
  echo "Ya existe, se aprovecha."
else
  # Con conda-forge no hace falta aceptar las condiciones de los canales de Anaconda
  "$CONDA" create -y -q -n "$ENTORNO" -c conda-forge --override-channels python=3.12
fi
PYTHON="$("$CONDA" run -n "$ENTORNO" python -c 'import sys; print(sys.executable)')"
"$PYTHON" -c 'import sys; assert sys.version_info[:2] == (3, 12), sys.version' \
  || error "El entorno $ENTORNO no tiene Python 3.12. Bórralo con  conda env remove -n $ENTORNO  y repite."
echo "Python en $PYTHON"

# ---------- 3. Librerias ----------
paso "3/5 Librerías (mediapipe, opencv, pygame, numpy)"
"$PYTHON" -m pip install -q --upgrade pip
"$PYTHON" -m pip install -q -r requirements.txt

# ---------- 4. Modelos ----------
paso "4/5 Modelos de MediaPipe"
if command -v sha256sum >/dev/null; then HUELLA="sha256sum"; else HUELLA="shasum -a 256"; fi
URL="https://storage.googleapis.com/mediapipe-models"
mkdir -p models
# nombre, ruta en el servidor y huella del archivo con el que se probo Temple
while read -r nombre ruta huella; do
  destino="models/$nombre.task"
  if [[ ! -s "$destino" ]]; then
    echo "Descargando $nombre"
    curl -fsSL -o "$destino.tmp" "$URL/$ruta/float16/latest/$nombre.task" \
      || error "No se pudo descargar $nombre. ¿Hay internet?"
    mv "$destino.tmp" "$destino"
  fi
  if [[ "$($HUELLA "$destino" | cut -d' ' -f1)" == "$huella" ]]; then
    echo "$nombre listo"
  else
    echo "Aviso. $nombre no es el mismo con el que se probó Temple (Google lo ha actualizado). Debería funcionar igual."
  fi
done <<'MODELOS'
pose_landmarker_full pose_landmarker/pose_landmarker_full 4eaa5eb7a98365221087693fcc286334cf0858e2eb6e15b506aa4a7ecdcec4ad
hand_landmarker hand_landmarker/hand_landmarker fbc2a30080c3c557093b5ddfc334698132eb341044ccee322ccf8bcf3607cde1
face_landmarker face_landmarker/face_landmarker 64184e229b263107bc2b804c6625db1341ff2bb731874b0bcc2fe6544e0bc9ff
MODELOS

# ---------- 5. Comprobar ----------
paso "5/5 Comprobando que todo funciona (unos 2 minutos)"
# Los tests abren la interfaz sin ventana ni sonido
if ! salida="$(SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy "$PYTHON" -m unittest discover tests 2>&1)"; then
  echo "$salida" | tail -n 40
  error "Algún test falla. Copia lo de arriba y pásaselo a Rares."
fi
echo "$salida" | grep -E "^(Ran|OK)"

printf '\n\033[1;32mTemple está instalado.\033[0m Para jugar\n\n    bash jugar.sh\n\nPara quitarlo, bash desinstalar.sh\n\n'
