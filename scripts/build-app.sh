#!/usr/bin/env bash
#
# Builds Winter Cabin.app as a universal (Apple Silicon + Intel) bundle.
#
# Ad-hoc signs by default. To sign and notarize properly instead, set:
#   DEVELOPER_ID="Developer ID Application: Your Name (TEAMID)"
#   NOTARY_PROFILE="the-keychain-profile-name"    # optional, enables notarytool
#
set -euo pipefail
cd "$(dirname "$0")/.."

APP_NAME="Winter Cabin"
EXE="WinterCabin"
BUNDLE="build/${APP_NAME}.app"
RES_BUNDLE="WinterCabin_WinterCabin.bundle"

echo "==> Toolchain"
swift --version

echo "==> Building universal binary (arm64 + x86_64)"
swift build -c release --arch arm64 --arch x86_64

# universal builds land in .build/apple/Products/Release; fall back to a search
BIN_DIR=".build/apple/Products/Release"
if [ ! -f "${BIN_DIR}/${EXE}" ]; then
    FOUND=$(find .build -type f -name "${EXE}" -perm -u+x 2>/dev/null | head -1 || true)
    if [ -z "${FOUND}" ]; then
        echo "error: ${EXE} not found after build" >&2
        exit 1
    fi
    BIN_DIR=$(dirname "${FOUND}")
    echo "    using ${BIN_DIR}"
fi

echo "==> Assembling ${BUNDLE}"
rm -rf "${BUNDLE}"
mkdir -p "${BUNDLE}/Contents/MacOS" "${BUNDLE}/Contents/Resources"

cp "${BIN_DIR}/${EXE}" "${BUNDLE}/Contents/MacOS/${EXE}"
chmod +x "${BUNDLE}/Contents/MacOS/${EXE}"

RES_PATH="${BIN_DIR}/${RES_BUNDLE}"
if [ ! -d "${RES_PATH}" ]; then
    RES_PATH=$(find .build -type d -name "${RES_BUNDLE}" 2>/dev/null | head -1 || true)
fi
if [ -z "${RES_PATH}" ] || [ ! -d "${RES_PATH}" ]; then
    echo "error: resource bundle ${RES_BUNDLE} not found" >&2
    exit 1
fi
cp -R "${RES_PATH}" "${BUNDLE}/Contents/Resources/"

cp scripts/Info.plist "${BUNDLE}/Contents/Info.plist"
printf 'APPL????' > "${BUNDLE}/Contents/PkgInfo"

echo "==> Icon"
iconutil -c icns scripts/AppIcon.iconset -o "${BUNDLE}/Contents/Resources/AppIcon.icns"

echo "==> Architectures"
lipo -info "${BUNDLE}/Contents/MacOS/${EXE}"

if [ -n "${DEVELOPER_ID:-}" ]; then
    echo "==> Signing with Developer ID"
    codesign --force --options runtime --timestamp \
        --sign "${DEVELOPER_ID}" "${BUNDLE}/Contents/Resources/${RES_BUNDLE}"
    codesign --force --options runtime --timestamp \
        --sign "${DEVELOPER_ID}" "${BUNDLE}"
    if [ -n "${NOTARY_PROFILE:-}" ]; then
        echo "==> Notarizing (this takes a few minutes)"
        ditto -c -k --keepParent "${BUNDLE}" "build/notarize.zip"
        xcrun notarytool submit "build/notarize.zip" \
            --keychain-profile "${NOTARY_PROFILE}" --wait
        xcrun stapler staple "${BUNDLE}"
        rm -f "build/notarize.zip"
    else
        echo "    NOTARY_PROFILE not set - signed but not notarized."
    fi
else
    echo "==> Signing ad-hoc (no Developer ID set)"
    codesign --force --sign - "${BUNDLE}/Contents/Resources/${RES_BUNDLE}"
    codesign --force --sign - "${BUNDLE}"
fi

codesign --verify --verbose=2 "${BUNDLE}"
echo "==> Built ${BUNDLE}"
