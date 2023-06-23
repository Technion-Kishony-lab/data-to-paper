## How to manually install latex package example (on linux)

1. download `siunitx` from CTAN (https://ctan.org/pkg/siunitx)
2. unzip the .zip you downloaded using ```unzip siunitx.zip -d siunitx```
3. cd into the `siunitx\siunitx` folder
4. run ```latex siunitx.ins``` command to create the `.sty` file
5. to install for all users run ```sudo mkdir -p /usr/share/texlive/texmf-dist/tex/latex/siunitx``` to create the designated folder
6. move all `.sty` files to the folder we created ```sudo mv *.sty /usr/share/texlive/texmf-dist/tex/latex/siunitx/```
7. update latex package database ```sudo mktexlsr```