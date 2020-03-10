from unittest import TestCase

from macaroonbakery.httpbakery import WebBrowserInteractionInfo


class TestWebBrowserInteractionInfo(TestCase):

    def test_from_dict(self):
        info_dict = {
            'VisitURL': 'https://example.com/visit',
            'WaitTokenURL': 'https://example.com/wait'}
        interaction_info = WebBrowserInteractionInfo.from_dict(info_dict)
        self.assertEqual(
            interaction_info.visit_url, 'https://example.com/visit')
        self.assertEqual(
            interaction_info.wait_token_url, 'https://example.com/wait')
