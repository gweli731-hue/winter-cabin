#!/usr/bin/env bash
#
# Packs Winter Cabin.app, the Wallpapers folder and the install guide into
# one compressed disk image: dist/WinterCabin.dmg
#
set -euo pipefail
cd "$(dirname "$0")/.."

APP_NAME="Winter Cabin"
APP="build/${APP_NAME}.app"
STAGE="build/dmg"
OUT="dist/WinterCabin.dmg"

if [ ! -d "${APP}" ]; then
    echo "error: ${APP} not found - run scripts/build-app.sh first" >&2
    exit 1
fi

echo "==> Staging"
rm -rf "${STAGE}"
mkdir -p "${STAGE}" dist
cp -R "${APP}" "${STAGE}/"
ln -s /Applications "${STAGE}/Applications"

mkdir -p "${STAGE}/Wallpapers"
cp Wallpapers/* "${STAGE}/Wallpapers/"

for doc in "How to install.pdf" "Install Winter Cabin - simple guide.pdf"; do
    if [ -f "dist/${doc}" ]; then
        cp "dist/${doc}" "${STAGE}/"
    else
        echo "warning: dist/${doc} is missing from the repository" >&2
    fi
done

echo "==> Building disk image"
rm -f "${OUT}"
hdiutil create \
    -volname "${APP_NAME}" \
    -srcfolder "${STAGE}" \
    -ov -format UDZO -imagekey zlib-level=9 \
    "${OUT}"

hdiutil verify "${OUT}"

SIZE_BYTES=$(stat -f%z "${OUT}")
SIZE_MB=$(( SIZE_BYTES / 1024 / 1024 ))
echo "==> ${OUT} is ${SIZE_MB} MB"
if [ "${SIZE_MB}" -ge 100 ]; then
    echo "warning: over the 100 MB target for sending by email or WhatsApp" >&2
fi
