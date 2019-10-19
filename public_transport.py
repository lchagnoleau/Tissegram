# coding=UTF-8

import requests
from datetime import datetime
from log import get_logger

import time


class PublicTransport(object):
    def __init__(self, token):
        #init logs
        self.logger = get_logger(self.__class__.__name__)
        self.logger.info("Init {}".format(self.__class__.__name__))
        
        self.token = token

    def construct_url(self, function, parameters = ""):
        url = "https://api.tisseo.fr/v1/{}.json?{}&key={}".format(function, parameters, self.token)
        self.logger.debug("Construct URL : {}".format(url))
        return url

    def get_lines(self):
        r = requests.get(url=self.construct_url(function="lines")).json()
        self.logger.debug("Response is \n{}".format(r))
        return r

    def get_line(self, line):
        self.logger.debug("Get line info for line : {}".format(line))
        lines_dict = self.get_lines()

        line_info = {}
        # search line
        for l in lines_dict["lines"]["line"]:
            if l['shortName'] == line:
                line_info = l
                break

        self.logger.debug("Line info : {}".format(line_info))
        return line_info

    def get_points(self, line_id):
        r = requests.get(url=self.construct_url(function="stop_points", parameters="lineId={}".format(line_id))).json()
        self.logger.debug("Response is \n{}".format(r))
        return r

    def get_places(self, term):
        self.logger.debug("Get places for term : {}".format(term))
        places = []
        term = "%20".join(term.split(" "))
        param = "term={}&displayOnlyStopAreas=1".format(term)
        result_request = requests.get(url=self.construct_url(function="places", parameters=param)).json()

        for place in result_request['placesList']['place']:
            places.append([place['id'], place['label']])

        self.logger.debug("Found places are : {}".format(places))
        return places

    def get_lines_by_stoppoints(self, stopId):
        self.logger.debug("Get lines for stop ID : {}".format(stopId))
        list_line = []

        param = "stopAreaId={}&displayLines=1&displayDestinations=1&timeFrame=7".format(stopId)
        result_request = requests.get(url=self.construct_url(function="stop_points", parameters=param)).json()
        
        line = {}
        for physicalStops in result_request['physicalStops']['physicalStop']:
            for dest in physicalStops['destinations']:
                line['dest-name'] = dest['name']
                line['dest-id'] = dest['id']
                for l in dest['line']:
                    if l['reservationMandatory'] == '0':
                        line['line-name'] = l['shortName']
                        line['line-id'] = l['id']
                        list_line.append(dict(line))

        self.logger.debug("Found lines are : {}".format(list_line))
        return list_line

    def get_next_passages(self, line, dest_id, stop_id, line_id):
        self.logger.debug("Get next passage")
        now = datetime.now()
        next_passage = []
        
        param = "stopPointId={}&lineId={}".format(stop_id, line_id)
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
            next_passage.append([l["dateTime"], int(int(d2_ts-d1_ts) / 60)])

        self.logger.debug("Next passages are : {}".format(next_passage))
        return next_passage