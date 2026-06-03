#!/usr/bin/env python3
"""
Парсинг сайта ijiza.ru — модели, рецепты, статьи, технологии.
Использует httpx + BeautifulSoup.
"""

import asyncio
import json
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://ijiza.ru"
OUTPUT_DIR = Path("docs/research/ijiza/site")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}


async def fetch(client: httpx.AsyncClient, url: str) -> str:
    resp = await client.get(url, headers=HEADERS, follow_redirects=True)
    resp.raise_for_status()
    return resp.text


async def parse_catalog(client: httpx.AsyncClient):
    """Парсинг каталога продукции."""
    print("Parsing catalog...")
    html = await fetch(client, f"{BASE_URL}/catalog/")
    soup = BeautifulSoup(html, "html.parser")
    
    products = []
    for item in soup.find_all("a", href=True):
        href = item["href"]
        if "/catalog/" in href and href != "/catalog/":
            products.append({
                "url": f"{BASE_URL}{href}",
                "title": item.get_text(strip=True),
            })
    
    print(f"Found {len(products)} catalog items")
    
    # Parse each product page
    for product in products:
        try:
            html = await fetch(client, product["url"])
            soup = BeautifulSoup(html, "html.parser")
            
            # Extract description
            desc = soup.find("meta", attrs={"name": "description"})
            product["description"] = desc["content"] if desc else ""
            
            # Extract text content
            content = soup.find("main") or soup.find("article") or soup.find("div", class_="content")
            if content:
                product["text"] = content.get_text(separator="\n", strip=True)[:5000]
            
            await asyncio.sleep(1)  # Rate limit
        except Exception as e:
            print(f"Error parsing {product['url']}: {e}")
    
    return products


async def parse_recipes(client: httpx.AsyncClient):
    """Парсинг рецептов."""
    print("Parsing recipes...")
    html = await fetch(client, f"{BASE_URL}/recipes/")
    soup = BeautifulSoup(html, "html.parser")
    
    recipes = []
    for item in soup.find_all("a", href=True):
        href = item["href"]
        if "/recipes/" in href and href != "/recipes/":
            recipes.append({
                "url": f"{BASE_URL}{href}",
                "title": item.get_text(strip=True),
            })
    
    print(f"Found {len(recipes)} recipes")
    
    for recipe in recipes:
        try:
            html = await fetch(client, recipe["url"])
            soup = BeautifulSoup(html, "html.parser")
            
            content = soup.find("article") or soup.find("main") or soup.find("div", class_="content")
            if content:
                recipe["text"] = content.get_text(separator="\n", strip=True)[:10000]
            
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error parsing {recipe['url']}: {e}")
    
    return recipes


async def parse_articles(client: httpx.AsyncClient):
    """Парсинг статей / информации."""
    print("Parsing articles...")
    
    urls = [
        f"{BASE_URL}/information/recommendation/gorjacee-kopchenie/standart-programs/",
        f"{BASE_URL}/information/recommendation/gorjacee-kopchenie/programmy-goryachego-kopcheniya-panel-izhitca-z115/",
        f"{BASE_URL}/technology/cold_smoking/",
    ]
    
    articles = []
    for url in urls:
        try:
            html = await fetch(client, url)
            soup = BeautifulSoup(html, "html.parser")
            
            title = soup.title.string if soup.title else url
            content = soup.find("article") or soup.find("main")
            
            articles.append({
                "url": url,
                "title": title,
                "text": content.get_text(separator="\n", strip=True)[:15000] if content else "",
            })
            
            await asyncio.sleep(1)
        except Exception as e:
            print(f"Error parsing {url}: {e}")
    
    return articles


async def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    async with httpx.AsyncClient(timeout=30.0) as client:
        catalog = await parse_catalog(client)
        recipes = await parse_recipes(client)
        articles = await parse_articles(client)
    
    # Save results
    (OUTPUT_DIR / "catalog.json").write_text(
        json.dumps(catalog, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    (OUTPUT_DIR / "recipes.json").write_text(
        json.dumps(recipes, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    (OUTPUT_DIR / "articles.json").write_text(
        json.dumps(articles, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    
    print(f"\nDone!")
    print(f"  Catalog: {len(catalog)} items")
    print(f"  Recipes: {len(recipes)} items")
    print(f"  Articles: {len(articles)} items")
    print(f"  Output: {OUTPUT_DIR}")


if __name__ == "__main__":
    asyncio.run(main())
