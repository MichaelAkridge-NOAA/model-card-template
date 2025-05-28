# Dockerfile
FROM ghcr.io/quarto-dev/quarto:latest

# 1) Install system dependencies
USER root
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       fonts-liberation \
       make \
       git \
       perl \
       curl \
       xz-utils \
  && rm -rf /var/lib/apt/lists/*

# 2) Install TinyTeX via Quarto (adds tlmgr to PATH)
RUN quarto install tool tinytex --no-prompt --update-path

# 3) Set tlmgr to use the CTAN mirror and then update/install
RUN tlmgr option repository https://mirror.ctan.org/systems/texlive/tlnet \
  && tlmgr update --self --all \
  && tlmgr install \
       collection-basic \
       collection-latexrecommended

# 4) Copy your project into the container
WORKDIR /home/quarto/project
COPY . /home/quarto/project

# 5) Default entrypoint: render your QMD → PDF
ENTRYPOINT ["quarto", "render"]
CMD ["model_card_modern.qmd", "--to", "pdf"]
