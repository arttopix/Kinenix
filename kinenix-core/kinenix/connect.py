"""`kinenix connect`: the Hub this machine sends runs and worker heartbeats to.

The address and worker API key are saved in ~/.kinenix/kinenix.env, which `kinenix run` and kinenix-worker
read through kinenix.env.get_env; KINENIX_HUB_URL and KINENIX_HUB_API_KEY in the environment still win.
The connection is checked before anything is saved, so a mistyped key is caught at once.
"""
import os
import socket
from typing import NamedTuple, Optional
from urllib.parse import urlparse

import requests

from .env import LEGACY_NAMES, env_source, get_env
from .workspace import save_settings, saved_settings, settings_file

URL_KEY = "KINENIX_HUB_URL"
API_KEY = "KINENIX_HUB_API_KEY"
DEFAULT_PORT = 8080
TIMEOUT = 5


def normalize_url(text: str) -> str:
    """`192.168.1.137` -> `http://192.168.1.137:8080`; a full URL is kept (without a trailing slash)."""
    text = text.strip().rstrip("/")
    if "://" not in text:
        text = f"http://{text}"
    parsed = urlparse(text)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ValueError(f"'{text}' is not a Hub address; use for example http://192.168.1.137:8080")
    if parsed.scheme == "http" and parsed.port is None:
        text = f"http://{parsed.netloc}:{DEFAULT_PORT}{parsed.path}"
    return text


class CheckResult(NamedTuple):
    usable: bool
    message: str
    key_checked: bool = True


def describe_unreachable(url: str, error: requests.RequestException) -> str:
    """Why the Hub does not answer: the name, the port, or no answer at all."""
    parsed = urlparse(url)
    host, port = parsed.hostname or "", parsed.port or (443 if parsed.scheme == "https" else DEFAULT_PORT)
    try:
        socket.getaddrinfo(host, port)
    except socket.gaierror:
        hint = " Names ending in .local need mDNS (Avahi) on both machines." if host.endswith(".local") else ""
        return (f"Cannot find the address of '{host}'. Check the name, or use the Hub's IP address "
                f"(on the Hub: hostname -I).{hint}")
    if isinstance(error, requests.Timeout):
        return f"No answer from {host} on port {port} within {TIMEOUT} s; a firewall may block the port."
    return (f"{host} was found, but nothing accepts connections on port {port}: the Hub is not running there, "
            f"or it accepts only its own machine (on the Hub: kinenix hub setup, allow other machines).")


def check(url: str, key: Optional[str]) -> CheckResult:
    """Whether the Hub answers and accepts the key for sending runs, and why not."""
    try:
        health = requests.get(f"{url}/api/v1/healthz", timeout=TIMEOUT)
    except requests.RequestException as e:
        return CheckResult(False, describe_unreachable(url, e))
    if health.status_code != 200:
        return CheckResult(False, f"{url} answered HTTP {health.status_code}; it does not look like a Kinenix Hub.")
    try:
        res = requests.get(f"{url}/api/v1/auth/worker", headers={"X-API-Key": key} if key else {}, timeout=TIMEOUT)
    except requests.RequestException as e:
        return CheckResult(False, f"The key check failed ({e.__class__.__name__}).")
    if res.status_code == 200:
        return CheckResult(True, "The Hub accepts runs from this machine.")
    if res.status_code == 404:
        return CheckResult(True, "The Hub answers; it is an older version that cannot check keys, so the key was not checked.",
                           key_checked=False)
    if res.status_code == 401:
        return CheckResult(False, "The Hub rejected the key. On the Hub, `kinenix hub show-key` prints the right one.")
    if res.status_code == 403:
        return CheckResult(False, "The Hub has no worker API key, so it accepts runs only from its own machine. "
                                  "On the Hub, run `kinenix hub setup` and allow other machines; it creates a key.")
    return CheckResult(False, f"The key check returned HTTP {res.status_code}.")


def _environment_value(name: str) -> str:
    old = LEGACY_NAMES.get(name)
    return os.environ.get(name) or (os.environ.get(old) if old else "") or ""


def _environment_warnings(url: Optional[str]) -> list:
    """Values in the environment win over the saved ones; say so when they differ."""
    warnings = []
    env_url = _environment_value(URL_KEY)
    if env_url and env_url.rstrip("/") != (url or ""):
        warnings.append(f"KINENIX_HUB_URL={env_url} is set in the environment and takes precedence over "
                        f"`kinenix connect`. Remove it (a worker service reads ~/.kinenix/worker.env) for this to apply.")
    if _environment_value(API_KEY):
        warnings.append("KINENIX_HUB_API_KEY is set in the environment and takes precedence over the saved key.")
    return warnings


def show() -> int:
    """`kinenix connect` without arguments: the Hub in use, where it comes from, and whether it answers."""
    url = get_env(URL_KEY)
    if not url:
        print("Not connected to a Hub: runs are kept on this machine only.")
        print("Connect with: kinenix connect http://<hub-address>:8080")
        return 0
    sources = {"environment": "environment variable", "saved": str(settings_file())}
    print(f"Hub:  {url}  (from {sources[env_source(URL_KEY)]})")
    key_source = env_source(API_KEY)
    print(f"Key:  {'set, from ' + sources[key_source] if key_source else 'not set'}")
    result = check(url.rstrip("/"), get_env(API_KEY) or None)
    print(result.message)
    return 0 if result.usable else 1


def connect(url_text: str, key: Optional[str], verify: bool = True) -> int:
    """Checks the Hub and saves it with its key; nothing is saved when the check fails."""
    try:
        url = normalize_url(url_text)
    except ValueError as e:
        print(f"Error: {e}")
        return 1
    key_checked = False
    if verify:
        result = check(url, key)
        if not result.usable:
            print(f"Error: {result.message} Nothing was saved.")
            return 1
        print(result.message)
        key_checked = result.key_checked
    path = save_settings({URL_KEY: url, API_KEY: key or None})
    print(f"Saved in {path}: `kinenix run` and kinenix-worker on this machine send runs to {url}.")
    if not key and not key_checked:
        print("Warning: no key was saved, and the Hub could not confirm that it needs none. If it uses a key, "
              "it will reject runs: connect again with the key (on the Hub: kinenix hub show-key).")
    for warning in _environment_warnings(url):
        print(f"Warning: {warning}")
    return 0


def disconnect() -> int:
    had = bool(saved_settings().get(URL_KEY))
    path = save_settings({URL_KEY: None, API_KEY: None})
    print(f"Removed the saved Hub from {path}." if had else "No Hub was saved on this machine.")
    for warning in _environment_warnings(None):
        print(f"Warning: {warning}")
    return 0
