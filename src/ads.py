from requests import Session
import json
import src.util as util
from typing import TypedDict

GAME_URL_PREFIX = "https://www.roblox.com/games/"

class IntCurTotalData(TypedDict):
	current: int
	total: int
class FloatCurTotalData(TypedDict):
	current: float
	total: float

class AdData(TypedDict):
	title: str
	id: int
	type: str
	is_running: bool
	clicks: IntCurTotalData
	ctr: FloatCurTotalData
	impressions: IntCurTotalData
	cpc: FloatCurTotalData
	bid: IntCurTotalData

def get_ads(session: Session, place_id: int, group_id: int) -> list[AdData]:
	ad_url = ""
	is_in_group = True
	if is_in_group:
		ad_url = f"https://www.roblox.com/develop/groups/{group_id}?Page=ads"
	else:
		ad_url = "https://www.roblox.com/develop?Page=ads"
	
	response = session.get(ad_url)
	tree = util.get_html_tree(response.text)

	ads: list[AdData] = []

	for tabl in tree.xpath('//table[@data-ad-type]'):
		# get title
		ad_id = tabl.get("data-item-id")
		ad_type = tabl.get("data-ad-type")
		ad_place_id: int
		ad_title: str
		for title in tabl.xpath('.//td[@colspan="6"]'):
		
			for span in title.xpath(".//span[not(@href) and @class='title']"):
				ad_title = span.text

			for a in title.xpath('.//a[@href]'):
				a_url = a.get("href")
				if GAME_URL_PREFIX in a_url:
					url_end = a_url.replace(GAME_URL_PREFIX, "")
					ad_place_id = int(url_end.split("/")[0])

		# get stats
		clicks: int
		total_clicks: int
		ctr: float
		total_ctr: float
		bid: int
		total_bid: int
		impressions: int
		total_impressions: int
		is_running: bool = len(tabl.xpath("//*[text()='Not running']")) == 0
		for stats in tabl.xpath('.//td[@class="stats-col"]'):
			for div in stats.xpath(".//div[not(@title) and @class='totals-label']"):
				for span in div.xpath(".//span"):
					if "Clicks" in div.text:
						clicks = int(span.text)
					elif "Bid" in div.text:
						bid = int(span.text)
					elif "CTR" in div.text:
						ctr = float(span.text.replace("%", ""))/100
					elif "Impressions" in div.text:
						impressions = int(span.text)

			for div in stats.xpath(".//div[@title and @class='totals-label']"):
				for span in div.xpath(".//span"):
					if "Clicks" in div.text:
						total_clicks = int(span.text)
					elif "Bid" in div.text:
						total_bid = int(span.text)
					elif "CTR" in div.text:
						total_ctr = float(span.text.replace("%", ""))/100
					elif "Impr" in div.text:
						total_impressions = int(span.text)

		ad_data: AdData = {
			"title": ad_title,
			"id": ad_id,
			"type": ad_type,
			"is_running": is_running,
			"clicks": {
				"current": clicks,
				"total": total_clicks,
			},
			"ctr": {
				"current": ctr,
				"total": total_ctr,
			},
			"bid": {
				"current": bid,
				"total": total_bid,
			},
			"impressions": {
				"current": impressions,
				"total": total_impressions,
			},
			"cpc": {
				"current": float(bid)/float(max(clicks,1)),
				"total": float(total_bid)/float(max(total_clicks,1)),
			},
		}
		if place_id == ad_place_id:
			ads.append(ad_data)

	return ads

