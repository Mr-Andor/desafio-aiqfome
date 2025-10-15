from elasticsearch import Elasticsearch, helpers
import requests

es = Elasticsearch("http://localhost:9200")
resp = requests.get("https://fakestoreapi.com/products")
docs = resp.json()

actions = [
    {
        "_index": "products",
        "_id": product["id"],
        "_source": product,
    }
    for product in docs
]
helpers.bulk(es, actions)
