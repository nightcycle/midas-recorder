from lxml import html
import json
from requests import Session
import src.util as util
from typing import TypedDict

class RatingData(TypedDict):
	likes: int
	dislikes: int

class InfoData(TypedDict):
	rating: RatingData
	favorites: int
	visits: int
	concurrents: int

GAME_URL_PREFIX = "https://www.roblox.com/games/"

def get_concurrents(session: Session, place_id: int) -> int: 
	response = session.get(GAME_URL_PREFIX+str(place_id))
	tree = html.fromstring(response.text)
	
	try:
		for element in tree.xpath("//li[@class='game-stat game-stat-width-voice']"):
			for stat in element.xpath(".//p[@class='text-label text-overflow font-caption-header']"):
				if stat.text == "Active":
					for val in element.xpath(".//p[@class='text-lead font-caption-body wait-for-i18n-format-render invisible']"):
						return int(val.text.replace(",", ""))
	except:
		return 0

	return 0
	
def get_game_stats(session: Session, place_id: int) -> InfoData:
	universe_id = util.get_universe_id(session, place_id)

	# get like / dislike
	for entry in json.loads(session.get(f"https://games.roblox.com/v1/games/votes?universeIds={universe_id}").text)["data"]:
		if entry["id"] == universe_id:
			likes = entry["upVotes"]
			dislikes = entry["downVotes"]

	# get favorites
	favorites = json.loads(session.get(f"https://games.roblox.com/v1/games/{universe_id}/favorites/count").text)["favoritesCount"]
	
	# parse for concurrents and visits
	response = session.get(GAME_URL_PREFIX+str(place_id))
	tree = html.fromstring(response.text)

	# get visits
	for element in tree.xpath("//p[@id='game-visit-count']"):
		visits = int(element.get("title").replace(",", ""))

	concurrents = get_concurrents(session, place_id)

	return {
		"rating": {
			"likes": likes,
			"dislikes": dislikes,
		},
		"favorites": favorites,
		"visits": visits,
		"concurrents": concurrents,
	}
