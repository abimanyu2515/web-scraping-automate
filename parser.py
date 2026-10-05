from bs4 import BeautifulSoup

def generate_name(element):
    text = element.get_text(" ", strip=True).lower()
    tag = element.name

    # Use HTML name attribute if available and text is empty
    html_name = element.get("name")
    if html_name and not text:
        text = html_name.lower()

    suffix_map = {
        "button": "_button",
        "input": "_input",
        "a": "_link",
        "select": "_select",
        "textarea": "_textarea",
    }

    suffix = suffix_map.get(tag, "")

    name = text.replace(" ", "_")
    if suffix and not name.endswith(suffix):
        name += suffix

    return name


def generate_css_selector(element, soup):
    # 1. ID is usually the best locator
    element_id = element.get("id")

    if element_id:
        return f"#{element_id}"

    # 2. Name attribute
    name = element.get("name")

    if name:
        selector = f'{element.name}[name="{name}"]'

        if len(soup.select(selector)) == 1:
            return selector

    # 3. Class-based selector
    classes = element.get("class", [])

    if classes:
        # Filter out classes containing ':' (e.g., Tailwind focus:outline-none)
        # as they cannot be used as regular CSS class selectors
        classes = [c for c in classes if ":" not in c]

        if classes:
            selector = element.name + "".join(
                f".{class_name}" for class_name in classes
            )

            if len(soup.select(selector)) == 1:
                return selector

    # 4. Fallback
    return element.name

def extract_elements(html):
    soup = BeautifulSoup(html, "html.parser")

    elements = soup.find_all([
        "input",
        "button",
        "a",
        "select",
        "textarea"
    ])

    repository = []

    for index, element in enumerate(elements, start=1):

        selector = generate_css_selector(element, soup)
        name = generate_name(element)

        data = {
            "name": name,
            "tag": element.name,
            "text": element.get_text(" ", strip=True),
            "id_attribute": element.get("id"),
            "locator_type": "css",
            "locator": selector,
            "html_id": element.get("id"),
            "class": element.get("class"),
            "name_attribute": element.get("name"),
            "type": element.get("type"),
            "placeholder": element.get("placeholder"),
            "href": element.get("href")
        }

        repository.append(data)

    return repository