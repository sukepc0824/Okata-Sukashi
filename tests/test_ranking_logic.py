
import sys
import os
import json
import unittest
from unittest.mock import MagicMock

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module
from app import reset_all, game_state

class TestRankingLogic(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        reset_all(num_groups=5)
        # Mock some scores
        groups['1']['total_score'] = 100
        groups['2']['total_score'] = 200
        groups['3']['total_score'] = 150
        groups['4']['total_score'] = 50
        groups['5']['total_score'] = 300
        
        # Expected order: 5 (300), 2 (200), 3 (150), 1 (100), 4 (50)

    def test_ranking_api_result_status(self):
        game_state["status"] = "result"
        game_state["current_index"] = 0 # Ensure valid index
        
        # Dummy group needed for 'score' access in loop, so ensure group '1' exists
        # In result status, API returns specific group data too.
        
        response = self.app.get('/api/state?group=1&player=A')
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'result')
        ranking = data['ranking']
        
        self.assertEqual(len(ranking), 5)
        
        # Check sort order
        self.assertEqual(ranking[0]['id'], '5')
        self.assertEqual(ranking[1]['id'], '2')
        self.assertEqual(ranking[2]['id'], '3')
        self.assertEqual(ranking[3]['id'], '1')
        self.assertEqual(ranking[4]['id'], '4')
        
        # Check ID presence
        self.assertIn('id', ranking[0])
        self.assertEqual(ranking[0]['group'], groups['5']['name'])

    def test_ranking_api_ranking_status(self):
        game_state["status"] = "ranking"
        
        response = self.app.get('/api/state?group=1&player=A')
        data = json.loads(response.data)
        
        self.assertEqual(data['status'], 'ranking')
        ranking = data['ranking']
        
        self.assertEqual(len(ranking), 5)
        
        # Check sort order (Should be descending now)
        self.assertEqual(ranking[0]['id'], '5')
        self.assertEqual(ranking[1]['id'], '2')
        self.assertEqual(ranking[2]['id'], '3')
        self.assertEqual(ranking[3]['id'], '1')
        self.assertEqual(ranking[4]['id'], '4')


if __name__ == '__main__':
    unittest.main()
