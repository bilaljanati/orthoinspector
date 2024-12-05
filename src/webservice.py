import requests


class WebService:
    def _fetch(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            return None
        return response.json()
