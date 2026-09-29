#!/usr/bin/env bash
# Downloads all datasets needed for the Babylonian literature fragment-joining project.
# Run from the babylonian-literature/ directory: bash download_data.sh
set -e

DATA_DIR="$(dirname "$0")/data"
mkdir -p "$DATA_DIR"

# ---------------------------------------------------------------------------
# 1. eBL fragments — full dataset (~25k tablets, transliterated cuneiform)
#    Source: Electronic Babylonian Library, LMU Munich
#    License: CC BY-NC-SA 4.0
#    Snapshot: 1 September 2023
# ---------------------------------------------------------------------------
echo "Downloading eBL full dataset from Zenodo..."
curl -L --progress-bar \
  -o "$DATA_DIR/ebl_fragments.json" \
  "https://zenodo.org/record/10018951/files/fragments.json"

echo "Downloading eBL 1k sample from GitHub (useful for quick dev/testing)..."
curl -L --progress-bar \
  -o "$DATA_DIR/ebl_fragments_sample.json" \
  "https://raw.githubusercontent.com/ElectronicBabylonianLiterature/transliterated-fragments/main/ebl/fragments.json"

# ---------------------------------------------------------------------------
# 2. CDLI ATF dump — hundreds of thousands of cuneiform tablets
#    Source: Cuneiform Digital Library Initiative
#    Note: bulk export frozen as of August 2022, but still the largest dump
#    Requires git-lfs: brew install git-lfs
# ---------------------------------------------------------------------------
echo ""
echo "Downloading CDLI ATF dump..."
if ! command -v git-lfs &> /dev/null; then
  echo "  git-lfs not found, installing via Homebrew..."
  brew install git-lfs
fi

git lfs install
GIT_LFS_SKIP_SMUDGE=0 git clone --depth=1 \
  https://github.com/cdli-gh/data.git "$DATA_DIR/cdli_repo"

cp "$DATA_DIR/cdli_repo/cdliatf_unblocked.atf" "$DATA_DIR/cdliatf_unblocked.atf"
cp "$DATA_DIR/cdli_repo/cdli_cat.csv"           "$DATA_DIR/cdli_cat.csv"
rm -rf "$DATA_DIR/cdli_repo"

# ---------------------------------------------------------------------------
# 3. Gilgamesh canonical text — all 12 Standard Babylonian tablets
#    Source: Electronic Babylonian Library public API
#    Includes: canonical ATF, English translations, manuscript variants, gap markers
# ---------------------------------------------------------------------------
echo ""
echo "Downloading Gilgamesh canonical text (all 12 tablets) from eBL API..."
mkdir -p "$DATA_DIR/gilgamesh"
BASE="https://www.ebl.lmu.de/api/texts/L/1/4/chapters/Standard%20Babylonian"
for TABLET in I II III IV V VI VII VIII IX X XI XII; do
  echo "  Tablet $TABLET..."
  curl -s -o "$DATA_DIR/gilgamesh/tablet_${TABLET}.json" \
    "${BASE}/${TABLET}/display"
  sleep 0.3
done

echo ""
echo "All done. Files in $DATA_DIR:"
ls -lh "$DATA_DIR"
ls -lh "$DATA_DIR/gilgamesh"
