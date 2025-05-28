# PowerShell script for installing minimal TeX packages
# Must be run after installing TinyTeX

# Ensure TinyTeX is installed and in PATH
$tinyTexPath = "$env:USERPROFILE\.TinyTeX\bin\windows"
if (Test-Path $tinyTexPath) {
    $env:Path = "$tinyTexPath;$env:Path"
} else {
    Write-Error "TinyTeX not found. Please install it first using 'quarto install tool tinytex'"
    exit 1
}

Write-Host "Updating tlmgr..."
tlmgr update --self

Write-Host "Installing minimal TeX packages..."
$packages = @(
    "collection-basic",
    "collection-latex",
    "collection-fontsrecommended",
    "collection-latexrecommended",
    "geometry",
    "fancyhdr",
    "xcolor",
    "tcolorbox",
    "fontspec"
)

foreach ($package in $packages) {
    Write-Host "Installing $package..."
    tlmgr install $package
}

Write-Host "Installation complete!"
