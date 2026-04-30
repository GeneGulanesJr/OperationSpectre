# Burp Suite Verification Checklist

## ✅ What's Covered

### Architecture Integration

# Manual Burp Suite usage
opspectre shell "burpsuite --headless --project-file=/workspace/scans/burp.project"
opspectre shell "curl -x localhost:8080 https://target.com"
```
- [x] Brute force setup guide
- [x] Payload directory structure

### 5. Decoder & Utilities
- [x] Base64 encode/decode
- [x] URL encode/decode
- [x] HTML encode/decode
- [x] Hex encode/decode
- [x] MD5, SHA1, SHA256 hashing
- [x] JWT decoder

### 6. Scope & Target Configuration
- [x] Set scope from URL
- [x] Generate scope regex
- [x] Multi-target scope
- [x] Filter proxy history

### 7. Search & Analysis
- [x] Search proxy history
- [x] Find sensitive data patterns
- [x] API key patterns
- [x] Credential patterns
- [x] Token patterns
- [x] Internal network patterns

### 8. CA Certificate for HTTPS
- [x] Download Burp CA cert guide
- [x] System CA installation
- [x] curl integration
- [x] Python requests integration

### 9. Extension Management
- [x] Extensions directory
- [x] List installed extensions
- [x] Install extensions (manual)
- [x] Load via CLI flag

### 10. Chain with Other Tools
- [x] nmap integration
- [x] nuclei integration
- [x] Web port discovery

### 11. Agent Wrapper (Simple Commands)
- [x] `burpsuite-agent start`
- [x] `burpsuite-agent stop`
- [x] `burpsuite-agent status`
- [x] `burpsuite-agent scan <url>`
- [x] `burpsuite-agent spider <url>`
- [x] `burpsuite-agent proxy <url>`
- [x] `burpsuite-agent intruder setup`
- [x] `burpsuite-agent intruder brute`
- [x] `burpsuite-agent decode <type> <data>`
- [x] `burpsuite-agent scope <url>`
- [x] `burpsuite-agent secrets`
- [x] `burpsuite-agent ca-cert`
- [x] `burpsuite-agent help`

### 12. Playbook Functions
- [x] burp_headless
- [x] burp_gui
- [x] burp_stop
- [x] burp_status
- [x] burp_passive_scan
- [x] burp_active_scan
- [x] burp_spider
- [x] burp_proxy_url
- [x] burp_chain_nmap
- [x] burp_chain_nuclei
- [x] burp_generate_config
- [x] burp_generate_aggressive_config
- [x] burp_setup_intruder
- [x] burp_intruder_config
- [x] burp_brute_force
- [x] burp_set_scope
- [x] burp_set_multi_scope
- [x] burp_decode
- [x] burp_decode_jwt
- [x] burp_search
- [x] burp_find_secrets
- [x] burp_install_ca
- [x] burp_list_extensions
- [x] burp_install_extension
- [x] burp_export_report
- [x] burp_debug
- [x] burp_fix
- [x] burp_help

### 13. File Locations
- [x] Burp JAR: /opt/burpsuite/burpsuite_community.jar
- [x] Configs: /opt/burpsuite/configs/
- [x] Payloads: /opt/burpsuite/payloads/
- [x] Extensions: /opt/burpsuite/extensions/
- [x] Projects: /workspace/output/burp-projects/
- [x] Reports: /workspace/output/reports/
- [x] Playbook: /opt/playbooks/burpsuite-playbook.sh
- [x] Agent wrapper: /usr/local/bin/burpsuite-agent

### 14. Auto-Loading
- [x] Playbook loads on shell login (.bashrc)
- [x] Playbook loads system-wide (/etc/bash.bashrc)
- [x] Agent wrapper in PATH
- [x] Aliases defined

## ❌ What's NOT Covered (Community Edition Limitations)

### Professional Edition Only
- [ ] REST API automation (requires Pro)
- [ ] Automated scanning via API (requires Pro)
- [ ] Collaborator server (requires Pro)
- [ ] Some advanced scanning options (requires Pro)

### GUI-Only Features (Manual Use)
- [ ] Sequencer (token randomness - GUI only)
- [ ] Comparer (response comparison - GUI only)
- [ ] Some extension interactions (GUI only)

## 🔧 How to Verify in Container

```bash
# Start container
docker exec -it opspectre-full bash

# Check playbook loaded
burphelp

# Check agent wrapper
burpsuite-agent help

# Check payloads
ls -la /opt/burpsuite/payloads/

# Check configs
ls -la /opt/burpsuite/configs/

# Test decode
burpsuite-agent decode base64-e "hello world"

# Test scope
burpsuite-agent scope https://example.com

# Test intruder setup
burpsuite-agent intruder setup
```

## 📋 Summary

**COVERED**: All essential Burp Suite Community Edition features for automated/headless use by AI agents.

**NOT COVERED**: Professional Edition API features and some GUI-only tools that require manual interaction.

**READY FOR**: Any AI agent to immediately use Burp Suite for:
- Web application scanning
- Proxy traffic interception
- Payload attacks (Intruder)
- Data encoding/decoding
- Scope configuration
- Sensitive data discovery

**AGENT ACCESS**: Via `burpsuite-agent` command or `burp_*` functions.