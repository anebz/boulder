# -*- coding: utf-8 -*-
"""
Created on Mon Sep  6 17:52:12 2021

@author: Anja
"""
from web_scrape import *
import unittest

class test_BerlinScraping(unittest.TestCase):
    
    def test_berlin_urlMagicMountain(self):
        urls_berlin = ['https://www.magicmountain.de/preise/#Besucheranzahl']
        occupancy = process_occupancy_berlinMagicMountain(urls_berlin[0])        
        self.assertEqual(type(occupancy), type(0))
    def test_berlin_urlArea85(self):
        occupancy = process_occupancy_area85(url_berlin_Area85)
        self.assertEqual(type(occupancy), type(0))
        
if __name__ == '__main__':
    unittest.main()