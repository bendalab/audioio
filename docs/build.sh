#!/bin/bash

die () { echo "ERROR: $*" >&2; exit 2; }

for cmd in pdoc3; do
    command -v "$cmd" >/dev/null ||
        die "Missing $cmd; \`pip install $cmd\`"
done

PACKAGE="audioio"
DOCROOT="$(dirname "$(realpath "$0")")"
BUILDROOT="$(realpath $DOCROOT/../site)"

echo
echo "Clean up documentation of $PACKAGE"
echo

mkdir -p "$BUILDROOT"
rm -r "$BUILDROOT/$PACKAGE" 2> /dev/null || true

echo
echo "Building general documentation for $PACKAGE"
echo

cd "$DOCROOT/.."
mkdocs build --config-file .mkdocs.yml --site-dir "$BUILDROOT" 
cd - > /dev/null

echo
echo "Building API reference docs for $PACKAGE"
echo

cd "$DOCROOT/.."
pdoc3 --html --output-dir "$BUILDROOT" $PACKAGE
mv "$BUILDROOT/$PACKAGE" "$BUILDROOT/api"
cd - > /dev/null

echo
echo "Done. Docs in:"
echo
echo "    file://$BUILDROOT/$PACKAGE/index.html"
echo
