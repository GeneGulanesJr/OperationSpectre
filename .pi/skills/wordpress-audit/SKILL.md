---
name: wordpress-audit
description: Specialized WordPress security audit using wpscan, wpbullet, and targeted enumeration in the opspectre sandbox. Use when the target is running WordPress.
---

# WordPress Security Audit

Comprehensive WordPress-specific security testing. Auto-detects WordPress sites and runs targeted enumeration, vulnerability scanning, and plugin/theme analysis.

## Prerequisites

- OperationSpectre sandbox running (`opspectre sandbox start`)
- Target running WordPress (detect with `whatweb` or check for `wp-content`, `wp-login`)
- wpscan installed (available in container)

## WordPress Detection

### Quick Check
```bash
opspectre shell "curl -s https://<TARGET>/ | grep -i 'wp-content\\|wp-includes\\|wordpress'"
```

### WhatWeb Detection
```bash
opspectre shell "whatweb https://<TARGET>"
```

### HTTP Header Check
```bash
opspectre shell "curl -sI https://<TARGET>/ | grep -i 'x-generator\\|link.*wp-json\\|wp-content'"
```

## Phase 1: WPScan Enumeration

### Full Enumeration (Users, Plugins, Themes)
```bash
opspectre shell "wpscan --url https://<TARGET> --enumerate u,vp,vt,dbe,cb,dbe --random-user-agent --disable-tls-checks -o /workspace/output/wordpress/wpscan-full.txt 2>&1"
```

### Enum Flags Reference
| Flag | What It Enumerates |
|------|-------------------|
| `u` | User accounts (from author archives, posts, etc.) |
| `vp` | Vulnerable plugins |
| `vt` | Vulnerable themes |
| `dbe` | Database exports |
| `cb` | Config backups |
| `dbe` | Db exports |
| `d` | Timthumbs |
| `ap` | All plugins |
| `at` | All themes |
| `p` | Popular plugins (top 100) |

### Users Only (Fast)
```bash
opspectre shell "wpscan --url https://<TARGET> --enumerate u --random-user-agent --disable-tls-checks -o /workspace/output/wordpress/wpscan-users.txt"
```

### Vulnerable Plugins/Themes Only
```bash
opspectre shell "wpscan --url https://<TARGET> --enumerate vp,vt --random-user-agent --disable-tls-checks -o /workspace/output/wordpress/wpscan-vulns.txt"
```

### With API Token (for unlimited vulnerability lookups)
```bash
opspectre shell "wpscan --url https://<TARGET> --api-token <WPSCAN_API_TOKEN> --enumerate vp,vt -o /workspace/output/wordpress/wpscan-api.txt"
```

### With Authentication (for deeper scanning)
```bash
opspectre shell "wpscan --url https://<TARGET> --passwords /usr/share/seclists/Passwords/Common-Credentials/10k-most-common.txt --usernames admin --random-user-agent -o /workspace/output/wordpress/wpscan-brute.txt"
```

## Phase 2: WordPress REST API Enumeration

### Check WP REST API
```bash
opspectre shell "curl -s https://<TARGET>/wp-json/wp/v2/users | python3 -m json.tool > /workspace/output/wordpress/wp-rest-users.txt"
```

### Check REST API Discovery
```bash
opspectre shell "curl -s https://<TARGET>/wp-json/ | python3 -m json.tool > /workspace/output/wordpress/wp-rest-api.txt"
```

### Check for Disabled REST API
```bash
opspectre shell "curl -sI https://<TARGET>/wp-json/wp/v2/users | head -1"
```

## Phase 3: WordPress Specific Files

### Check for Sensitive Files
```bash
opspectre shell "for path in wp-config.php.bak wp-config.php.save wp-config.php~ .wp-config.php.swp wp-config.php.old wp-config.php.dist readme.html license.txt wp-login.php xmlrpc.php wp-cron.php; do
  code=\$(curl -s -o /dev/null -w '%{http_code}' \"https://<TARGET>/\$path\")
  [ \"\$code\" != \"404\" ] && echo \"FOUND: \$path (\$code)\"
done > /workspace/output/wordpress/wp-sensitive-files.txt"
```

### Check for Backup Files
```bash
opspectre shell "for ext in .bak .old .save .zip .tar.gz .sql .log .txt ~ .swp; do
  code=\$(curl -s -o /dev/null -w '%{http_code}' \"https://<TARGET>/wp-config.php\$ext\")
  [ \"\$code\" != \"404\" ] && echo \"FOUND: wp-config.php\$ext (\$code)\"
done >> /workspace/output/wordpress/wp-sensitive-files.txt"
```

### Check wp-content/uploads
```bash
opspectre shell "curl -s https://<TARGET>/wp-content/uploads/ | head -50 > /workspace/output/wordpress/wp-uploads.txt"
```

## Phase 4: XML-RPC

### Check XML-RPC Enabled
```bash
opspectre shell "curl -s https://<TARGET>/xmlrpc.php -d '<?xml version=\"1.0\"?><methodCall><methodName>system.listMethods</methodName></methodCall>' | grep -oP '<name>\K[^<]+' > /workspace/output/wordpress/xmlrpc-methods.txt"
```

### XML-RPC Brute Force Check
```bash
opspectre shell "curl -s -o /dev/null -w '%{http_code}' https://<TARGET>/xmlrpc.php -d '<?xml version=\"1.0\"?><methodCall><methodName>wp.getUsersBlogs</methodName><params><param><value><string>admin</string></value></param><param><value><string>wrong</string></value></param></params></methodCall>'"
```

## Phase 5: Directory Discovery (WordPress-Specific Wordlists)

### wp-content Plugins
```bash
opspectre shell "gobuster dir -u https://<TARGET>/wp-content/plugins/ -w /usr/share/seclists/Discovery/Web-Content/wp-plugins.txt -o /workspace/output/wordpress/wp-plugins.txt -t 15 -q --delay 1s --random-agent"
```

### wp-content Themes
```bash
opspectre shell "gobuster dir -u https://<TARGET>/wp-content/themes/ -w /usr/share/seclists/Discovery/Web-Content/wp-themes.txt -o /workspace/output/wordpress/wp-themes.txt -t 15 -q --delay 1s --random-agent"
```

### WordPress General
```bash
opspectre shell "gobuster dir -u https://<TARGET>/ -w /usr/share/seclists/Discovery/Web-Content/wordpress.txt -o /workspace/output/wordpress/wp-dirs.txt -t 15 -q --delay 1s --random-agent"
```

## Phase 6: User Enumeration

### Author Archives (passive)
```bash
opspectre shell "for i in \$(seq 1 20); do
  resp=\$(curl -sI \"https://<TARGET>/?author=\$i\" | grep Location)
  [ -n \"\$resp\" ] && echo \"Author \$i: \$resp\"
done > /workspace/output/wordpress/wp-author-enum.txt"
```

### WPScan User Enumeration
```bash
opspectre shell "wpscan --url https://<TARGET> --enumerate u --random-user-agent -o /workspace/output/wordpress/wpscan-users.txt"
```

## Phase 7: Login & Authentication Testing

### Check Login Page
```bash
opspectre shell "curl -sI https://<TARGET>/wp-login.php > /workspace/output/wordpress/wp-login-headers.txt"
```

### Check Rate Limiting on Login
```bash
opspectre shell "for i in \$(seq 1 15); do
  code=\$(curl -s -o /dev/null -w '%{http_code}' -X POST https://<TARGET>/wp-login.php -d 'log=admin&pwd=wrong\$i&wp-submit=Login')
  echo \"Attempt \$i: \$code\"
done > /workspace/output/wordpress/wp-rate-limit-test.txt"
```

### Check for Two-Factor / Login Protection Plugins
```bash
opspectre shell "curl -s https://<TARGET>/wp-content/plugins/ | grep -iE 'two-factor|login-security|brute-force|limit-login' > /workspace/output/wordpress/wp-security-plugins.txt"
```

## Phase 8: WordPress Version Vulnerability Check

### Get Exact Version
```bash
opspectre shell "wpscan --url https://<TARGET> --random-user-agent 2>&1 | grep -i 'wordpress version'"
```

### Check via Readme
```bash
opspectre shell "curl -s https://<TARGET>/readme.html | grep -oP 'Version \\K[0-9.]+' | head -1"
```

## Output Locations

All results saved under `/workspace/output/wordpress/`:
- `wpscan-full.txt` / `wpscan-users.txt` / `wpscan-vulns.txt` — WPScan results
- `wp-rest-users.txt` / `wp-rest-api.txt` — REST API data
- `wp-sensitive-files.txt` — exposed config/backup files
- `wp-uploads.txt` — uploads directory listing
- `xmlrpc-methods.txt` — XML-RPC available methods
- `wp-plugins.txt` / `wp-themes.txt` / `wp-dirs.txt` — directory discovery
- `wp-author-enum.txt` — enumerated users
- `wp-login-headers.txt` — login page analysis
- `wp-rate-limit-test.txt` — rate limiting test
- `wp-security-plugins.txt` — detected security plugins

## Quick Full WordPress Audit

```bash
opspectre run "mkdir -p /workspace/output/wordpress && \
  wpscan --url https://<TARGET> --enumerate u,vp,vt,cb --random-user-agent --disable-tls-checks -o /workspace/output/wordpress/wpscan-full.txt && \
  curl -s https://<TARGET>/wp-json/wp/v2/users | python3 -m json.tool > /workspace/output/wordpress/wp-rest-users.txt && \
  curl -s https://<TARGET>/xmlrpc.php -d '<?xml version=\"1.0\"?><methodCall><methodName>system.listMethods</methodName></methodCall>' | grep -oP '<name>\\K[^<]+' > /workspace/output/wordpress/xmlrpc-methods.txt && \
  gobuster dir -u https://<TARGET>/wp-content/plugins/ -w /usr/share/seclists/Discovery/Web-Content/wp-plugins.txt -o /workspace/output/wordpress/wp-plugins.txt -t 15 -q --delay 1s --random-agent"
```

## Tips

- Replace `<TARGET>` with the actual URL (e.g., `https://example.com`)
- `--random-user-agent` is critical — some WAFs block default WPScan UA
- `--disable-tls-checks` helps with self-signed or mismatched certs
- Use `--api-token` with a WPScan API token for full vulnerability database access
- Check `wp-security-plugins.txt` before attempting brute force — some plugins block it
- XML-RPC can be abused for amplification DDoS even if login is rate-limited
- REST API user enumeration works even if author archives are disabled
- Always check wp-config.php backups — they may contain DB credentials
- Chain with the web-app-audit skill for full OWASP Top 10 coverage on top of WordPress-specific checks
