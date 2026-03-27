# Merge into ~/.jupyter/jupyter_lab_config.py (create file if missing).
# Then restart Jupyter Lab. Fixes 403 / blocked websocket when using Cloudflare Tunnel.

c = get_config()

c.ServerApp.allow_remote_access = True
c.ServerApp.trust_xheaders = True
c.ServerApp.allow_origin = "https://lab.nishtha.rocks"

# If you still see 403, uncomment:
# c.ServerApp.local_hostnames = ["lab.nishtha.rocks", "localhost", "127.0.0.1"]
