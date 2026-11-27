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

# prove the image really contains what we think it does
echo "==> Contents"
MOUNT=$(mktemp -d)
hdiutil attach "${OUT}" -mountpoint "${MOUNT}" -nobrowse -quiet
ls -1 "${MOUNT}"
echo "    Wallpapers: $(ls -1 "${MOUNT}/Wallpapers" | wc -l | tr -d ' ') files"
MISSING=0
for want in "${APP_NAME}.app" "How to install.pdf" "Install Winter Cabin - simple guide.pdf"; do
    if [ ! -e "${MOUNT}/${want}" ]; then
        echo "error: ${want} is not in the disk image" >&2
        MISSING=1
    fi
done
hdiutil detach "${MOUNT}" -quiet
rmdir "${MOUNT}" 2>/dev/null || true
[ "${MISSING}" -eq 0 ] || exit 1

SIZE_BYTES=$(stat -f%z "${OUT}")
SIZE_MB=$(( SIZE_BYTES / 1024 / 1024 ))
echo "==> ${OUT} is ${SIZE_MB} MB"
if [ "${SIZE_MB}" -ge 100 ]; then
    echo "warning: over the 100 MB target for sending by email or WhatsApp" >&2
fi
