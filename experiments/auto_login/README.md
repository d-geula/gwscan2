# Experimental auto login

This folder contains a standalone test flow for GateWa.rs that:

- logs in if needed
- solves the PIN captcha with Gemini
- navigates to `bank.php`
- clicks the deposit button

The runtime is split across:

- `login_test.py`: browser flow, site interaction, logging
- `gemini_pin_solver.py`: Gemini request/response handling for the PIN image

## Run

From the repository root:

```bash
uv run python experiments/auto_login/login_test.py
```

Optional flags:

```bash
uv run python experiments/auto_login/login_test.py --headless
uv run python experiments/auto_login/login_test.py --model gemini-3.1-pro-preview
```

## Environment

The script reads these from the repository `.env` file:

- `GW_USERNAME`
- `GW_EMAIL`
- `GW_PASSWORD`
- `GEMINI_API_KEY`

The browser profile used by the experiment lives in:

```text
experiments/auto_login/profile/
```

## Runtime behavior

- Login form entry happens directly without extra random delay.
- Non-login site interactions use a small randomized pause to avoid acting at perfectly fixed intervals.
- The script waits 1 extra second at the end so a headed run is easy to visually confirm.

## VPS target

For a cheap headless VPS, the minimal viable setup should be roughly:

- `1 vCPU`
- `1 GB RAM` minimum, `2 GB RAM` safer
- `10 GB` disk is plenty
- Ubuntu 24.04 LTS or Debian 12 is a sensible default

You also need:

- Python 3.13
- `uv`
- whatever Chromium/Chrome runtime dependencies `zendriver` needs on that distro

If you want the least friction, use a small Ubuntu VPS and test one manual headed run locally first, then only switch the VPS job to `--headless`.

## Scheduling

`systemd` is the simpler fit here than cron because:

- it is easy to start, stop, enable, and disable over SSH
- timer jitter is built in
- logs go straight to `journalctl`

The schedule you described maps cleanly to:

- base time: `5 minutes 15 seconds` past each hour
- extra randomness: up to `45 seconds`

That means each run happens between `:05:15` and `:06:00`.

### Service file

Create `/etc/systemd/system/gwscan2-auto-login.service`:

```ini
[Unit]
Description=gwscan2 auto login bank deposit test
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=dev
WorkingDirectory=/home/dev/gwscan2
ExecStart=/usr/local/bin/uv run python experiments/auto_login/login_test.py --headless
```

Adjust `User`, `WorkingDirectory`, and `ExecStart` to match the VPS.

### Timer file

Create `/etc/systemd/system/gwscan2-auto-login.timer`:

```ini
[Unit]
Description=Run gwscan2 auto login every hour shortly after :05

[Timer]
OnCalendar=*-*-* *:05:15
RandomizedDelaySec=45s
Persistent=true
Unit=gwscan2-auto-login.service

[Install]
WantedBy=timers.target
```

### Enable and control

Reload systemd after adding the files:

```bash
sudo systemctl daemon-reload
```

Enable and start the timer:

```bash
sudo systemctl enable --now gwscan2-auto-login.timer
```

Pause the schedule:

```bash
sudo systemctl stop gwscan2-auto-login.timer
```

Resume the schedule:

```bash
sudo systemctl start gwscan2-auto-login.timer
```

Disable it completely:

```bash
sudo systemctl disable --now gwscan2-auto-login.timer
```

Run the job once manually:

```bash
sudo systemctl start gwscan2-auto-login.service
```

Inspect timer state:

```bash
systemctl list-timers gwscan2-auto-login.timer
```

Inspect logs:

```bash
journalctl -u gwscan2-auto-login.service -n 200 --no-pager
```

## Notes

- `Persistent=true` means if the VPS is off during a scheduled time, systemd will run the missed job after boot.
- If you do not want catch-up behavior after downtime, remove `Persistent=true`.
- If you prefer cron, you can do it, but systemd is the cleaner operational choice for this case.
