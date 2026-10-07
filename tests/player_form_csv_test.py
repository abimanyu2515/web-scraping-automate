import argparse
import csv
from pathlib import Path

from dotenv import dotenv_values
from playwright.sync_api import TimeoutError, expect, sync_playwright

from playwright_repository import ObjectRepositoryPage
from repository import load_repository


ACCESS_URL = "https://cricscore-wheat.vercel.app/access"
HOME_URL = "https://cricscore-wheat.vercel.app/"
EXPECTED_COLUMNS = (
    "player_name",
    "role",
    "batting_hand",
    "bowling_hand",
    "bowling_style",
)
VALID_ROLES = {"BATSMAN", "BOWLER", "ALL-ROUNDER"}
VALID_HANDS = {"Right", "Left"}
VALID_BOWLING_STYLES = {
    "Fast",
    "Fast-medium",
    "Medium-fast",
    "Medium",
    "Off spin",
    "Leg spin",
}
EXPECTED_ROWS = 20


def _read_test_data(csv_path: Path) -> list[dict[str, str]]:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        if tuple(reader.fieldnames or ()) != EXPECTED_COLUMNS:
            raise ValueError(
                f"CSV columns must be exactly {', '.join(EXPECTED_COLUMNS)}"
            )
        rows = list(reader)

    if len(rows) != EXPECTED_ROWS:
        raise ValueError(
            f"Expected exactly {EXPECTED_ROWS} CSV rows, found {len(rows)}"
        )

    player_names: set[str] = set()
    for row_number, row in enumerate(rows, start=2):
        for column in EXPECTED_COLUMNS:
            row[column] = (row[column] or "").strip()
            if not row[column]:
                raise ValueError(
                    f"CSV row {row_number} has an empty {column!r} value"
                )

        if row["player_name"] in player_names:
            raise ValueError(
                f"CSV row {row_number} repeats a player_name"
            )
        player_names.add(row["player_name"])

        if row["role"] not in VALID_ROLES:
            raise ValueError(f"CSV row {row_number} has an unsupported role")
        if row["batting_hand"] not in VALID_HANDS:
            raise ValueError(
                f"CSV row {row_number} has an unsupported batting_hand"
            )
        if row["bowling_hand"] not in VALID_HANDS:
            raise ValueError(
                f"CSV row {row_number} has an unsupported bowling_hand"
            )
        if row["bowling_style"] not in VALID_BOWLING_STYLES:
            raise ValueError(
                f"CSV row {row_number} has an unsupported bowling_style"
            )

    return rows


def _required_pin(environment: dict[str, str | None], name: str, length: int) -> str:
    pin = (environment.get(name) or "").strip()
    if len(pin) != length or not pin.isdigit():
        raise ValueError(
            f"{name} in the project .env must contain exactly {length} digits"
        )
    return pin


def _require_object_repository(objects: dict, names: tuple[str, ...]) -> None:
    missing = [name for name in names if name not in objects]
    if missing:
        raise KeyError(
            "Missing object repository entries: " + ", ".join(missing)
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description=(
            "Exercise the CricScore add-player form using CSV rows without "
            "creating player records."
        )
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Close the browser automatically after the test completes.",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parents[1]
    rows = _read_test_data(project_root / "data" / "player_form_test_data.csv")
    environment = dotenv_values(project_root / ".env")
    access_pin = _required_pin(environment, "CRICSCORE_ACCESS_PIN", 5)
    admin_pin = _required_pin(environment, "CRICSCORE_ADMIN_PIN", 4)

    access_objects = load_repository(ACCESS_URL)
    app_objects = load_repository(HOME_URL)
    _require_object_repository(access_objects, ("_input", "enter_button"))
    _require_object_repository(
        app_objects,
        (
            "manage_players_button",
            "admin_pin_inputs",
            "admin_verify_button",
            "add_player_button",
            "player_name_input",
            "player_role_buttons",
            "player_form_dropdowns",
        ),
    )

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=args.headless)
        try:
            page = browser.new_page()
            page.goto(ACCESS_URL, wait_until="domcontentloaded")
            access_repository = ObjectRepositoryPage(page, access_objects)
            app_repository = ObjectRepositoryPage(page, app_objects)

            access_repository.fill_pin("_input", access_pin, reverse=True)
            access_repository.click("enter_button")
            try:
                page.wait_for_url(HOME_URL, timeout=15000)
            except TimeoutError as error:
                message = " ".join(page.locator("body").inner_text().split())
                raise RuntimeError(
                    "Access PIN was not accepted. "
                    f"Page message: {message[:250]!r}"
                ) from error

            app_repository.click("manage_players_button")
            admin_inputs = app_repository.locator("admin_pin_inputs")
            admin_inputs.first.wait_for(state="visible", timeout=15000)
            app_repository.fill_pin(
                admin_inputs, admin_pin, reverse=False
            )

            verify_button = app_repository.locator("admin_verify_button")
            if verify_button.count():
                verify_button.click()
            page.get_by_text("// ADMIN PANEL", exact=True).wait_for(
                state="visible", timeout=15000
            )

            app_repository.click("add_player_button")
            page.get_by_text("// ADD NEW PLAYER", exact=True).wait_for(
                state="visible", timeout=15000
            )

            name_input = app_repository.locator("player_name_input")
            role_buttons = app_repository.locator("player_role_buttons")
            dropdowns = app_repository.locator("player_form_dropdowns")
            if dropdowns.count() != 3:
                raise AssertionError(
                    f"Expected 3 player form dropdowns, found {dropdowns.count()}"
                )

            for row_number, row in enumerate(rows, start=1):
                name_input.fill(row["player_name"])
                selected_role = role_buttons.filter(
                    has_text=row["role"]
                )
                if selected_role.count() != 1:
                    raise AssertionError(
                        f"CSV row {row_number}: expected one role button for "
                        f"{row['role']!r}"
                    )
                selected_role.click()
                expect(selected_role).to_have_attribute("aria-pressed", "true")

                dropdowns.nth(0).select_option(value=row["batting_hand"])
                dropdowns.nth(1).select_option(value=row["bowling_hand"])
                dropdowns.nth(2).select_option(value=row["bowling_style"])

                if name_input.input_value() != row["player_name"]:
                    raise AssertionError(
                        f"CSV row {row_number}: player name did not remain in the form"
                    )
                selected_values = [
                    dropdowns.nth(index).input_value() for index in range(3)
                ]
                expected_values = [
                    row["batting_hand"],
                    row["bowling_hand"],
                    row["bowling_style"],
                ]
                if selected_values != expected_values:
                    raise AssertionError(
                        f"CSV row {row_number}: selected form values did not match CSV"
                    )

                print(
                    f"Verified CSV row {row_number}/{EXPECTED_ROWS}: "
                    f"{row['player_name']} ({row['role']})"
                )

            print(
                f"PASS: verified all {EXPECTED_ROWS} CSV combinations. "
                "No player records were submitted or created."
            )
            if not args.headless:
                print("Review the open form, then close the browser window.")
                page.wait_for_event("close")
        finally:
            browser.close()


if __name__ == "__main__":
    main()
