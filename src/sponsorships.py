import json
from requests import Session
import src.util as util
from typing import TypedDict

class SponsorAPIData(TypedDict):
	adId: int
	adSetId: int
	adName: str
	adStatus: str
	creativeType: str
	creativeTargetId: int
	creativeUrl: str
	bidAmountInRobux: int
	budgetInRobux: int
	adSetStatus: str
	startDate: str
	endDate: str
	targetGender: str
	targetAgeBracket: str
	targetDeviceType: str
	campaignTargetType: str
	campaignTargetId: int
	totalSpendInRobux: int
	totalImpressions: int
	totalClicks: int
	totalConversions: int
	impressionConversions: int
	clickConversions: int

class SponsorAPIResponse(TypedDict):
	sponsoredGames: list[SponsorAPIData]
	previousPageCursor: str | None
	nextPageCursor: str | None

class CampaignData(TypedDict):
	target_type: str
	target_id: int
	device: str

class SponsorTargeting(TypedDict):
	gender: list[str]
	age: list[str]
	device: list[str]

class SponsorTime(TypedDict):
	start: str
	end: str

class SponsorData(TypedDict):
	title: str
	id: int
	status: str
	bid: int
	budget: int
	clicks: int
	impressions: int
	target: SponsorTargeting
	time: SponsorTime

def get_sponsor_data(session: Session, place_id: int) -> SponsorAPIResponse:
	universe_id = util.get_universe_id(session, place_id)
	response = session.get(
		url=f"https://adconfiguration.roblox.com/v2/sponsored-games?universeId={universe_id}&includeReportingStats=true",
		headers={},
	)
	data = json.loads(response.text)
	return data

def get_sponsors(session: Session, place_id: int) -> list[SponsorData]:
	out = []

	api_response = get_sponsor_data(session, place_id)

	for sponsor_api_data in api_response["sponsoredGames"]:

		data: SponsorData = {
			"title": sponsor_api_data["adName"],
			"id": sponsor_api_data["adId"],
			"status": sponsor_api_data["adSetStatus"],
			"bid": sponsor_api_data["bidAmountInRobux"],
			"budget": sponsor_api_data["budgetInRobux"],
			"impressions": sponsor_api_data["totalImpressions"],
			"impression_conversions": sponsor_api_data["impressionConversions"],
			"clicks": sponsor_api_data["totalClicks"],
			"click_conversions": sponsor_api_data["clickConversions"],
			"target": {
				"gender": sponsor_api_data["targetGender"].split(","),
				"age": sponsor_api_data["targetAgeBracket"].split(","),
				"device": sponsor_api_data["targetDeviceType"].split(","),
			},
			"time": {
				"start": sponsor_api_data["startDate"],
				"end": sponsor_api_data["endDate"],
			},
		}
		out.append(data)


	return out