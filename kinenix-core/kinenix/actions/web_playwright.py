import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional
from playwright.sync_api import sync_playwright, Browser, Page, Playwright

from .base import BaseAction
from .registry import register_action
from ..models.context import ExecutionContext

logger = logging.getLogger("kinenix")


def _launch_browser_with_auto_install(pw: Playwright, headless: bool) -> Browser:
    if not headless and sys.platform.startswith("linux"):
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            logger.warning(
                "No display environment detected ($DISPLAY or $WAYLAND_DISPLAY is unset). "
                "Automatically switching Playwright browser to headless mode for headless Linux/SSH."
            )
            headless = True

    try:
        return pw.chromium.launch(headless=headless)
    except Exception as e:
        err_msg = str(e)
        if "Missing X server" in err_msg or "$DISPLAY" in err_msg:
            logger.warning(
                "Missing X server detected. Retrying Playwright launch in headless mode..."
            )
            return pw.chromium.launch(headless=True)
        if "Executable doesn't exist" in err_msg or "Please run the following command" in err_msg:
            logger.info("Playwright Chromium browser not detected. Installing Chromium automatically (first run only)...")
            res = subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"])
            if res.returncode != 0:
                raise RuntimeError(
                    "Failed to auto-install Chromium. Please run in terminal: playwright install chromium"
                ) from e
            try:
                return pw.chromium.launch(headless=headless)
            except Exception as retry_err:
                retry_msg = str(retry_err)
                if "Host system is missing dependencies" in retry_msg or "libraries" in retry_msg.lower():
                    raise RuntimeError(
                        "Chromium installed, but host system is missing OS dependencies. "
                        "Please run in terminal: sudo playwright install-deps chromium"
                    ) from retry_err
                raise
        elif "Host system is missing dependencies" in err_msg:
            raise RuntimeError(
                "Host system is missing dependencies to run Chromium. "
                "Please run in terminal: sudo playwright install-deps chromium"
            ) from e
        raise


def _get_page(context: ExecutionContext) -> Page:
    page = context.get_variable("__playwright_page__")
    if not page:
        raise RuntimeError("No active browser page found. Please execute 'web.open' first.")
    return page


def _resolve_locator(page: Page, parameters: Dict[str, Any]):
    selector = parameters.get("selector")
    label = parameters.get("label")

    if label:
        return page.locator(f"//label[normalize-space()='{label}']/following::input[1]")
    elif selector:
        return page.locator(selector)
    else:
        raise ValueError("Either 'selector' or 'label' parameter is required.")


@register_action("web.open")
class WebOpenAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        url = parameters.get("url")
        headless = bool(parameters.get("headless", False))
        timeout = float(parameters.get("timeout", 30000))

        pw: Optional[Playwright] = context.get_variable("__playwright_pw__")
        browser: Optional[Browser] = context.get_variable("__playwright_browser__")

        if not pw:
            pw = sync_playwright().start()
            context.set_variable("__playwright_pw__", pw)

        if not browser:
            browser = _launch_browser_with_auto_install(pw, headless=headless)
            context.set_variable("__playwright_browser__", browser)

        page = browser.new_page()
        page.set_default_timeout(timeout)
        context.set_variable("__playwright_page__", page)

        if url:
            page.goto(url, wait_until="networkidle")

        return {"url": url, "headless": headless, "status": "opened"}


@register_action("web.click")
class WebClickAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        locator = _resolve_locator(page, parameters)
        timeout = float(parameters.get("timeout", 30000))
        optional = bool(parameters.get("optional", False))
        try:
            locator.first.click(timeout=timeout)
            return {"action": "web.click", "status": "clicked"}
        except Exception as e:
            if optional:
                logger.info(f"Optional click on '{parameters.get('selector') or parameters.get('label')}' skipped: {e}")
                return {"action": "web.click", "status": "skipped", "reason": str(e)}
            raise


@register_action("web.type")
class WebTypeAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        locator = _resolve_locator(page, parameters)
        text = str(parameters.get("text", ""))
        locator.first.fill(text)
        return {"action": "web.type", "text": text, "status": "typed"}


@register_action("web.get_text")
class WebGetTextAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        locator = _resolve_locator(page, parameters)
        text = locator.first.inner_text()
        return text


@register_action("web.screenshot")
class WebScreenshotAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        path_str = parameters.get("path", "screenshot.png")
        full_page = bool(parameters.get("full_page", False))

        target_path = Path(path_str)
        if not target_path.is_absolute():
            flow_dir_str = context.get_variable("__flow_dir__")
            if flow_dir_str:
                target_path = Path(flow_dir_str) / path_str

        target_path.parent.mkdir(parents=True, exist_ok=True)
        page.screenshot(path=str(target_path), full_page=full_page)
        return {"screenshot_path": str(target_path)}


@register_action("web.download")
class WebDownloadAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        selector = parameters.get("selector")
        target_path_str = parameters.get("target_path", "downloads/downloaded_file")
        timeout = float(parameters.get("timeout", 30000))

        target_path = Path(target_path_str)
        if not target_path.is_absolute():
            flow_dir_str = context.get_variable("__flow_dir__")
            if flow_dir_str:
                target_path = Path(flow_dir_str) / target_path_str

        target_path.parent.mkdir(parents=True, exist_ok=True)

        if not selector:
            raise ValueError("Parameter 'selector' is required for action 'web.download'.")

        locator = _resolve_locator(page, parameters).first

        # Check if the element has an href attribute to download directly via browser session
        href = locator.get_attribute("href")
        if href:
            # Resolve relative URL against current page URL
            from urllib.parse import urljoin
            full_url = urljoin(page.url, href)
            response = page.context.request.get(full_url, timeout=timeout)
            if response.status >= 400:
                raise RuntimeError(f"Failed to download from '{full_url}', HTTP status {response.status}")
            target_path.write_bytes(response.body())
        else:
            # If it's a button or trigger that initiates a browser download event
            with page.expect_download(timeout=timeout) as download_info:
                locator.click()
            download = download_info.value
            download.save_as(str(target_path))

        file_size = target_path.stat().st_size
        return {
            "status": "downloaded",
            "file_path": str(target_path),
            "file_size": file_size
        }


@register_action("web.close")
class WebCloseAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        if context.get_variable("__shared_browser__"):
            logger.warning(
                "Safeguard: 'web.close' was invoked inside a subflow sharing parent browser session. "
                "Skipping browser closure to protect parent workflow."
            )
            return {"status": "skipped", "reason": "protected_shared_browser"}

        browser: Optional[Browser] = context.get_variable("__playwright_browser__")
        pw: Optional[Playwright] = context.get_variable("__playwright_pw__")

        if browser:
            browser.close()
            context.set_variable("__playwright_browser__", None)
            context.set_variable("__playwright_page__", None)

        if pw:
            pw.stop()
            context.set_variable("__playwright_pw__", None)

        return {"status": "closed"}


@register_action("web.wait_for")
class WebWaitForAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        selector = parameters.get("selector")
        label = parameters.get("label")
        state = parameters.get("state", "visible")
        timeout = float(parameters.get("timeout", 30000))

        if selector or label:
            locator = _resolve_locator(page, parameters)
            locator.first.wait_for(state=state, timeout=timeout)
            return {"action": "web.wait_for", "state": state, "status": "ready"}
        else:
            page.wait_for_timeout(timeout)
            return {"action": "web.wait_for", "timeout_ms": timeout, "status": "waited"}


@register_action("web.is_visible")
class WebIsVisibleAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        locator = _resolve_locator(page, parameters)
        timeout = float(parameters.get("timeout", 2000))
        try:
            if timeout <= 0:
                return locator.first.is_visible()
            locator.first.wait_for(state="visible", timeout=timeout)
            return True
        except Exception:
            return False


@register_action("web.get_attribute")
class WebGetAttributeAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        attr_name = parameters.get("attribute") or parameters.get("name")
        if not attr_name:
            raise ValueError("Parameter 'attribute' is required for action 'web.get_attribute'.")

        locator = _resolve_locator(page, parameters)
        val = locator.first.get_attribute(attr_name)
        return val


@register_action("web.press")
class WebPressAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        key = parameters.get("key")
        if not key:
            raise ValueError("Parameter 'key' is required for action 'web.press'.")

        selector = parameters.get("selector")
        label = parameters.get("label")

        if selector or label:
            locator = _resolve_locator(page, parameters)
            locator.first.press(key)
        else:
            page.keyboard.press(key)

        return {"action": "web.press", "key": key, "status": "pressed"}


@register_action("web.scroll")
class WebScrollAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        selector = parameters.get("selector")
        label = parameters.get("label")

        if selector or label:
            locator = _resolve_locator(page, parameters)
            locator.first.scroll_into_view_if_needed()
            return {"action": "web.scroll", "target": "element", "status": "scrolled"}

        direction = str(parameters.get("direction", "down")).lower()
        amount = int(parameters.get("amount", 500))

        if direction == "bottom":
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        elif direction == "top":
            page.evaluate("window.scrollTo(0, 0)")
        elif direction == "up":
            page.evaluate(f"window.scrollBy(0, -{amount})")
        else:  # down
            page.evaluate(f"window.scrollBy(0, {amount})")

        return {"action": "web.scroll", "direction": direction, "amount": amount, "status": "scrolled"}


@register_action("web.hover")
class WebHoverAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        timeout = float(parameters.get("timeout", 30000))
        locator = _resolve_locator(page, parameters)
        locator.first.hover(timeout=timeout)
        return {"action": "web.hover", "status": "hovered"}


@register_action("web.switch_tab")
class WebSwitchTabAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        browser: Optional[Browser] = context.get_variable("__playwright_browser__")
        if not browser or not browser.contexts:
            raise RuntimeError("No active browser context found. Cannot switch tab.")

        browser_context = browser.contexts[0]
        pages = browser_context.pages
        if not pages:
            raise RuntimeError("No open tabs/pages found in browser.")

        target_page = None
        index = parameters.get("index")
        url_pattern = parameters.get("url_pattern")
        title = parameters.get("title")

        if index is not None:
            idx = int(index)
            if 0 <= idx < len(pages) or -len(pages) <= idx < 0:
                target_page = pages[idx]
            else:
                raise IndexError(f"Tab index {idx} out of range (total open tabs: {len(pages)}).")
        elif url_pattern:
            for p in pages:
                if url_pattern in p.url:
                    target_page = p
                    break
            if not target_page:
                raise ValueError(f"No tab found matching url_pattern: '{url_pattern}'.")
        elif title:
            for p in pages:
                if title.lower() in p.title().lower():
                    target_page = p
                    break
            if not target_page:
                raise ValueError(f"No tab found matching title: '{title}'.")
        else:
            target_page = pages[-1]

        target_page.bring_to_front()
        context.set_variable("__playwright_page__", target_page)
        return {
            "action": "web.switch_tab",
            "title": target_page.title(),
            "url": target_page.url,
            "status": "switched"
        }


@register_action("web.select_option")
class WebSelectOptionAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        locator = _resolve_locator(page, parameters)

        val = parameters.get("value")
        text = parameters.get("label_text") or parameters.get("text")
        index = parameters.get("index")
        ai_match = bool(parameters.get("ai_match", False))

        if ai_match:
            from .ai_systemone import call_systemone_api

            target_query = str(text if text is not None else (val if val is not None else "")).strip()
            if not target_query:
                raise ValueError("Parameter 'text' or 'value' is required when 'ai_match' is enabled.")

            # Extract options from DOM via Playwright evaluate
            dom_options = locator.first.evaluate("""
                el => {
                    if (!el || !el.options) return [];
                    return Array.from(el.options).map(o => ({
                        value: o.value,
                        text: (o.text || '').trim()
                    }));
                }
            """)

            if not dom_options:
                raise RuntimeError("No <option> elements found in the target select element.")

            # Fast-path: Check exact match first
            exact_match = None
            for opt in dom_options:
                opt_text = opt.get("text", "")
                opt_val = opt.get("value", "")
                if target_query.lower() in (opt_text.lower(), opt_val.lower()):
                    exact_match = opt
                    break

            if exact_match:
                selected = locator.first.select_option(value=exact_match["value"])
                return {
                    "action": "web.select_option",
                    "selected": selected,
                    "matched_text": exact_match["text"],
                    "ai_match": True,
                    "confidence": 1.0,
                    "match_type": "exact",
                    "status": "selected"
                }

            # AI Semantic Matching using OpenThai-SystemOne
            base_url = str(parameters.get("systemone_url") or parameters.get("base_url") or "http://localhost:8000")
            criteria = {opt["text"]: None for opt in dom_options if opt.get("text")}

            sys_resp = call_systemone_api(
                state=target_query,
                questions={
                    "selected_option": {
                        "type": "choice",
                        "instructions": "เลือกตัวเลือกจากรายการที่ตรงกับความหมายของข้อความที่ระบุมากที่สุด",
                        "criteria": criteria
                    }
                },
                base_url=base_url,
                timeout=float(parameters.get("timeout", 30.0)),
                fallback_to_ollama=bool(parameters.get("fallback_to_ollama", True))
            )

            matched_label = sys_resp.get("answers", {}).get("selected_option", {}).get("choice")
            confidence = sys_resp.get("answers", {}).get("selected_option", {}).get("confidence")

            if not matched_label:
                raise RuntimeError(
                    f"AI semantic matching failed to resolve option for '{target_query}'."
                )

            # Match to value or label
            matched_opt = next((o for o in dom_options if o.get("text") == matched_label), None)
            if matched_opt and matched_opt.get("value"):
                selected = locator.first.select_option(value=matched_opt["value"])
            else:
                selected = locator.first.select_option(label=matched_label)

            return {
                "action": "web.select_option",
                "selected": selected,
                "matched_text": matched_label,
                "confidence": confidence,
                "ai_match": True,
                "match_type": "semantic",
                "status": "selected"
            }

        if val is not None:
            selected = locator.first.select_option(value=str(val))
        elif text is not None:
            selected = locator.first.select_option(label=str(text))
        elif index is not None:
            selected = locator.first.select_option(index=int(index))
        else:
            raise ValueError("One of 'value', 'text', or 'index' is required for action 'web.select_option'.")

        return {"action": "web.select_option", "selected": selected, "status": "selected"}


@register_action("web.upload_file")
class WebUploadFileAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        file_path_str = parameters.get("file_path") or parameters.get("path")
        if not file_path_str:
            raise ValueError("Parameter 'file_path' is required for action 'web.upload_file'.")

        target_path = Path(file_path_str)
        if not target_path.is_absolute():
            flow_dir_str = context.get_variable("__flow_dir__")
            if flow_dir_str:
                target_path = Path(flow_dir_str) / file_path_str

        if not target_path.exists():
            raise FileNotFoundError(f"File to upload not found: {target_path}")

        locator = _resolve_locator(page, parameters)
        locator.first.set_input_files(str(target_path.resolve()))

        return {
            "action": "web.upload_file",
            "file_path": str(target_path.resolve()),
            "status": "uploaded"
        }


@register_action("web.check")
class WebCheckAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        timeout = float(parameters.get("timeout", 30000))
        locator = _resolve_locator(page, parameters)
        locator.first.check(timeout=timeout)
        return {"action": "web.check", "status": "checked"}


@register_action("web.uncheck")
class WebUncheckAction(BaseAction):
    def execute(self, parameters: Dict[str, Any], context: ExecutionContext) -> Any:
        page = _get_page(context)
        timeout = float(parameters.get("timeout", 30000))
        locator = _resolve_locator(page, parameters)
        locator.first.uncheck(timeout=timeout)
        return {"action": "web.uncheck", "status": "unchecked"}

