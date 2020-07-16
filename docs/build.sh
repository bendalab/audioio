#!/bin/bash

die () { echo "ERROR: $*" >&2; exit 2; }

for cmd in pdoc3; do
    command -v "$cmd" >/dev/null ||
        die "Missing $cmd; \`pip install $cmd\`"
done

PACKAGE="audioio"
DOCROOT="$(dirname "$(realpath "$0")")"
BUILDROOT="$DOCROOT/build"

echo
echo "Building API reference docs for $PACKAGE"
echo

mkdir -p "$BUILDROOT"
rm -r "$BUILDROOT/$PACKAGE" 2> /dev/null || true
cd "$DOCROOT/.."
pdoc3 --html --output-dir "$BUILDROOT" $PACKAGE
cd - > /dev/null

echo
echo "Done. Docs in:"
echo
echo "    file://$BUILDROOT/$PACKAGE/index.html"
echo
