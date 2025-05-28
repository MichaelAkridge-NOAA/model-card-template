#!/bin/bash
# Install minimal TeX packages for model cards

# Ensure tlmgr is in PATH
if [[ -d "$HOME/.TinyTeX" ]]; then
    export PATH="$HOME/.TinyTeX/bin/x86_64-linux:$PATH"
elif [[ -d "/opt/TinyTeX" ]]; then
    export PATH="/opt/TinyTeX/bin/x86_64-linux:$PATH"
fi

# Update package manager
tlmgr update --self

# Install required collections and packages
tlmgr install \
    collection-basic \
    collection-latex \
    collection-fontsrecommended \
    collection-latexrecommended \
    geometry \
    fancyhdr \
    xcolor \
    tcolorbox \
    fontspec

# Verify installation
echo "Verifying LaTeX packages..."
kpsewhich geometry.sty
kpsewhich fancyhdr.sty
kpsewhich xcolor.sty
kpsewhich tcolorbox.sty
kpsewhich fontspec.sty
