# coding=UTF-8

import requests
from datetime import datetime
import time


class PublicTransport(object):
    def __init__(self, token):
        self.token = token

    def construct_url(self, function, parameters = ""):
        return "https://api.tisseo.fr/v1/{}.json?{}&key={}".format(function, parameters, self.token)

    def get_lines(self):
        return requests.get(url=self.construct_url(function="lines")).json()

    def get_line(self, line):
        lines_dict = self.get_lines()

        line_info = {}
        # search line
        for l in lines_dict["lines"]["line"]:
            if l['shortName'] == line:
                line_info = l
                break

        return line_info

    def get_points(self, line_id):
        return requests.get(url=self.construct_url(function="stop_points", parameters="lineId={}".format(line_id))).json()

    def get_places(self, term):
        places = []
        term = "%20".join(term.split(" "))
        param = "term={}&displayOnlyStopAreas=1".format(term)
        result_request = requests.get(url=self.construct_url(function="places", parameters=param)).json()

        for place in result_request['placesList']['place']:
            places.append([place['id'], place['label']])

        return places

    def get_lines_by_stoppoints(self, stopId):
        list_line = []
        param = "stopPointId={}&displayRealTime=0".format(stopId)
        result_request = requests.get(url=self.construct_url(function="stops_schedules", parameters=param)).json()
        tmp = []
        for dest in result_request["departures"]["departure"]:
            for d in dest["destination"]:
                tmp.append(dest["line"]["shortName"]) 
                tmp.append(d["name"])
                tmp.append(d["id"])
                tmp.append(stopId)
                if tmp not in list_line:
                    list_line.append(tmp)
                tmp = []

        return list_line

    def get_next_passages(self, line, dest_id, stop_id):
        now = datetime.now()
        next_passage = []
        
        param = "stopPointId={}&displayRealTime=0".format(stop_id)
        result_request = requests.get(url=self.construct_url(function="stops_schedules", parameters=param)).json()
        interest_list = []
        for dest in result_request["departures"]["departure"]:
            if dest["destination"][0]["id"] == dest_id and dest["line"]["shortName"] == line:
                interest_list.append(dest)

        for l in interest_list:
            fmt = '%Y-%m-%d %H:%M:%S'
            nowstr = now.strftime("%Y-%m-%d %H:%M:%S")
            d1 = datetime.strptime(nowstr, fmt)
            d2 = datetime.strptime(l["dateTime"], fmt)
            d1_ts = time.mktime(d1.timetuple())
            d2_ts = time.mktime(d2.timetuple())
            next_passage.append([l["dateTime"], (int(d2_ts-d1_ts) / 60)])

        return next_passage