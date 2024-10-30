import cloudscraper
from pyquery import PyQuery as pq
from flask import Flask, request, jsonify
import urllib.parse
import asyncio

app = Flask(__name__)

async def search(query, page=1):
    scraper = cloudscraper.create_scraper()
    encoded_query = urllib.parse.quote(query)
    url = f"https://nekopoi.care/search/{encoded_query}/page/{page}"
    response = scraper.get(url)
    data = response.text
    document = pq(data)
    
    result = document("div.result > ul > li").map(lambda i, el: {
        'title': pq(el).find("div.top > h2 > a").text().strip(),
        'link': pq(el).find("div.top > h2 > a").attr("href"),
        'image': pq(el).find("div.limitnjg > img").attr("src"),
        'genre': pq(el).find("div.desc > p").eq(3).text().replace("Genre :", "").strip(),
        'producers': pq(el).find("div.desc > p").eq(5).text().replace("Producers :", "").strip(),
        'duration': pq(el).find("div.desc > p").eq(6).text().replace("Duration :", "").strip(),
        'size': pq(el).find("div.desc > p").eq(7).text().replace("Size :", "").strip(),
    })
    
    return result

async def detail(url):
    scraper = cloudscraper.create_scraper()
    response = scraper.get(url)
    data = response.text
    document = pq(data)
    result = {}

    result['title'] = document("div.eropost > div.eroinfo > h1").text().strip()
    result['info'] = document("div.eropost > div.eroinfo > p").text().strip()
    result['img'] = document("div.contentpost > div.thm > img").attr("src")

    for element in document(".konten p"):
        text = pq(element).text()
        if "Genre" in text:
            result['genre'] = text.replace("Genre", "").replace(":", "").strip()
        elif "Sinopsis" in text:
            result['sinopsis'] = pq(element).next().text().replace(":", "").strip()
        elif "Anime" in text:
            result['anime'] = text.replace("Anime", "").replace(":", "").strip()
        elif "Producers" in text:
            result['producers'] = text.replace("Producers", "").replace(":", "").strip()
        elif "Duration" in text:
            result['duration'] = text.replace("Duration", "").replace(":", "").strip()
        elif "Size" in text:
            result['size'] = text.replace("Size", "").replace(":", "").strip()

    result['stream'] = document("div#stream1 > iframe").attr("src")
    result['download'] = []

    for box in document("div.arealinker > div.boxdownload > div.liner"):
        title = pq(box).find("div.name").text().strip()
        type_match = pq(box).find("div.name").text().strip().split('[')[-1].rstrip(']')
        type_ = type_match if type_match else None

        links = []
        for link in pq(box).find("div.listlink > p a"):
            links.append({
                'name': pq(link).text().strip(),
                'link': pq(link).attr("href"),
            })

        result['download'].append({
            'type': type_,
            'title': title,
            'links': links,
        })

    return result

@app.route('/search', methods=['GET'])
def search_route():
    query = request.args.get('query')
    page = request.args.get('page', default=1, type=int)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    results = loop.run_until_complete(search(query, page))
    return jsonify(results)

@app.route('/detail', methods=['GET'])
def detail_route():
    url = request.args.get('url')
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(detail(url))
    return jsonify(result)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)