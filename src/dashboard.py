import sys
import json
from requests import Session
import requests
from datetime import datetime, timedelta
import src.util as util
from src.devstat import GranularityType
from typing import TypedDict, Literal, Any


# 2023-06-24T12%3A53%3A48.000Z
TIME_FORMAT = "%Y-%m-%dT%H:%M:%S.000Z"

KPIType = Literal[
	"W1Retention","D1Retention", "D7Retention", "D30Retention", "D1Stickyness", "D7Stickyness","D30Stickyness",
	"Visits", "MonthlyActiveUsers", "TotalHours", "AveragePlayTime", "NewUsers", "AveragePlayTime", "DailyActiveUsers", 
	"Robux", "ConversionRate", "PayingUsers", "ARPPU", "PayingUsers", "ARPU"
]

class QueryBreakdownData(TypedDict):
	dimension: str
	value: str

class QueryDatapointData(TypedDict):
	timestamp: str
	value: float

class QueryData(TypedDict):
	breakdowns: list[QueryBreakdownData]
	datapoints: list[QueryDatapointData]

class QueryResponseData(TypedDict):
	values: list[QueryData]


def get_benchmark_data(
	session: Session, 
	place_id: int, 
	granularity_type: GranularityType,
	kpi_type: KPIType, 
	start_time: datetime, 
	end_time: datetime
) -> QueryResponseData:

	universe_id = util.get_universe_id(session, place_id)

	response = session.get(
		url=f"https://apis.roblox.com/developer-analytics-aggregations/v1/get-similar-benchmarks/universes/{universe_id}",
		params={
			"kpiType":kpi_type,
			"granularity": granularity_type,
			"startTime":start_time.strftime(TIME_FORMAT),
			"endTime":end_time.strftime(TIME_FORMAT),
		},
	)
	data = json.loads(response.text)
	return data

BreakdownType = Literal["DeviceType", "OperatingSystem", "AgeGroup", "Country", "Locale", "Total"]
class DashboardValueSet(TypedDict):
	dataDivisionTargetValue: str
	data: dict[str, None | float]

class DashboardTopLevelMetricData(TypedDict):
	average: float
	total: float

class DashboardData(TypedDict):
	universeId: int
	kpiType: KPIType
	granularity: int
	breakdownType: BreakdownType
	startTime: str
	endTime: str
	values: list[DashboardValueSet]
	topLevelMetrics: DashboardTopLevelMetricData

def get_data(
	session: Session, 
	place_id: int, 
	break_down_type: BreakdownType, 
	kpi_type: KPIType, 
	start_time: datetime, 
	end_time: datetime
) -> dict:
	universe_id = util.get_universe_id(session, place_id)
	session.headers["Content-Type"] = "application/json-patch+json"

	payload = {
		"universeId": universe_id,
		"kpiType": kpi_type,
		"queryFilter": {
			"breakdownType": break_down_type,
		},
		"aggregationStartDateTime": start_time.strftime(TIME_FORMAT),
		"aggregationEndDateTime": end_time.strftime(TIME_FORMAT),
	}

	path_url = f"https://apis.roblox.com/developer-analytics-aggregations/v1/universes/{universe_id}/breakdown"
	# print("\n", path_url)
	# print(payload)

	response = session.post(
		url = path_url,
		data=json.dumps(payload),
	)
	session.headers.pop("Content-Type")

	dashboard_data: DashboardData = json.loads(response.text)

	out = {}

	for value_data in dashboard_data["values"]:
		key = value_data["dataDivisionTargetValue"]
		max_datetime: datetime | None = None
		max_val: float | None = None
		for ts, val in value_data["data"].items():
			ts_datetime = datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")
			if max_datetime == None:
				max_datetime = ts_datetime
				max_val = val
			else:
				assert max_datetime != None
				certified_datetime: Any = max_datetime
				if certified_datetime > ts_datetime:
					max_datetime = ts_datetime
					max_val = val

		out[key.lower()] = max_val
	
	return out

PlatformFilter = Literal["Computer", "Phone", "Tablet"]
AcquisitionMetric = Literal["GameDetails", "Impressions", "DirectJoins", "GameDetailsJoins", "PlaySessions", "NewUsers", "ImpressionUniqueSessions", "GameDetailsUniqueSessions", "UniqueSessions"]
AcquisitionFilterValue = Literal["Organic", "Home"]
AcquisitionGranularity = Literal["OneDay"]

def get_aquisition_data(
	session: Session, 
	place_id: int,
	metric: AcquisitionMetric,
	start_time: datetime, 
	end_time: datetime,
	filters: list[AcquisitionFilterValue] = [],
	platform: PlatformFilter | None = None,
	granularity: AcquisitionGranularity = "OneDay"
) -> QueryResponseData:


	filter_data: list[dict] = []

	if len(filters) > 0:
		filter_data.append({
			"dimension": "Source",
			"values": filters,
		})

	if platform != None:
		filter_data.append({
			"dimension": "Platform",
			"values": [
				platform
			]
		})

	body_data = {
		"metric": metric,
		"granularity": granularity,
		"startTime": start_time.strftime(TIME_FORMAT),
		"endTime": end_time.strftime(TIME_FORMAT),
		"breakdown": [
			"Source"
		],
		"filters": filter_data
	}

	# print(json.dumps(body_data, indent=5))

	universe_id = util.get_universe_id(session, place_id)
	session.headers["Content-Type"] = "application/json-patch+json"
	response = session.post(
		url = f"https://apis.roblox.com/developer-analytics-aggregations/v1/metrics/user-acquisition/universes/{universe_id}",
		data=json.dumps(body_data),
	)
	session.headers.pop("Content-Type")
	return json.loads(response.text)

def record_data(session: Session, place_id: int, interval: int) -> dict:
	end_time: datetime = datetime.now()
	start_time: datetime = end_time - timedelta(minutes=60*24) #interval)

	def dump_kpi_data(kpi_type: KPIType) -> dict:
		out = {
			"device_type": get_data(
				session=session,
				place_id=place_id,
				break_down_type="DeviceType",
				kpi_type=kpi_type,
				start_time=start_time,
				end_time=end_time,
			),
			"os": get_data(
				session=session,
				place_id=place_id,
				break_down_type="OperatingSystem",
				kpi_type=kpi_type,
				start_time=start_time,
				end_time=end_time,
			),
			"age_group": get_data(
				session=session,
				place_id=place_id,
				break_down_type="AgeGroup",
				kpi_type=kpi_type,
				start_time=start_time,
				end_time=end_time,
			),
			"country": get_data(
				session=session,
				place_id=place_id,
				break_down_type="Country",
				kpi_type=kpi_type,
				start_time=start_time,
				end_time=end_time,
			),		
			"locale": get_data(
				session=session,
				place_id=place_id,
				break_down_type="Locale",
				kpi_type=kpi_type,
				start_time=start_time,
				end_time=end_time,
			),	
			"total": get_data(
				session=session,
				place_id=place_id,
				break_down_type="Total",
				kpi_type=kpi_type,
				start_time=start_time,
				end_time=end_time,
			),	
		}
		return out

	# def dump_benchmark_data(kpi_type: KPIType) -> Any:
	# 	# out = {}
	# 	# for granularity_type in ["OneDay"]:
	# 	# 	out[granularity_type] = 
	# 	return get_benchmark_data(
	# 		session=session,
	# 		place_id=place_id, 
	# 		granularity_type="Daily", 
	# 		kpi_type=kpi_type,
	# 		start_time=end_time - timedelta(minutes=60*24),
	# 		end_time=end_time,
	# 	)

	def dump_aquisition_data(metric_type: AcquisitionMetric) -> dict:
		out = {}

		for platform_filter in ["Computer", "Phone", "Tablet"]:
			p_filter: Any = platform_filter
			aquisition_data = get_aquisition_data(
				session=session,
				place_id=place_id, 
				start_time=start_time,
				end_time=end_time,
				metric=metric_type,
				granularity = "OneDay",
				filters=["Organic", "Home"],
				platform=p_filter,

			)
			src_data = {}
			for value_data in aquisition_data["values"]:
				breakdown_value = value_data["breakdowns"][0]["value"]
				src_data[breakdown_value.lower()] = value_data["datapoints"][0]["value"]

			out[platform_filter.lower()] = src_data
		return out

	return {
		"kpi": {
			"w1_rr": dump_kpi_data("W1Retention"),
			"d1_rr": dump_kpi_data("D1Retention"),
			"d7_rr": dump_kpi_data("D7Retention"),
			"d30_rr": dump_kpi_data("D30Retention"),
			"d1_stick": dump_kpi_data("D1Stickyness"),
			"d7_stick": dump_kpi_data("D7Stickyness"),
			"d30_stick": dump_kpi_data("D30Stickyness"),
			"visits": dump_kpi_data("Visits"),
			"mau": dump_kpi_data("MonthlyActiveUsers"),
			"total_hours": dump_kpi_data("TotalHours"),
			"avg_play_time": dump_kpi_data("AveragePlayTime"),
			"new_users": dump_kpi_data("NewUsers"),
			"avg_play_time": dump_kpi_data("AveragePlayTime"),
			"dau": dump_kpi_data("DailyActiveUsers"),
			"robux": dump_kpi_data("Robux"),
			"conversion_rate": dump_kpi_data("ConversionRate"),
			"paying_users": dump_kpi_data("PayingUsers"),
			"arppu": dump_kpi_data("ARPPU"),
			"paying_users": dump_kpi_data("PayingUsers"),
			"arpu": dump_kpi_data("ARPU"),
		},
		# "benchmarks": {
		# 	"w1_rr": dump_benchmark_data("W1Retention"),
		# 	"d1_rr": dump_benchmark_data("D1Retention"),
		# 	"d7_rr": dump_benchmark_data("D7Retention"),
		# 	"d30_rr": dump_benchmark_data("D30Retention"),
		# 	"d1_stick": dump_benchmark_data("D1Stickyness"),
		# 	"d7_stick": dump_benchmark_data("D7Stickyness"),
		# 	"d30_stick": dump_benchmark_data("D30Stickyness"),
		# 	"visits": dump_benchmark_data("Visits"),
		# 	"mau": dump_benchmark_data("MonthlyActiveUsers"),
		# 	"total_hours": dump_benchmark_data("TotalHours"),
		# 	"avg_play_time": dump_benchmark_data("AveragePlayTime"),
		# 	"new_users": dump_benchmark_data("NewUsers"),
		# 	"avg_play_time": dump_benchmark_data("AveragePlayTime"),
		# 	"dau": dump_benchmark_data("DailyActiveUsers"),
		# 	"robux": dump_benchmark_data("Robux"),
		# 	"conversion_rate": dump_benchmark_data("ConversionRate"),
		# 	"paying_users": dump_benchmark_data("PayingUsers"),
		# 	"arppu": dump_benchmark_data("ARPPU"),
		# 	"paying_users": dump_benchmark_data("PayingUsers"),
		# 	"arpu": dump_benchmark_data("ARPU"),
		# },
		"aquisition": {
			"game_details": dump_aquisition_data("GameDetails"), 
			"impressions": dump_aquisition_data("Impressions"), 
			"play_sessions": dump_aquisition_data("PlaySessions"), 
			"new_users": dump_aquisition_data("NewUsers"), 
			"joins": {
				"direct": dump_aquisition_data("DirectJoins"),  
				"game_detail": dump_aquisition_data("GameDetailsJoins"), 
			},
			"unique_sessions": {
				"impression": dump_aquisition_data("ImpressionUniqueSessions"), 
				"game_details": dump_aquisition_data("GameDetailsUniqueSessions"), 
				"total": dump_aquisition_data("UniqueSessions"), 
			},
		},
	}