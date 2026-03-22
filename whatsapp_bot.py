"""
whatsapp_bot.py — Selenium WhatsApp Web automation
Flow: open chat → click attach → click "Photos & Videos" menu item → upload → paste caption → send
"""
import os, time, logging, pyperclip
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

SESSION_DIR = os.path.abspath("./wa_session")
WA_URL      = "https://web.whatsapp.com"

logging.basicConfig(level=logging.INFO, format="%(asctime)s [BOT] %(message)s")
log = logging.getLogger("wa_bot")


def _make_driver(headless=False):
    opts = Options()
    opts.add_argument(f"--user-data-dir={SESSION_DIR}")
    opts.add_argument("--profile-directory=Default")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1300,900")
    if headless:
        opts.add_argument("--headless=new")
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    opts.add_argument("--disable-blink-features=AutomationControlled")
    service = Service(ChromeDriverManager().install())
    return webdriver.Chrome(service=service, options=opts)


class WhatsAppBot:
    def __init__(self, headless=False):
        self.driver   = None
        self.headless = headless
        self.ready    = False

    # ── Lifecycle ──────────────────────────────────────────
    def start(self):
        os.makedirs(SESSION_DIR, exist_ok=True)
        log.info("Launching Chrome...")
        self.driver = _make_driver(headless=self.headless)
        self.driver.get(WA_URL)
        log.info("Waiting for WhatsApp Web to load (scan QR if prompted)...")
        self._wait_ready(timeout=120)

    def _wait_ready(self, timeout=120):
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR,
                    'div[aria-label="Search input textbox"], '
                    'div[data-testid="search-input"]'))
            )
            self.ready = True
            log.info("✅ WhatsApp ready!")
        except TimeoutException:
            log.error("❌ WhatsApp did not load in time.")
            self.ready = False

    def is_alive(self):
        try:
            return self.driver is not None and bool(self.driver.window_handles)
        except Exception:
            return False

    def quit(self):
        if self.driver:
            self.driver.quit()
            self.driver = None
            self.ready  = False

    # ── Send image ─────────────────────────────────────────
    def send_image_to_group(self, group_name: str, image_path: str, caption: str) -> tuple[bool, str]:
        if not self.ready or not self.is_alive():
            return False, "Bot not ready"
        try:
            abs_image = str(Path(image_path).resolve())
            if not os.path.exists(abs_image):
                return False, f"Image not found: {abs_image}"

            # 1. Open chat
            if not self._open_chat(group_name):
                return False, f"Group not found: {group_name}"
            time.sleep(2)

            # 2. Click attach button to open the attach menu
            attach = self._find_attach_button()
            if not attach:
                return False, "Attach button not found"
            attach.click()
            log.info("    Attach menu opened")
            time.sleep(1.2)

            # 3. Click the "Photos & Videos" label/li in the attach menu
            #    This opens the file picker for images specifically
            if not self._click_photos_videos_menu():
                return False, "Photos & Videos menu item not found"
            time.sleep(1)

            # 4. Upload file via the now-active file input
            if not self._upload_file(abs_image):
                return False, "File upload failed"
            log.info("    Image uploaded, waiting for preview...")
            time.sleep(3)  # wait for WhatsApp to process & show preview

            # 5. Type caption into the caption box (NOT the main message box)
            if caption and caption.strip():
                if not self._type_caption(caption):
                    log.warning("    Caption box not found — will send without caption")
            time.sleep(0.5)

            # 6. Press Enter to send (most reliable method for the send button)
            if not self._press_send():
                return False, "Could not send"
            time.sleep(3)

            log.info(f"✅ Sent to: {group_name}")
            return True, "Sent"

        except Exception as e:
            log.error(f"❌ Error sending to {group_name}: {e}")
            return False, str(e)

    # ── Send text ──────────────────────────────────────────
    def send_text_to_group(self, group_name: str, message: str) -> tuple[bool, str]:
        if not self.ready or not self.is_alive():
            return False, "Bot not ready"
        try:
            if not self._open_chat(group_name):
                return False, f"Group not found: {group_name}"
            time.sleep(1.5)
            msg_box = self._wait_el('div[aria-label="Type a message"]', 10)
            if not msg_box:
                return False, "Message box not found"
            msg_box.click()
            self._paste_text(msg_box, message)
            time.sleep(0.5)
            msg_box.send_keys(Keys.ENTER)
            time.sleep(2)
            log.info(f"✅ Text sent to: {group_name}")
            return True, "Sent"
        except Exception as e:
            return False, str(e)

    # ── Step helpers ───────────────────────────────────────

    def _find_attach_button(self):
        """Find the paperclip attach button in the chat footer."""
        selectors = [
            'div[title="Attach"]',
            'button[title="Attach"]',
            '[aria-label="Attach"]',
            'div[data-testid="clip"]',
            'span[data-testid="clip"]',
            'div[data-testid="attach-menu-plus"]',
            'span[data-testid="attach-menu-plus"]',
        ]
        for sel in selectors:
            try:
                el = WebDriverWait(self.driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                return el
            except Exception:
                continue
        return None

    def _click_photos_videos_menu(self) -> bool:
        """
        After clicking attach, a popup menu appears with:
          - Photos & Videos
          - Documents
          - Camera
          - Contact
        We need to click 'Photos & Videos' so the image is sent as a photo.
        """
        # Try clicking the visible menu item labeled Photos & Videos
        label_selectors = [
            # by aria-label on the li or button
            'li[aria-label*="Photos"]',
            'button[aria-label*="Photos"]',
            'div[aria-label*="Photos"]',
            # by data-testid
            'li[data-testid*="photo"]',
            'div[data-testid*="photo"]',
            # by title
            '[title*="Photos"]',
            '[title*="Photo"]',
            # span text match via XPath (fallback)
        ]
        for sel in label_selectors:
            try:
                el = WebDriverWait(self.driver, 3).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                el.click()
                log.info("    Clicked Photos & Videos menu item")
                return True
            except Exception:
                continue

        # XPath fallback — find any element containing "Photos" text
        try:
            el = WebDriverWait(self.driver, 3).until(
                EC.element_to_be_clickable((By.XPATH,
                    '//*[contains(text(),"Photos") or contains(text(),"photos")]')))
            el.click()
            log.info("    Clicked Photos via XPath")
            return True
        except Exception:
            pass

        # Last resort — the file input for images becomes clickable after attach click
        # Just send keys directly to it without clicking the menu
        log.info("    Menu item not found — using direct file input")
        return True  # continue to _upload_file which will handle it

    def _upload_file(self, abs_image: str) -> bool:
        """Send the file path to the correct file input."""
        # After clicking Photos & Videos, an <input type=file> becomes active
        # We target image-accepting inputs specifically
        selectors = [
            'input[accept="image/*,video/mp4,video/3gpp,video/quicktime"]',
            'input[accept*="image/*"]',
            'input[accept*="image/"]',
            'input[type="file"]',
        ]
        for sel in selectors:
            try:
                els = self.driver.find_elements(By.CSS_SELECTOR, sel)
                if els:
                    # Use JS to make visible then send keys
                    self.driver.execute_script(
                        "arguments[0].style.display='block';"
                        "arguments[0].style.visibility='visible';"
                        "arguments[0].style.opacity='1';",
                        els[0]
                    )
                    els[0].send_keys(abs_image)
                    log.info(f"    File sent to input: {sel}")
                    return True
            except Exception:
                continue
        return False

    def _type_caption(self, caption: str) -> bool:
        """
        Find the caption box that appears in the image preview and paste text.
        This is DIFFERENT from the main message box.
        """
        selectors = [
            'div[aria-label="Add a caption"]',
            'div[aria-label="Caption"]',
            'p[class*="caption"]',
            'div[data-testid="media-caption-input-container"] div[contenteditable]',
            'div[contenteditable="true"][data-tab="10"]',
            'div[contenteditable="true"][data-tab="7"]',
            'div[contenteditable="true"][data-tab="6"]',
        ]
        for sel in selectors:
            try:
                el = WebDriverWait(self.driver, 6).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, sel)))
                if el and el.is_displayed():
                    el.click()
                    time.sleep(0.3)
                    self._paste_text(el, caption)
                    log.info("    Caption typed")
                    return True
            except Exception:
                continue

        # XPath fallback for contenteditable in the preview modal
        try:
            el = WebDriverWait(self.driver, 4).until(
                EC.presence_of_element_located((By.XPATH,
                    '//div[@contenteditable="true" and @data-lexical-editor]')))
            if el and el.is_displayed():
                el.click()
                time.sleep(0.3)
                self._paste_text(el, caption)
                log.info("    Caption typed via XPath")
                return True
        except Exception:
            pass

        return False

    def _press_send(self) -> bool:
        """
        Press Enter on the caption box OR click the send button.
        Enter is most reliable when the caption box is focused.
        """
        # Try pressing Enter on whichever element is focused
        try:
            focused = self.driver.switch_to.active_element
            if focused:
                focused.send_keys(Keys.ENTER)
                log.info("    Pressed Enter on focused element")
                return True
        except Exception:
            pass

        # Fallback: find and JS-click the send button
        selectors = [
            'div[aria-label="Send"]',
            'button[aria-label="Send"]',
            'span[data-testid="send"]',
            'div[data-testid="send"]',
            '[aria-label="Send"]',
        ]
        for sel in selectors:
            try:
                el = WebDriverWait(self.driver, 6).until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, sel)))
                self.driver.execute_script("arguments[0].click();", el)
                log.info(f"    Send button clicked: {sel}")
                return True
            except Exception:
                continue
        return False

    def _paste_text(self, element, text: str):
        """Paste text including emojis via clipboard (Ctrl+V)."""
        try:
            pyperclip.copy(text)
            element.click()
            time.sleep(0.2)
            element.send_keys(Keys.CONTROL, 'v')
            time.sleep(0.3)
        except Exception as e:
            log.warning(f"Clipboard paste failed ({e}), stripping emojis")
            safe = ''.join(c for c in text if ord(c) <= 0xFFFF)
            element.send_keys(safe)

    def _open_chat(self, group_name: str) -> bool:
        try:
            search = self._wait_el(
                'div[aria-label="Search input textbox"], '
                'div[data-testid="search-input"]', 10)
            if not search:
                return False
            search.click()
            time.sleep(0.2)
            search.send_keys(Keys.CONTROL + "a")
            search.send_keys(Keys.DELETE)
            time.sleep(0.2)
            pyperclip.copy(group_name)
            search.send_keys(Keys.CONTROL, 'v')
            time.sleep(2)
            try:
                result = self.driver.find_element(
                    By.XPATH, f'//span[@title="{group_name}"]')
                result.click()
                return True
            except NoSuchElementException:
                pass
            results = self.driver.find_elements(
                By.XPATH, f'//span[contains(@title, "{group_name}")]')
            if results:
                results[0].click()
                return True
            return False
        except Exception as e:
            log.error(f"_open_chat error: {e}")
            return False

    def _wait_el(self, selector: str, timeout: int = 8):
        try:
            return WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
        except TimeoutException:
            return None

    def get_groups_list(self) -> list[str]:
        try:
            search = self._wait_el('div[aria-label="Search input textbox"]', 10)
            search.click()
            search.send_keys(" ")
            time.sleep(2)
            spans = self.driver.find_elements(By.CSS_SELECTOR, 'span[dir="auto"][title]')
            names = list({s.get_attribute("title") for s in spans if s.get_attribute("title")})
            search.send_keys(Keys.CONTROL + "a")
            search.send_keys(Keys.DELETE)
            return sorted(names)
        except Exception:
            return []


# ── Singleton ──────────────────────────────────────────────
_bot: WhatsAppBot = None

def get_bot(headless=False) -> WhatsAppBot:
    global _bot
    if _bot is None:
        _bot = WhatsAppBot(headless=headless)
    return _bot
