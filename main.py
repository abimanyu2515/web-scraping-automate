from scraper import fetch_page
from parser import extract_elements
from repository import save_repository, load_repository


url = "https://cricscore-wheat.vercel.app/access"

html = fetch_page(url)

if html:

    elements = extract_elements(html)

    print("Elements extracted:", len(elements))

    save_repository(elements, url)

    # Load and print repository structure
    repo = load_repository(url)
    print("Repository keys:", list(repo.keys()) if repo else "empty")
    
else:
    print("Failed to fetch webpage.")