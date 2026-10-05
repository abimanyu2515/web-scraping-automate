This is a sample app that is used to scrape web pages and store the elements in an object repository

## Application Building Context

Read the following files in order before implementing or making any architectural decision:

1. `context/progress-tracker.md` — current phase, completed work, open questions, and next steps

## 🛑 Boundaries & Do Not Touch
* NEVER modify `.env` or `.env.local` files.
* DO NOT edit files in the `.venv/` or `__pycache__` directory; it is auto-generated.
* NEVER modify `requirements.txt` directly; only modify it via `npm install`.

## 📁 Project Structure
```
web-scrapping-automate/
   ├──.env
   ├──.venv
   ├──.gitignore
   ├── data/
   │   ├── object-repository.json
   ├── AGENTS.md
   ├── main.py
   ├── parser.py
   ├── repository.py          
   ├── requirements.txt
   └── scraper.py
```



- `src/data/` - Contains the json data for object repository.
- `main.py` - the main file that executes the parser and scraper
- `parser.py` - the html parsing file
- `scraper.py` - the file containing scraping functions
- requirements.txt - file containing dependencies and libraries are/need to be installed