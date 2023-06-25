import json
from datetime import datetime, timedelta
from requests import Session
from typing import TypedDict, Literal, Any
import src.util as util

StatType = Literal["Visits", "PremiumVisits", "PremiumPayout"]
GranularityType = Literal["Hourly", "Daily","Monthly"]
DivisionType=Literal["Age", "Platform"]
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.000Z"
class LivePlayerDeviceData(TypedDict):
	Computer:int
	Tablet:int
	Phone:int
	Console:int

class LiveStatData(TypedDict):
	totalPlayerCount:int
	playerCountsByDeviceType:LivePlayerDeviceData
	gameCount:int

def get_live_stat_data(session: Session, place_id: int) -> LiveStatData:
	universe_id = util.get_universe_id(session, place_id)
	response = session.get(f"https://develop.roblox.com/v1/universes/{universe_id}/live-stats")
	return json.loads(response.text)

DeviceStatusType = Literal["Unknown", "Good", "Bad"]

class DeviceCompatData(TypedDict):
	status: DeviceStatusType
	platformName: str
	crashRatePercentage: Literal["NaN"] | float

class CompatibilityData(TypedDict):
	Compatibilities: list[DeviceCompatData]

def get_compatibility_data(session: Session, place_id: int) -> CompatibilityData:
	universe_id = util.get_universe_id(session, place_id)
	response = session.get(f"https://develop.roblox.com/v1/universes/{universe_id}/compatibilities")
	return json.loads(response.text)

class DevStatDataSection(TypedDict):
	type: str
	data: dict[str, float]

class DevStatData(TypedDict):
	placeId: int
	dataType: int
	dataGranularity: int
	startTime: str
	endTime: str
	data: dict[str, DevStatDataSection]

def get_dev_stat_data(
	session: Session, 
	place_id: int, 
	stat_type: StatType, 
	granularity_type: GranularityType, 
	division_type: DivisionType
) -> DevStatData:
	response = session.get(f"https://develop.roblox.com/v1/places/{place_id}/stats/{stat_type}?granularity={granularity_type}&divisionType={division_type}")
	return json.loads(response.text)


def get_data(session: Session, place_id: int) -> dict:
	end_time: datetime = datetime.now()
	start_time: datetime = end_time - timedelta(minutes=60) #interval)

	def get_final_data_point(stat_type: StatType, division_type: DivisionType) -> Any:
		data = get_dev_stat_data(
			session=session,
			place_id=place_id,
			stat_type=stat_type,
			granularity_type="Hourly",
			division_type=division_type
		)

		out = {
			# "data": data
		}
		for name, data_table in data["data"].items():
			max_tick = 0
			final_val: Any | None = None
			for tick, val in data_table["data"].items():
				tick_val = int(tick)
				if tick_val > max_tick:
					max_tick = tick_val
					final_val = val

			out[name] = final_val

		return out
	
	out = {
		"visits": {
			"age": get_final_data_point(
				division_type="Age",
				stat_type="Visits",
			),
			"platform": get_final_data_point(
				division_type="Platform",
				stat_type="Visits",
			),
		},
		"premium": {
			"visits": {
				"age": get_final_data_point(
					division_type="Age",
					stat_type="PremiumVisits",
				),
				"platform": get_final_data_point(
					division_type="Platform",
					stat_type="PremiumVisits",
				),
			},
			"payout": {
				"age": get_final_data_point(
					division_type="Age",
					stat_type="PremiumPayout",
				),
				"platform": get_final_data_point(
					division_type="Platform",
					stat_type="PremiumPayout",
				),
			},
		},
	}
	return out
