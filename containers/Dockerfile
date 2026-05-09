# syntax=docker/dockerfile:1
# =========================================================================
# Dockerfile — Debian-slim single-stage sandbox for CTF + Web Pentesting
#
# Replaces the old Kali two-stage build (Dockerfile.base + Dockerfile).
# Drops: Metasploit, PostgreSQL, CME, evil-winrm, AD tooling, wireless,
#        network services, VPN, stealth/proxy tooling.
# Keeps: CTF tools + web application pentesting tools.
#
# Build:
#   ./scripts/build.sh
#
# Size: ~800 MB (down from 3 GB)
# Time: ~6-10 min (down from 25 min)
# =========================================================================

FROM debian:bookworm-slim

LABEL description="OPERATIONSPECTRE - Debian sandbox (CTF + Web Pentest)"

# ===== SYSTEM + RUNTIMES =====
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    sudo curl git vim nano unzip tar wget \
    apt-transport-https ca-certificates gnupg lsb-release \
    build-essential pkg-config \
    gcc libc6-dev libpcap-dev libssl-dev libffi-dev \
    python3 python3-pip python3-dev python3-venv python3-setuptools \
    pipx \
    nodejs npm \
    ruby ruby-dev \
    net-tools dnsutils whois \
    jq parallel ripgrep grep \
    less man-db procps htop \
    iproute2 iputils-ping netcat-openbsd \
    tmux

# ===== OBSCURA HEADLESS BROWSER (replaces Chromium — 70MB vs 300MB) =====
# Single binary, CDP-compatible (Puppeteer/Playwright), built-in stealth mode.
# https://github.com/h4ckf0r0day/obscura
RUN ARCH=$(uname -m) && \
    case "$ARCH" in \
        x86_64) OBSCURA_ARCH="x86_64" ;; \
        aarch64|arm64) OBSCURA_ARCH="aarch64" ;; \
        *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac && \
    curl -fsSL "https://github.com/h4ckf0r0day/obscura/releases/latest/download/obscura-${OBSCURA_ARCH}-linux.tar.gz" \
    -o /tmp/obscura.tar.gz && \
    tar xzf /tmp/obscura.tar.gz -C /usr/local/bin/ && \
    rm /tmp/obscura.tar.gz && \
    chmod +x /usr/local/bin/obscura && \
    echo '[INFO] Obscura headless browser installed'

# ===== CORE SECURITY TOOLS (apt available in Debian) =====
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    nmap masscan \
    sqlmap ffuf gobuster wapiti whatweb \
    hydra john hashcat medusa crunch cewl \
    binwalk foremost apktool \
    gdb gdbserver checksec socat ncat \
    steghide exiftool imagemagick p7zip-full \
    wireshark-common tshark \
    libpcap0.8-dev libsqlite3-dev \
    libnl-3-dev libnl-genl-3-dev libnl-route-3-dev ethtool \
    libjson-perl libxml-writer-perl

# radare2 — not in Debian bookworm, install from GitHub
RUN mkdir -p /opt/radare2 && \
    wget -q -O /tmp/radare2.deb \
    "https://github.com/radareorg/radare2/releases/download/5.9.8/radare2_5.9.8_amd64.deb" && \
    dpkg -i /tmp/radare2.deb 2>/dev/null || \
    (apt-get update && apt-get install -y -f --no-install-recommends) && \
    rm /tmp/radare2.deb

# ===== WORDLISTS (Seclists via git, rockyou via wget) =====
RUN git clone --depth 1 https://github.com/danielmiessler/SecLists /usr/share/seclists && \
    mkdir -p /usr/share/wordlists && \
    wget -q -O /usr/share/wordlists/rockyou.txt.gz \
    "https://github.com/praetorian-inc/Hob0Rules/raw/master/wordlists/rockyou.txt.gz" && \
    gunzip /usr/share/wordlists/rockyou.txt.gz && \
    mkdir -p /opt/opspectre/wordlists && \
    ln -sf /usr/share/wordlists /opt/opspectre/wordlists/wordlists && \
    ln -sf /usr/share/seclists /opt/opspectre/wordlists/seclists

# ===== TOOLS NOT IN DEBIAN REPOS =====
# nikto — Perl web server scanner
RUN git clone --depth 1 https://github.com/sullo/nikto /opt/nikto && \
    ln -s /opt/nikto/program/nikto.pl /usr/local/bin/nikto

# hash-identifier — identify hash types
RUN git clone --depth 1 https://gitlab.com/kalilinux/packages/hash-identifier /opt/hash-identifier && \
    ln -s /opt/hash-identifier/hash-id.py /usr/local/bin/hash-identifier

# wpscan — WordPress scanner (Ruby gem)
RUN gem install wpscan

# volatility3 — memory forensics (pip)
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install volatility3 --break-system-packages

# gdb-peda — Python Exploit Development Assistance for GDB
RUN git clone --depth 1 https://github.com/longld/peda /opt/peda && \
    echo "source /opt/peda/peda.py" >> /etc/skel/.gdbinit && \
    echo "source /opt/peda/peda.py" >> /root/.gdbinit

# ===== BURP SUITE =====
# ~150MB JAR from PortSwigger CDN. Use --progress + --timeout so it doesn't hang silently.
RUN mkdir -p /opt/burpsuite/{configs,extensions,payloads} && \
    wget --progress=dot:giga --timeout=60 \
    -O /opt/burpsuite/burpsuite_community.jar \
    "https://portswigger.net/burp/releases/download?product=community&version=2024.12.1&type=jar" || \
    echo "[WARN] Burp download failed (timeout or network issue) - will need manual install"

# ===== CERTIFICATES =====
RUN mkdir -p /app/certs && \
    openssl ecparam -name prime256v1 -genkey -noout -out /app/certs/ca.key && \
    openssl req -x509 -new -key /app/certs/ca.key \
    -out /app/certs/ca.crt -days 3650 \
    -subj "/C=US/ST=CA/O=Security Testing/CN=Testing Root CA" \
    -addext "basicConstraints=critical,CA:TRUE" \
    -addext "keyUsage=critical,digitalSignature,keyEncipherment,keyCertSign" && \
    openssl pkcs12 -export -out /app/certs/ca.p12 \
    -inkey /app/certs/ca.key -in /app/certs/ca.crt \
    -passout pass:"" -name "Testing Root CA" && \
    cp /app/certs/ca.crt /usr/local/share/ca-certificates/ca.crt && \
    update-ca-certificates

# ===== SECURITY SCANNERS (trivy, trufflehog, gitleaks) =====
RUN curl -sSfL https://raw.githubusercontent.com/trufflesecurity/trufflehog/main/scripts/install.sh | sh -s -- -b /usr/local/bin

RUN set -eux; \
    ARCH="$(uname -m)"; \
    case "$ARCH" in \
        x86_64) GITLEAKS_ARCH="x64" ;; \
        aarch64|arm64) GITLEAKS_ARCH="arm64" ;; \
        *) echo "Unsupported architecture: $ARCH" >&2; exit 1 ;; \
    esac; \
    TAG="$(curl -fsSL https://api.github.com/repos/gitleaks/gitleaks/releases/latest | jq -r .tag_name)"; \
    curl -fsSL "https://github.com/gitleaks/gitleaks/releases/download/${TAG}/gitleaks_${TAG#v}_linux_${GITLEAKS_ARCH}.tar.gz" -o /tmp/gitleaks.tgz; \
    tar -xzf /tmp/gitleaks.tgz -C /tmp; \
    install -m 0755 /tmp/gitleaks /usr/local/bin/gitleaks; \
    rm -f /tmp/gitleaks /tmp/gitleaks.tgz

RUN curl -sfL https://raw.githubusercontent.com/aquasecurity/trivy/main/contrib/install.sh | sh -s -- -b /usr/local/bin

# ===== CAIDO CLI =====
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        CAIDO_ARCH="x86_64"; \
    elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then \
        CAIDO_ARCH="aarch64"; \
    else \
        echo "Unsupported architecture: $ARCH" && exit 1; \
    fi && \
    wget -q -O /tmp/caido-cli.tar.gz https://caido.download/releases/v0.48.0/caido-cli-v0.48.0-linux-${CAIDO_ARCH}.tar.gz && \
    tar -xzf /tmp/caido-cli.tar.gz -C /tmp && \
    chmod +x /tmp/caido-cli && \
    mv /tmp/caido-cli /usr/local/bin/ && \
    rm -f /tmp/caido-cli.tar.gz

# ===== UV =====
RUN curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh

# nmap capabilities handled via docker cap_add (NET_RAW) — file cap_setcap removed
# because no-new-privileges:true prevents file-based capabilities from being honored.

# ===== GO RUNTIME (direct binary — apt's golang-go is Go 1.19, tools need 1.21+) =====
RUN ARCH=$(uname -m) && \
    case "$ARCH" in \
        x86_64) GO_ARCH="amd64" ;; \
        aarch64|arm64) GO_ARCH="arm64" ;; \
        *) echo "Unsupported architecture: $ARCH" && exit 1 ;; \
    esac && \
    wget -q -O /tmp/go.tar.gz "https://go.dev/dl/go1.22.10.linux-${GO_ARCH}.tar.gz" && \
    rm -rf /usr/local/go && \
    tar -C /usr/local -xzf /tmp/go.tar.gz && \
    rm /tmp/go.tar.gz && \
    ln -sf /usr/local/go/bin/go /usr/local/bin/go && \
    ln -sf /usr/local/go/bin/gofmt /usr/local/bin/gofmt

ENV GOPATH="/root/go"
ENV PATH="/root/go/bin:/usr/local/go/bin:/root/.local/bin:/root/.npm-global/bin:$PATH"

# ===== GO TOOLS (with module + build cache) =====
RUN --mount=type=cache,target=/root/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@v1.6.9 && \
    go install -v github.com/projectdiscovery/katana/cmd/katana@v1.1.1 && \
    go install -v github.com/jaeles-project/gospider@v1.1.6 && \
    go install -v github.com/lc/gau/v2/cmd/gau@latest && \
    go install -v github.com/tomnomnom/waybackurls@latest && \
    go install -v github.com/sensepost/gowitness@latest && \
    go install -v github.com/haccer/subjack@latest && \
    go install -v github.com/hahwul/dalfox/v2@latest && \
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest && \
    go install -v github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest && \
    go install -v github.com/projectdiscovery/naabu/v2/cmd/naabu@latest && \
    go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@v1.2.0

# ===== PYTHON TOOLS (pipx with cache) =====
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.local/pipx \
    pipx install arjun && \
    pipx install wafw00f && \
    pipx install semgrep && \
    pipx install bandit && \
    pipx install webtech && \
    pipx install pwntools && \
    pipx install z3-solver && \
    echo '[INFO] pipx tools installed'

# ===== CTF PYTHON VENV =====
RUN python3 -m venv /opt/ctf-python-venv && \
    . /opt/ctf-python-venv/bin/activate && \
    pip install pycryptodome gmpy2 requests Pillow sympy && \
    echo '[INFO] CTF Python venv ready (pycryptodome, gmpy2, requests, Pillow, sympy)'

# ===== CTF TOOLS =====
# stegseek — download .deb from RickdeJager/stegseek (C++ tool, not Go)
RUN wget -q https://github.com/RickdeJager/stegseek/releases/download/v0.6/stegseek_0.6-1.deb -O /tmp/stegseek.deb && \
    dpkg -i /tmp/stegseek.deb 2>/dev/null && \
    rm /tmp/stegseek.deb || \
    { echo '[WARN] stegseek dpkg failed - trying apt deps'; \
      apt-get install -y -f && rm /tmp/stegseek.deb; }

# zsteg — PNG LSB steganalysis (Ruby gem)
RUN gem install zsteg 2>/dev/null || echo '[INFO] zsteg gem install skipped'

# CFR Java Decompiler
RUN wget -q -O /opt/opspectre/tools/cfr.jar \
    "https://github.com/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar" 2>/dev/null || \
    echo '[INFO] CFR decompiler download failed'

# ===== CUSTOM TOOLS (with git clone cache) =====
RUN mkdir -p /opt/opspectre/tools /tmp/git-clones
WORKDIR /opt/opspectre/tools
RUN --mount=type=cache,target=/tmp/git-clones \
    set -eux; \
    for repo in \
        "https://github.com/aravind0x7/JS-Snooper.git" \
        "https://github.com/xchopath/jsniper.sh.git" \
        "https://github.com/ticarpi/jwt_tool.git" \
        "https://github.com/RsaCtfTool/RsaCtfTool.git"; do \
        name=$(basename "$repo" .git); \
        if [ ! -d "$name" ]; then \
            git clone "$repo"; \
        fi; \
    done && \
    chmod +x JS-Snooper/js_snooper.sh jsniper.sh/jsniper.sh jwt_tool/jwt_tool.py && \
    chmod +x RsaCtfTool/RsaCtfTool.py 2>/dev/null || true

# ===== EXPLOIT-DB / SEARCHSPLOIT (standalone from git) =====
RUN git clone --depth 1 https://gitlab.com/exploit-database/exploitdb /opt/exploitdb && \
    ln -s /opt/exploitdb/searchsploit /usr/local/bin/searchsploit

# ===== NUCLEI TEMPLATES =====
RUN --mount=type=cache,target=/root/nuclei-templates \
    nuclei -ut 2>/dev/null || echo '[INFO] Nuclei templates will download on first run'

# ===== USER-AGENT WORDLIST =====
RUN wget -qO /opt/opspectre/wordlists/user-agents.txt \
    'https://raw.githubusercontent.com/torden/go-random-user-agent/master/data/list.txt' || \
    curl -sL 'https://raw.githubusercontent.com/torden/go-random-user-agent/master/data/list.txt' \
    -o /opt/opspectre/wordlists/user-agents.txt || \
    printf 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n' \
    > /opt/opspectre/wordlists/user-agents.txt

# ===== NPM PACKAGES =====
ENV NPM_CONFIG_PREFIX=/root/.npm-global
RUN --mount=type=cache,target=/root/.npm \
    mkdir -p /root/.npm-global && \
    npm install -g retire eslint js-beautify jshint

# ===== PANDOC + LATEX (reports) =====
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    pandoc texlive-latex-base texlive-latex-recommended \
    texlive-latex-extra texlive-fonts-recommended \
    lmodern texinfo && \
    apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# ===== PLAYBOOKS =====
COPY containers/scan-helpers.sh /opt/playbooks/scan-helpers.sh
COPY containers/burpsuite-playbook.sh /opt/playbooks/burpsuite-playbook.sh
COPY containers/burpsuite-agent.sh /usr/local/bin/burpsuite-agent
COPY containers/owasp-top10-playbook.sh /opt/playbooks/owasp-top10-playbook.sh
COPY containers/osint-playbook.sh /opt/playbooks/osint-playbook.sh
COPY containers/rate-limit-helpers.sh /opt/playbooks/rate-limit-helpers.sh
COPY containers/ctf-playbook.sh /opt/playbooks/ctf-playbook.sh
RUN chmod +x /opt/playbooks/*.sh /usr/local/bin/burpsuite-agent && \
    for f in /opt/playbooks/*.sh; do \
        echo "source $f" >> /etc/bash.bashrc; \
        echo "source $f" >> /root/.bashrc; \
    done

# ===== TOOL WRAPPERS =====
COPY containers/wrappers/ /usr/local/bin/
RUN chmod +x /usr/local/bin/*-run

# ===== APPLICATION CODE (MOST VOLATILE — LAST) =====
WORKDIR /opt/opspectre/tools
COPY pyproject.toml uv.lock ./
COPY src/opspectre/ opspectre/

RUN uv sync --frozen --no-dev --extra sandbox
# playwright-core is bundled as a dependency of playwright>=1.40.0 (CDP mode — connects to Obscura, no Chromium download needed)

RUN uv pip install -r /opt/opspectre/tools/jwt_tool/requirements.txt && \
    ln -s /opt/opspectre/tools/jwt_tool/jwt_tool.py /usr/local/bin/jwt_tool

# ===== DIRECTORY LAYOUT =====
RUN mkdir -p /opt/opspectre/{configs,output,scripts,tools,wordlists} \
             /opt/playbooks \
             /app/runtime /app/tools /app/certs \
             /workspace/output/{loot,sessions,logs,scans,exploits,reports,recon,osint,web-audit,wordpress,container-audit,secrets,nmap,burp-projects,compliance,scan_runs}

# ===== ENVIRONMENT =====
ENV VIRTUAL_ENV="/opt/opspectre/tools/.venv"
ENV OPSPECTRE_SANDBOX_MODE=true
ENV PYTHONPATH=/opt/opspectre/tools
ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV DISPLAY=:99

# ===== CREATE PENTESTER USER =====
RUN useradd -m -s /bin/bash pentester && \
    usermod -aG sudo pentester && \
    echo "pentester ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers && \
    touch /home/pentester/.hushlogin

# ===== CLEANUP =====
RUN apt-get autoremove -y && \
    apt-get autoclean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# ===== OWNERSHIP =====
RUN chown -R pentester:pentester /opt/opspectre /home/pentester /workspace

# ===== ENTRYPOINT =====
COPY containers/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

WORKDIR /workspace
ENTRYPOINT ["docker-entrypoint.sh"]
