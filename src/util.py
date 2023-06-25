from bs4 import BeautifulSoup as htmlparser
import json
from datetime import datetime
from lxml.html import HtmlElement
from lxml import html
from requests import Session

def get_universe_id(session: Session, place_id: int) -> int:
	response = session.get(f"https://games.roblox.com/v1/games/multiget-place-details?placeIds={place_id}")
	for place in json.loads(response.text):
		universe_id = int(place["universeId"])
		assert universe_id
		return universe_id
	raise ValueError("Bad response: "+response.text)
	
# def get_if_owner_is_group(session: Session, place_id: int) -> bool:
# 	return False

# def get_owner_id(session: Session, place_id: int) -> int:
# 	return 42223924

def dump_element(element) -> str:
	return (html.tostring(element)).decode('utf-8')

def get_html_tree(tree_content: str) -> HtmlElement:
	return html.fromstring(tree_content)

def get_xcrf_token(session: Session) -> str:
	response = session.post("https://auth.roblox.com/v2/logout")
	token = response.headers["x-csrf-token"]
	assert token
	return token