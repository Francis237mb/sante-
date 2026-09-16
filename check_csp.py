import urllib.request

servers = [
    "https://meet.jit.si",
    "https://jitsi.riot.im",
    "https://meet.guifi.net",
    "https://jitsi.linux.it",
    "https://meet.hostsharing.net",
    "https://meet.mayfirst.org",
    "https://meet.infra.run",
    "https://framatalk.org"
]

print("Checking Content-Security-Policy for Jitsi servers...")
for server in servers:
    try:
        req = urllib.request.Request(server, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=5) as response:
            csp = response.headers.get('Content-Security-Policy', '')
            if 'frame-ancestors' in csp.lower():
                print(f"[BLOCKED] {server} - has frame-ancestors: {csp[:50]}...")
            else:
                print(f"[OK] {server} - NO frame-ancestors block!")
    except Exception as e:
        print(f"[ERROR] {server} - {e}")
