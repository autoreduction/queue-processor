import unittest

"""
TODO: 
    # tests:
#        self.current_date = datetime.date.today() # today
#        self.current_date = datetime.datetime.strptime('2019-09-10', '%Y-%m-%d').date() # first day of cycle
#        self.current_date = datetime.datetime.strptime('2016-04-13', '%Y-%m-%d').date() # last cycle in data frame
#        self.current_date = datetime.datetime.strptime('2020-7-11', '%Y-%m-%d').date() # before any published cycles
#        self.current_date = datetime.datetime.strptime('2020-4-26', '%Y-%m-%d').date() # between cycles
#        self.current_date = datetime.datetime.strptime('2016-4-10', '%Y-%m-%d').date() # later than last cycle
"""

class MyTestCase(unittest.TestCase):
    def test_something(self):
        self.assertEqual(True, False)


if __name__ == '__main__':
    unittest.main()
