# coding=UTF-8

import requests


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
        term = replace(term, ' ', '%20')
        param = "term={}&displayOnlyStopAreas=1".format(term)
        result_request = requests.get(url=self.construct_url(function="places", parameters=param)).json()

        for place in result_request['placesList']['place']:
            places.append([place['id'], place[label]])

        return places