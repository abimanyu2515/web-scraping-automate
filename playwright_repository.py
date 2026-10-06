import os
import sys

from dotenv import load_dotenv
from playwright.sync_api import Locator, Page, TimeoutError, expect, sync_playwright

from repository import load_repository


DEFAULT_URL = "https://cricscore-wheat.vercel.app/access"
PIN_LENGTH = 5
PLAYER_FILTERS = ("BAT", "BOWL", "ALL-ROUNDER", "ALL")


class ObjectRepositoryPage:
    def __init__(self, page: Page, objects: dict):
        self.page = page
        self.objects = objects

    def locator(self, name: str) -> Locator:
        if name not in self.objects:
            raise KeyError(f"Object {name!r} is not in the repository")

        element = self.objects[name]
        if element.get("locator_type") != "css":
            raise ValueError(
                f"Unsupported locator type for {name!r}: "
                f"{element.get('locator_type')!r}"
            )

        selector = element.get("locator")
        if not selector:
            raise ValueError(f"Object {name!r} does not have a locator")

        return self.page.locator(selector)

    def click(self, name: str) -> None:
        self._require_unique(name).click()

    def fill_pin(
        self, target: str | Locator, pin: str, *, reverse: bool = True
    ) -> None:
        if not pin.isdigit():
            raise ValueError("The PIN must contain only digits")

        self.page.wait_for_function(
            """() => {
                const input = document.querySelector('input[type="password"]');
                return input && Object.keys(input).some(
                    (key) => key.startsWith('__reactProps$')
                );
            }""",
            timeout=15000,
        )

        inputs = self.locator(target) if isinstance(target, str) else target
        count = inputs.count()
        if count != len(pin):
            raise ValueError(
                f"Expected {len(pin)} PIN fields, found {count}"
            )

        indexes = reversed(range(len(pin))) if reverse else range(len(pin))
        for index in indexes:
            inputs.nth(index).fill(pin[index])
            expect(inputs.nth(index)).to_have_value(pin[index], timeout=3000)

        entered_pin = "".join(
            inputs.nth(index).input_value() for index in range(count)
        )
        if entered_pin != pin:
            mismatched_indexes = [
                index
                for index in range(count)
                if inputs.nth(index).input_value() != pin[index]
            ]
            raise AssertionError(
                "PIN input fields did not retain values at indexes "
                f"{mismatched_indexes}"
            )

    def _require_unique(self, name: str) -> Locator:
        locator = self.locator(name)
        count = locator.count()
        if count != 1:
            raise ValueError(
                f"Expected exactly one match for {name!r}, found {count}"
            )
        return locator


def _click_named_control(page: Page, label: str) -> None:
    for role in ("link", "button"):
        locator = page.get_by_role(role, name=label, exact=True)
        count = locator.count()
        if count > 1:
            raise ValueError(f"Expected one {role} named {label!r}, found {count}")
        if count == 1:
            locator.click()
            return

    text = page.get_by_text(label, exact=True)
    count = text.count()
    if count != 1:
        raise ValueError(f"Could not find one visible control named {label!r}")
    text.click()


def _exercise_players(page: Page) -> None:
    _click_named_control(page, "MANAGE PLAYERS")

    for filter_name in PLAYER_FILTERS:
        filter_button = page.get_by_role(
            "button", name=filter_name, exact=True
        )
        if filter_button.count() != 1:
            raise AssertionError(
                f"Expected one player filter button {filter_name!r}"
            )
        filter_button.click()
        print(f"Players filter: {filter_name}")


def _exercise_matches(page: Page) -> None:
    _click_named_control(page, "MATCHES")
    page.get_by_text("PRACTICE MATCH", exact=True).first.wait_for(
        state="visible", timeout=15000
    )
    match_count = page.get_by_text("PRACTICE MATCH", exact=True).count()
    print(f"Matches page: {match_count} practice match card(s) found")


def main() -> None:
    load_dotenv()
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    objects = load_repository(url)
    if not objects:
        raise ValueError(f"No objects found in the repository for {url!r}")

    pin = os.getenv("CRICSCORE_ACCESS_PIN")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded")
            repository_page = ObjectRepositoryPage(page, objects)

            for name in objects:
                matches = repository_page.locator(name).count()
                print(f"{name}: {matches} matching element(s)")
                if matches == 0:
                    raise AssertionError(
                        f"Repository locator {name!r} did not match the page"
                    )

            if not pin:
                print(
                    "Access page verified. Set CRICSCORE_ACCESS_PIN in the "
                    "environment to run the authenticated Players and Matches flow."
                )
                return

            repository_page.fill_pin("_input", pin)
            repository_page.click("enter_button")
            try:
                page.get_by_text("MANAGE PLAYERS", exact=True).wait_for(
                    state="visible", timeout=15000
                )
            except TimeoutError as error:
                raise RuntimeError(
                    "The dashboard did not open after submitting the access PIN"
                ) from error

            _exercise_players(page)
            _exercise_matches(page)
        finally:
            browser.close()


if __name__ == "__main__":
    main()
