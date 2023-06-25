import os
import multiprocessing
import json
import requests
from datetime import datetime
import base64
import src.util as util
import src.ads as ads
import src.dashboard as dashboard
import src.devstat as devstat
import src.info as info
import src.sponsorships as sponsorships
import sys

ROBLOX_COOKIE_ENV_KEY = "ROBLOX_COOKIE"

def get_arg(key: str) -> str | None:
	for i, k in enumerate(sys.argv):
		if k == key:
			# if i+1 in sys.argv:
			# 	str_val = sys.argv[i+1]
			# 	assert(str_val)
			return sys.argv[i+1]
			# else:
				# return None
	return None

def get_place_id() -> int:
	place_id_str = sys.argv[2]
	assert place_id_str
	
	place_id = int(place_id_str)
	assert place_id

	return place_id

def get_roblox_cookie() -> str:
	if os.path.exists("test-cookie.txt"):
		with open("test-cookie.txt") as txt_file:
			return txt_file.read()

	roblox_cookie: str | None = os.getenv(ROBLOX_COOKIE_ENV_KEY)
	if not roblox_cookie:
		roblox_cookie = get_arg("-cookie")

	assert roblox_cookie, "github secret ROBLOX_COOKIE does not exist"
	return roblox_cookie

def main():

	try:

		if "run" == sys.argv[1]:
			place_id = get_place_id()

			session = requests.Session()
			# session.headers["Content-Type"] = "text/plain"
			session.cookies.update({
				".ROBLOSECURITY": get_roblox_cookie()
			})
			session.headers.update({
				"X-Csrf-Token": util.get_xcrf_token(session)
			})

			out_path = get_arg("-o")
			assert out_path != None

			interval = int(get_arg("-interval"))
			assert interval != None

			group_id = int(get_arg("-group"))
			assert group_id != None

			final_data = {}
			# try:
			final_data["dashboard"] = dashboard.record_data(session, place_id, interval)
			# except:
				# print("dashboard data failed")

			# try:
			final_data["dev_stat"] = devstat.get_data(session, place_id)
			# except:
				# print("dev stat data failed")	

			# try:
			final_data["info"] = info.get_game_stats(session, place_id)
			# except:
				# print("info data failed")	

			# try:
			final_data["ads"] = ads.get_ads(session, place_id, group_id)
			# except:
				# print("ad data failed")	

			

			try:
				final_data["sponsors"] = sponsorships.get_sponsors(session, place_id)
			except:
				print("sponsor data failed")	

			now = datetime.now()
			now_txt = now.strftime("%Yy-%mm-%dd%Hh%Mm")
			final_data["timestamp"] = now_txt

			file_name = now_txt.replace(":","_")+".txt"

			with open(out_path+"/"+file_name, "wb") as data_file:
				data_file.write(base64.b64encode(bytes(json.dumps(final_data), "utf-8")))

	except:
		raise ValueError("something went wrong")

# prevent from running twice
if __name__ == '__main__':
	multiprocessing.freeze_support()
	main()		

