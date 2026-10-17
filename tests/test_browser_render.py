from __future__ import annotations

from pathlib import Path
import sys
import unittest
from unittest.mock import Mock


ROOT_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT_DIR / "scripts"))

from browser_render import BrowserPageRequestRouter  # noqa: E402


class FakeRequest:
    def __init__(
        self,
        url: str,
        *,
        method: str = "GET",
        resource_type: str = "script",
        navigation: bool = False,
    ) -> None:
        self.url = url
        self.method = method
        self.resource_type = resource_type
        self._navigation = navigation

    def is_navigation_request(self) -> bool:
        return self._navigation


class FakeRoute:
    def __init__(self, request: FakeRequest) -> None:
        self.request = request
        self.aborted = False
        self.fulfilled: dict[str, object] | None = None

    def abort(self) -> None:
        self.aborted = True

    def fulfill(self, **kwargs: object) -> None:
        self.fulfilled = kwargs


class BrowserRequestRouterTests(unittest.TestCase):
    def make_router(self, fetcher: Mock, **kwargs: object) -> BrowserPageRequestRouter:
        return BrowserPageRequestRouter(
            "https://example.com/",
            safe_fetcher=fetcher,
            user_agent="SearchScope test",
            **kwargs,
        )

    def test_same_origin_get_is_fulfilled_through_public_safe_fetcher(self) -> None:
        fetcher = Mock(
            return_value=(
                {
                    "status": 200,
                    "content_type": "application/javascript",
                    "content_charset": "utf-8",
                    "bytes_read": 4,
                    "truncated": False,
                    "error": None,
                },
                b"test",
            )
        )
        route = FakeRoute(FakeRequest("https://example.com/app.js"))

        self.make_router(fetcher).handle(route)

        self.assertIsNotNone(route.fulfilled)
        self.assertEqual(b"test", route.fulfilled["body"])
        self.assertEqual("application/javascript; charset=utf-8", route.fulfilled["headers"]["content-type"])
        self.assertFalse(route.aborted)
        self.assertEqual("https://example.com/app.js", fetcher.call_args.args[0])
        self.assertFalse(fetcher.call_args.kwargs["allow_private"])
        self.assertTrue(fetcher.call_args.kwargs["return_bytes"])
        self.assertFalse(fetcher.call_args.kwargs["follow_redirects"])
        self.assertEqual("https://example.com", fetcher.call_args.kwargs["allowed_origin"])

    def test_default_https_port_is_normalized_for_browser_navigation(self) -> None:
        fetcher = Mock(
            return_value=(
                {"status": 200, "content_type": "text/html", "bytes_read": 1, "truncated": False},
                b"x",
            )
        )
        router = BrowserPageRequestRouter(
            "https://example.com:443/",
            safe_fetcher=fetcher,
            user_agent="SearchScope test",
        )
        route = FakeRoute(
            FakeRequest("https://example.com/", resource_type="document", navigation=True)
        )

        router.handle(route)

        self.assertIsNotNone(route.fulfilled)
        self.assertEqual("https://example.com", fetcher.call_args.kwargs["allowed_origin"])

    def test_cross_origin_and_non_get_requests_are_blocked_without_fetching(self) -> None:
        fetcher = Mock()
        router = self.make_router(fetcher)

        for request in (
            FakeRequest("https://cdn.example.net/app.js"),
            FakeRequest("https://example.com/submit", method="POST"),
            FakeRequest("https://example.com/picture.png", resource_type="image"),
            FakeRequest("file:///C:/private.txt", resource_type="document", navigation=True),
        ):
            with self.subTest(url=request.url, method=request.method):
                route = FakeRoute(request)
                router.handle(route)
                self.assertTrue(route.aborted)
                self.assertIsNone(route.fulfilled)

        fetcher.assert_not_called()

    def test_only_expected_document_navigation_is_allowed(self) -> None:
        fetcher = Mock(
            return_value=(
                {"status": 200, "content_type": "text/html", "bytes_read": 1, "truncated": False},
                b"x",
            )
        )
        router = self.make_router(fetcher)
        route = FakeRoute(
            FakeRequest("https://example.com/other", resource_type="document", navigation=True)
        )

        router.handle(route)

        self.assertTrue(route.aborted)
        fetcher.assert_not_called()

    def test_redirect_is_validated_and_browser_followup_is_routed(self) -> None:
        fetcher = Mock(
            side_effect=[
                (
                    {
                        "status": 302,
                        "content_type": "text/html",
                        "redirect_url": "https://example.com/final",
                        "bytes_read": 0,
                        "truncated": False,
                        "error": None,
                    },
                    b"",
                ),
                (
                    {
                        "status": 200,
                        "content_type": "text/html",
                        "bytes_read": 5,
                        "truncated": False,
                        "error": None,
                    },
                    b"<html>",
                ),
            ]
        )
        router = self.make_router(fetcher)
        redirect = FakeRoute(
            FakeRequest("https://example.com/", resource_type="document", navigation=True)
        )
        router.handle(redirect)
        followup = FakeRoute(
            FakeRequest("https://example.com/final", resource_type="document", navigation=True)
        )
        router.handle(followup)

        self.assertEqual("https://example.com/final", redirect.fulfilled["headers"]["location"])
        self.assertIsNotNone(followup.fulfilled)
        self.assertFalse(redirect.aborted)
        self.assertFalse(followup.aborted)
        self.assertEqual(2, fetcher.call_count)

    def test_truncated_resource_is_aborted(self) -> None:
        fetcher = Mock(
            return_value=(
                {
                    "status": 200,
                    "content_type": "application/javascript",
                    "bytes_read": 10,
                    "truncated": True,
                    "error": None,
                },
                b"x" * 10,
            )
        )
        route = FakeRoute(FakeRequest("https://example.com/large.js"))

        self.make_router(fetcher, max_resource_bytes=10).handle(route)

        self.assertTrue(route.aborted)
        self.assertIsNone(route.fulfilled)
        self.assertEqual(10, fetcher.call_args.kwargs["max_bytes"])


if __name__ == "__main__":
    unittest.main()
