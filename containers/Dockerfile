# syntax=docker/dockerfile:1
# =========================================================================
# Dockerfile — App layer on top of opspectre-base
#
# This is the fast-rebuild layer. All the heavy Kali packages, wordlists,
# metasploit, certificates, and security tools live in opspectre-base.
# Changes to playbooks, Go/Python/npm tools, wrappers, and app code
# rebuild here in ~2-5 minutes instead of 15-30.
#
# Usage:
#   docker build -f containers/Dockerfile -t opspectre-full:latest .
# =========================================================================

FROM opspectre-base:latest

LABEL description="OPERATIONSPECTRE - App layer (playbooks, tools, wrappers, app code)"

# ===== PLAYBOOKS =====
COPY containers/scan-helpers.sh /opt/playbooks/scan-helpers.sh
COPY containers/burpsuite-playbook.sh /opt/playbooks/burpsuite-playbook.sh
COPY containers/burpsuite-agent.sh /usr/local/bin/burpsuite-agent
COPY containers/owasp-top10-playbook.sh /opt/playbooks/owasp-top10-playbook.sh
COPY containers/osint-playbook.sh /opt/playbooks/osint-playbook.sh
COPY containers/rate-limit-helpers.sh /opt/playbooks/rate-limit-helpers.sh
COPY containers/ctf-playbook.sh /opt/playbooks/ctf-playbook.sh
RUN chmod +x /opt/playbooks/scan-helpers.sh /opt/playbooks/burpsuite-playbook.sh /usr/local/bin/burpsuite-agent \
             /opt/playbooks/owasp-top10-playbook.sh /opt/playbooks/osint-playbook.sh \
             /opt/playbooks/rate-limit-helpers.sh /opt/playbooks/ctf-playbook.sh && \
    echo 'source /opt/playbooks/burpsuite-playbook.sh' >> /root/.bashrc && \
    echo 'source /opt/playbooks/burpsuite-playbook.sh' >> /etc/bash.bashrc && \
    echo 'source /opt/playbooks/owasp-top10-playbook.sh' >> /root/.bashrc && \
    echo 'source /opt/playbooks/owasp-top10-playbook.sh' >> /etc/bash.bashrc && \
    echo 'source /opt/playbooks/osint-playbook.sh' >> /root/.bashrc && \
    echo 'source /opt/playbooks/osint-playbook.sh' >> /etc/bash.bashrc && \
    echo 'source /opt/playbooks/rate-limit-helpers.sh' >> /root/.bashrc && \
    echo 'source /opt/playbooks/rate-limit-helpers.sh' >> /etc/bash.bashrc && \
    echo 'source /opt/playbooks/ctf-playbook.sh' >> /root/.bashrc && \
    echo 'source /opt/playbooks/ctf-playbook.sh' >> /etc/bash.bashrc

# ===== PYTHON TOOLS (pipx with cache) =====
ENV PATH="/root/.local/bin:$PATH"
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.local/pipx \
    pipx install arjun && \
    pipx install wafw00f && \
    pipx install semgrep && \
    pipx install bandit && \
    pipx install webtech && \
    echo '[INFO] dirsearch skipped (Python 3.13 pkg_resources removed); use gobuster/ffuf'

# ===== CTF PYTHON TOOLS (pipx with cache) =====
RUN --mount=type=cache,target=/root/.cache/pip \
    --mount=type=cache,target=/root/.local/pipx \
    python3 -m venv /opt/ctf-python-venv && \
    . /opt/ctf-python-venv/bin/activate && \
    pip install pycryptodome gmpy2 requests Pillow sympy && \
    pipx install pwntools && \
    pipx install z3-solver && \
    echo '[INFO] CTF Python tools installed (pwntools, z3-solver, pycryptodome, gmpy2, sympy)'

# ===== GO TOOLS (with module + build cache) =====
WORKDIR /tmp
ENV GOPATH="/root/go"
RUN --mount=type=cache,target=/root/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go install -v github.com/projectdiscovery/httpx/cmd/httpx@v1.6.9 && \
    go install -v github.com/projectdiscovery/katana/cmd/katana@v1.1.1 && \
    go install -v github.com/projectdiscovery/vulnx/v2/cmd/vulnx@v2.0.1 && \
    go install -v github.com/jaeles-project/gospider@v1.1.6 && \
    go install -v github.com/projectdiscovery/interactsh/cmd/interactsh-client@v1.2.0 && \
    go install -v github.com/lc/gau/v2/cmd/gau@latest && \
    go install -v github.com/tomnomnom/waybackurls@latest && \
    go install -v github.com/sensepost/gowitness@latest && \
    go install -v github.com/haccer/subjack@latest && \
    go install -v github.com/hahwul/dalfox/v2@latest && \
    go install -v github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest

# ===== CTF GO TOOLS (stegseek) =====
RUN --mount=type=cache,target=/root/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    go install -v github.com/raehik/stegseek@latest || { \
    echo '[WARN] stegseek Go install failed - falling back to binary download' && \
    cd /tmp && \
    curl -L -s https://github.com/raehik/stegseek/releases/latest/download/stegseek-linux-amd64 -o stegseek || \
    wget -q https://github.com/raehik/stegseek/releases/latest/download/stegseek-linux-amd64 -O stegseek || \
    { echo '[ERROR] Failed to download stegseek binary' && exit 1; } && \
    mv stegseek /usr/local/bin/stegseek && \
    chmod +x /usr/local/bin/stegseek && \
    echo '[INFO] stegseek installed via binary fallback'; }

# ===== CTF Ruby tool (zsteg for PNG LSB analysis) =====
RUN gem install zsteg 2>/dev/null || echo '[INFO] zsteg gem install skipped'

# ===== NUCLEI TEMPLATES (with cache) =====
# NOTE: nuclei v3.x uses -ut for template update (dropped -update-templates flag)
RUN --mount=type=cache,target=/root/nuclei-templates \
    nuclei -ut 2>/dev/null || echo '[INFO] Nuclei templates update skipped (will download on first run)'

# ===== USER-AGENT ROTATION WORDLIST =====
RUN mkdir -p /opt/opspectre/wordlists && \
    (wget -qO /opt/opspectre/wordlists/user-agents.txt \
    'https://raw.githubusercontent.com/torden/go-random-user-agent/master/data/list.txt' || \
    curl -sL 'https://raw.githubusercontent.com/torden/go-random-user-agent/master/data/list.txt' \
    -o /opt/opspectre/wordlists/user-agents.txt || \
    printf 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36\n' \
    > /opt/opspectre/wordlists/user-agents.txt) && \
    echo '[INFO] User-agent wordlist ready'

# ===== CHROMIUM (headless browser for gowitness, playwright, visual recon) =====
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends chromium chromium-driver && \
    apt-get autoremove -y && rm -rf /var/lib/apt/lists/* && \
    ln -sf /usr/bin/chromium /usr/bin/google-chrome 2>/dev/null || true && \
    echo '[INFO] Chromium installed for gowitness / headless browser automation'

# ===== PROXYCHAINS CONFIGURATION =====
RUN mkdir -p /etc/proxychains && \
    printf 'strict_chain\nproxy_dns\ntcp_read_time_out 15000\ntcp_connect_time_out 8000\n[ProxyList]\n# socks5 127.0.0.1 9050\n# http 10.10.10.10 8080\n' \
    > /etc/proxychains/proxychains.conf && \
    echo '[INFO] Proxychains config ready'

# ===== PANDOC + LaTeX (PDF report generation) =====
RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
    pandoc texlive-latex-base texlive-latex-recommended \
    texlive-latex-extra texlive-fonts-recommended \
    lmodern texinfo && \
    apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# ===== NPM PACKAGES (with cache) =====
ENV NPM_CONFIG_PREFIX=/root/.npm-global
RUN --mount=type=cache,target=/root/.npm \
    mkdir -p /root/.npm-global && \
    npm install -g retire eslint js-beautify @ast-grep/cli tree-sitter-cli jshint

# ===== TREE-SITTER PARSERS =====
RUN --mount=type=cache,target=/tmp/ts-parsers \
    set -eux; \
    TS_PARSER_DIR="/root/.tree-sitter/parsers"; \
    mkdir -p "${TS_PARSER_DIR}"; \
    for repo in tree-sitter-java tree-sitter-javascript tree-sitter-python tree-sitter-go tree-sitter-bash tree-sitter-json tree-sitter-yaml tree-sitter-typescript; do \
        if [ "$repo" = "tree-sitter-yaml" ]; then \
            repo_url="https://github.com/tree-sitter-grammars/${repo}.git"; \
        else \
            repo_url="https://github.com/tree-sitter/${repo}.git"; \
        fi; \
        git clone --depth 1 "${repo_url}" "${TS_PARSER_DIR}/${repo}" 2>/dev/null || true; \
    done

# ===== CUSTOM TOOLS (with git clone cache) =====
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
            git clone --reference-if-able /tmp/git-clones/"$name" --dissociate "$repo"; \
        fi; \
        if [ -d /tmp/git-clones/"$name" ]; then \
            cp -a /tmp/git-clones/"$name"/.git "$name/" 2>/dev/null || true; \
        fi; \
    done && \
    chmod +x JS-Snooper/js_snooper.sh jsniper.sh/jsniper.sh jwt_tool/jwt_tool.py && \
    [ -f RsaCtfTool/RsaCtfTool.py ] && chmod +x RsaCtfTool/RsaCtfTool.py 2>/dev/null || true && \
    mkdir -p /tmp/git-clones && \
    for d in JS-Snooper jsniper.sh jwt_tool RsaCtfTool; do \
        cp -a "$d" /tmp/git-clones/ 2>/dev/null || true; \
    done

# ===== CTF TOOL: CFR Java Decompiler =====
RUN wget -q -O /opt/opspectre/tools/cfr.jar \
    "https://github.com/leibnitz27/cfr/releases/download/0.152/cfr-0.152.jar" 2>/dev/null || \
    echo '[INFO] CFR decompiler download failed - will try on next build'

# ===== TOOL WRAPPERS =====
COPY containers/wrappers/ /usr/local/bin/
RUN chmod +x /usr/local/bin/msf-run /usr/local/bin/hydra-run /usr/local/bin/hashcat-run \
             /usr/local/bin/john-run /usr/local/bin/aircrack-run /usr/local/bin/responder-run \
             /usr/local/bin/cme-run /usr/local/bin/evil-winrm-run \
             /usr/local/bin/pwn-run /usr/local/bin/vol-run /usr/local/bin/steg-run \
             /usr/local/bin/z3-run

# ===== APPLICATION CODE (MOST VOLATILE — LAST) =====
WORKDIR /opt/opspectre/tools
COPY pyproject.toml uv.lock ./
COPY opspectre/ opspectre/

RUN uv sync --frozen --no-dev --extra sandbox
RUN .venv/bin/python -m playwright install chromium

RUN uv pip install -r /opt/opspectre/tools/jwt_tool/requirements.txt && \
    ln -s /opt/opspectre/tools/jwt_tool/jwt_tool.py /usr/local/bin/jwt_tool

# ===== OWNERSHIP =====
RUN chown -R pentester:pentester /opt/opspectre /home/pentester /workspace

# ===== FINAL SETUP =====
COPY containers/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

WORKDIR /workspace

ENTRYPOINT ["docker-entrypoint.sh"]
