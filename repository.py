import json
import os


def save_repository(elements, url=None):

    os.makedirs("data", exist_ok=True)

    file_path = "data/object_repository.json"

    # Load existing repo if it exists (backward compatibility with list format)
    repo = {}
    if os.path.exists(file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            content = json.load(file)
            if isinstance(content, list):
                # Convert old list format to new dict format keyed by name
                for item in content:
                    name = item.get("name", "")
                    if name:
                        repo[name] = item
                    else:
                        repo[f"element_{len(repo)}"] = item
            elif isinstance(content, dict):
                repo = content

    # Convert elements list to dict keyed by "name" if needed
    elements_dict = {}
    if isinstance(elements, list):
        for item in elements:
            name = item.get("name", "")
            if name:
                elements_dict[name] = item
            else:
                elements_dict[f"element_{len(elements_dict)}"] = item
    else:
        elements_dict = elements

    # Structure: {url: { "elements": {name: {...}} }}
    if url:
        if url not in repo:
            repo[url] = {"elements": {}}
        repo[url]["elements"].update(elements_dict)
    else:
        # If no URL, merge at root level
        repo.update(elements_dict)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(repo, file, indent=4, ensure_ascii=False)

    print(f"Object Repository saved to: {file_path}")


def load_repository(url=None):

    file_path = "data/object_repository.json"

    if not os.path.exists(file_path):
        return {}

    with open(file_path, "r", encoding="utf-8") as file:
        content = json.load(file)

    if url:
        return content.get(url, {}).get("elements", {})
    
    # No URL: return all elements
    # Handle new format: {url: {"elements": {...}}}
    if isinstance(content, dict):
        # Check if content has URL keys (each with "elements" sub-key)
        for key in content:
            if isinstance(content[key], dict) and "elements" in content[key]:
                # New format: merge all elements from all URLs
                all_elements = {}
                for url_key, url_data in content.items():
                    elements = url_data.get("elements", {})
                    all_elements.update(elements)
                return all_elements
        
        # Check if content is name->element format (old format or single page)
        # If first value has "name" key, it's element format
        if content and isinstance(list(content.values())[0], dict) and "name" in list(content.values())[0]:
            return content
        
        # Default: try to return elements if present
        if "elements" in content:
            return content["elements"]
    
    return content if isinstance(content, dict) else {}