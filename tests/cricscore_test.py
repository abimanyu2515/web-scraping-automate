from pathlib import Path

from dotenv import dotenv_values
from playwright.sync_api import TimeoutError, sync_playwright

from playwright_repository import ObjectRepositoryPage
from repository import load_repository


URL = "https://cricscore-wheat.vercel.app/access"
HOME_URL = "https://cricscore-wheat.vercel.app/"
ADMIN_URL = "https://cricscore-wheat.vercel.app/admin"
ADMIN_PIN_LENGTH = 4
from dotenv import load_dotenv

load_dotenv()

def _get_pin(
    environment: dict[str, str | None],
    environment_variable: str,
    description: str,
    length: int,
) -> str:
    pin = (environment.get(environment_variable) or "").strip()
    if not pin:
        raise ValueError(
            f"Missing {environment_variable} in the project .env file. "
            f"Add {environment_variable}=... with your {description}."
        )
    if len(pin) != length or not pin.isdigit():
        raise ValueError(
            f"{environment_variable} in .env must contain exactly {length} digits"
        )
    return pin


def main() -> None:
    project_root = Path(__file__).resolve().parents[1]
    environment = dotenv_values(project_root / ".env")
    access_pin = _get_pin(
        environment, "CRICSCORE_ACCESS_PIN", "access PIN", 5
    )
    admin_pin = _get_pin(
        environment, "CRICSCORE_ADMIN_PIN", "admin PIN", ADMIN_PIN_LENGTH
    )

    objects = load_repository(URL)
    if not objects:
        raise ValueError(f"No objects found in the repository for {URL!r}")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        try:
            page = browser.new_page()
            page.goto(URL, wait_until="domcontentloaded")
            page.get_by_role("heading", name="// CRICSCORE", exact=True).wait_for(
                state="visible", timeout=15000
            )
            repository_page = ObjectRepositoryPage(page, objects)
            repository_page.fill_pin("_input", access_pin, reverse=True)
            repository_page.click("enter_button")

            try:
                page.wait_for_url(HOME_URL, timeout=15000)
            except TimeoutError as error:
                page_text = " ".join(page.locator("body").inner_text().split())
                raise RuntimeError(
                    "The access page did not navigate to the dashboard. "
                    "Check the access PIN. "
                    f"Current URL: {page.url}. Page message: {page_text[:300]!r}"
                ) from error

            page.get_by_role("heading", name="CRICSCORE", exact=True).wait_for(
                state="visible", timeout=15000
            )
            page.goto(ADMIN_URL, wait_until="domcontentloaded")
            try:
                page.get_by_text("// ADMIN PIN REQUIRED", exact=True).wait_for(
                    state="visible", timeout=15000
                )
            except TimeoutError as error:
                raise RuntimeError("The admin PIN prompt did not appear") from error

            admin_inputs = page.get_by_role("textbox")
            if admin_inputs.count() != ADMIN_PIN_LENGTH:
                raise AssertionError(
                    f"Expected {ADMIN_PIN_LENGTH} admin PIN fields, "
                    f"found {admin_inputs.count()}"
                )
            repository_page.fill_pin(
                admin_inputs, admin_pin, reverse=False
            )
            try:
                admin_panel = page.get_by_text("// ADMIN PANEL", exact=True)
                if admin_panel.count() == 0 and admin_inputs.count() == ADMIN_PIN_LENGTH:
                    page.get_by_role("button", name="VERIFY", exact=True).click()
                admin_panel.wait_for(state="visible", timeout=15000)
            except TimeoutError as error:
                page_text = " ".join(page.locator("body").inner_text().split())
                raise RuntimeError(
                    "The admin panel did not open after submitting the admin PIN"
                    f" Current URL: {page.url}. "
                    f"Page message: {page_text[:300]!r}"
                ) from error

            print("Admin panel is open. Close the browser window when finished.")
            page.wait_for_event("close")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
