# -*- coding: utf-8 -*-
"""
Created on Wed Nov 16 12:22:08 2022

@author: jpeacock
"""
# =============================================================================
# Imports
# =============================================================================
import unittest
from mt_metadata.utils.list_dict import ListDict
from mt_metadata.timeseries import Survey, Station, Run, Channel

# =============================================================================


class TestListDict(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.ld = ListDict()
        self.ld["a"] = 10

    def test_in_keys(self):
        self.assertIn("a", self.ld.keys())

    def test_value(self):
        self.assertEqual(self.ld["a"], 10)

    def test_from_index(self):
        self.assertEqual(self.ld[0], 10)

    def test_from_key(self):
        self.assertEqual(self.ld["a"], 10)

    def test_get_item_fail(self):
        self.assertRaises(KeyError, self.ld._get_key_from_index, 1)

    def test_str(self):
        self.assertEqual("Keys In Order: a", self.ld.__str__())

    def test_repr(self):
        self.assertEqual("OrderedDict([('a', 10)])", self.ld.__repr__())

    def test_items(self):
        self.assertTupleEqual((("a", 10),), tuple(self.ld.items()))

    def test_get_index_from_key(self):
        self.assertEqual(0, self.ld._get_index_from_key("a"))

    def test_get_index_from_key_fail(self):
        self.assertRaises(KeyError, self.ld._get_index_from_key, "b")

    def test_get_key_from_index(self):
        self.assertEqual("a", self.ld._get_key_from_index(0))

    def test_get_key_from_index_fail(self):
        self.assertRaises(KeyError, self.ld._get_key_from_index, 2)


class TestListDictSetIndex(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.ld = ListDict()
        self.ld[1] = 2

    def test_in_keys(self):
        self.assertIn("1", self.ld.keys())

    def test_from_key(self):
        self.assertEqual(self.ld["1"], 2)

    def test_from_index(self):
        self.assertEqual(self.ld[0], 2)


class TestListDictFromSurvey(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.ld = ListDict()
        self.survey = Survey(id="test")
        self.ld.append(self.survey)
        self.maxDiff = None

    def test_in_keys(self):
        self.assertIn("test", self.ld.keys())

    def test_survey_from_index(self):
        self.assertDictEqual(
            self.survey.to_dict(single=True), self.ld[0].to_dict(single=True)
        )

    def test_survey_from_key(self):
        self.assertDictEqual(
            self.survey.to_dict(single=True),
            self.ld["test"].to_dict(single=True),
        )


class TestListDictFromStation(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.ld = ListDict()
        self.station = Station(id="test")
        self.ld.append(self.station)
        self.maxDiff = None

    def test_in_keys(self):
        self.assertIn("test", self.ld.keys())

    def test_station_from_index(self):
        self.assertDictEqual(
            self.station.to_dict(single=True), self.ld[0].to_dict(single=True)
        )

    def test_station_from_key(self):
        self.assertDictEqual(
            self.station.to_dict(single=True),
            self.ld["test"].to_dict(single=True),
        )


class TestListDictFromRun(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.ld = ListDict()
        self.run_obj = Run(id="test")
        self.ld[0] = self.run_obj
        self.maxDiff = None

    def test_in_keys(self):
        self.assertIn("test", self.ld.keys())

    def test_run_from_index(self):
        self.assertDictEqual(
            self.run_obj.to_dict(single=True), self.ld[0].to_dict(single=True)
        )

    def test_run_from_key(self):
        self.assertDictEqual(
            self.run_obj.to_dict(single=True),
            self.ld["test"].to_dict(single=True),
        )


class TestListDictFromChannel(unittest.TestCase):
    @classmethod
    def setUpClass(self):
        self.ld = ListDict()
        self.channel = Channel(component="test")
        self.ld.append(self.channel)
        self.maxDiff = None

    def test_in_keys(self):
        self.assertIn("test", self.ld.keys())

    def test_survey_from_index(self):
        self.assertDictEqual(
            self.channel.to_dict(single=True), self.ld[0].to_dict(single=True)
        )

    def test_survey_from_key(self):
        self.assertDictEqual(
            self.channel.to_dict(single=True),
            self.ld["test"].to_dict(single=True),
        )


class TestListDictRemove(unittest.TestCase):
    def setUp(self):
        self.ld = ListDict()
        self.ld["a"] = 0

    def test_remove_by_key(self):
        self.ld.remove("a")
        self.assertListEqual([], self.ld.keys())

    def test_remove_by_index(self):
        self.ld.remove(0)
        self.assertListEqual([], self.ld.keys())


# =============================================================================
# Run test
# =============================================================================
if __name__ == "__main__":
    unittest.main()
