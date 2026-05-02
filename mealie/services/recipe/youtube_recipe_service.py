from __future__ import annotations

import asyncio
import json
import re
from urllib.parse import parse_qs, urlparse

import requests
from youtube_transcript_api import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApi,
)

from mealie.schema.recipe import Recipe
from mealie.services.recipe.recipe_service import OpenAIRecipeService


class YouTubeRecipeService(OpenAIRecipeService):
    """Build recipes from YouTube video metadata and transcripts using OpenAI.

    Uses YouTube's mobile site (m.youtube.com) with a mobile User-Agent to
    extract the video description without triggering bot detection. Combines
    with youtube-transcript-api for captions. Works from any IP including
    datacenter/VPS deployments.
    """

    MAX_TRANSCRIPT_CHARS = 30000

    _MOBILE_UA = (
        "Mozilla/5.0 (Linux; Android 14; SM-G991B) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Mobile Safari/537.36"
    )

    @staticmethod
    def is_youtube_url(url: str) -> bool:
        try:
            parsed = urlparse(url)
        except Exception:
            return False

        host = parsed.netloc.lower().removeprefix("www.").removeprefix("m.")
        return host in {"youtube.com", "youtu.be", "youtube-nocookie.com"} or host.endswith(".youtube.com")

    @classmethod
    def extract_video_id(cls, url: str) -> str | None:
        parsed = urlparse(url)
        host = parsed.netloc.lower().removeprefix("www.").removeprefix("m.")

        if host == "youtu.be":
            return parsed.path.strip("/").split("/")[0] or None

        if parsed.path == "/watch":
            return parse_qs(parsed.query).get("v", [None])[0]

        path_parts = [part for part in parsed.path.split("/") if part]
        if path_parts and path_parts[0] in {"embed", "shorts", "live"} and len(path_parts) > 1:
            return path_parts[1]

        return None

    @classmethod
    def _fetch_mobile_page(cls, video_id: str) -> str:
        """Fetch the mobile HTML page for a video."""
        url = f"https://m.youtube.com/watch?v={video_id}"
        headers = {
            "User-Agent": cls._MOBILE_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }

        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        return resp.text

    @classmethod
    def _extract_description_from_html(cls, html: str) -> str:
        """Extract the video description from mobile HTML.

        YouTube's mobile pages include a JSON blob with video details
        containing the shortDescription field.
        """
        # Try to find ytInitialPlayerResponse
        player_match = re.search(
            r'var\s+ytInitialPlayerResponse\s*=\s*({.+?});',
            html,
            re.DOTALL,
        )
        if player_match:
            try:
                data = json.loads(player_match.group(1))
                video_details = data.get("videoDetails", {})
                description = video_details.get("shortDescription", "")
                return description.strip()
            except (json.JSONDecodeError, AttributeError):
                pass

        # Fallback: look for description in meta tags
        desc_match = re.search(
            r'<meta\s+name="description"\s+content="([^"]*)"',
            html,
            re.IGNORECASE,
        )
        if desc_match:
            return desc_match.group(1).strip()

        # Fallback: look for og:description
        og_match = re.search(
            r'<meta\s+property="og:description"\s+content="([^"]*)"',
            html,
            re.IGNORECASE,
        )
        if og_match:
            return og_match.group(1).strip()

        return ""

    @classmethod
    def _extract_video_info(cls, video_id: str) -> dict:
        """Fetch video metadata including title, channel, and description.

        Uses the mobile site with a mobile User-Agent to avoid bot detection.
        """
        html = cls._fetch_mobile_page(video_id)

        # Extract description from the HTML
        description = cls._extract_description_from_html(html)

        # Extract title from the HTML
        title = ""
        title_match = re.search(
            r'<meta\s+property="og:title"\s+content="([^"]*)"',
            html,
            re.IGNORECASE,
        )
        if title_match:
            title = title_match.group(1).strip()
        else:
            # Try from ytInitialPlayerResponse
            player_match = re.search(
                r'var\s+ytInitialPlayerResponse\s*=\s*({.+?});',
                html,
                re.DOTALL,
            )
            if player_match:
                try:
                    data = json.loads(player_match.group(1))
                    title = data.get("videoDetails", {}).get("title", "").strip()
                except (json.JSONDecodeError, AttributeError):
                    pass

        # Extract channel from the HTML
        channel = ""
        channel_match = re.search(
            r'<meta\s+property="og:video:tag"\s+content="([^"]*)"',
            html,
            re.IGNORECASE,
        )
        if not channel_match:
            # Try from ytInitialPlayerResponse
            player_match = re.search(
                r'var\s+ytInitialPlayerResponse\s*=\s*({.+?});',
                html,
                re.DOTALL,
            )
            if player_match:
                try:
                    data = json.loads(player_match.group(1))
                    channel = data.get("videoDetails", {}).get("author", "").strip()
                except (json.JSONDecodeError, AttributeError):
                    pass

        return {
            "title": title,
            "channel": channel,
            "description": description,
        }

    @classmethod
    def _extract_transcript(cls, video_id: str) -> str:
        """Fetch English transcript/captions via youtube-transcript-api."""
        try:
            if hasattr(YouTubeTranscriptApi, "get_transcript"):
                transcript_entries = YouTubeTranscriptApi.get_transcript(
                    video_id, languages=["en"]
                )
            else:
                transcript_entries = YouTubeTranscriptApi().fetch(
                    video_id, languages=["en"]
                )
        except NoTranscriptFound:
            try:
                if hasattr(YouTubeTranscriptApi, "list_transcripts"):
                    transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                else:
                    transcript_list = YouTubeTranscriptApi().list(video_id)
                transcript_entries = transcript_list.find_generated_transcript(
                    ["en"]
                ).fetch()
            except Exception:
                return ""
        except (TranscriptsDisabled, VideoUnavailable):
            return ""
        except Exception:
            return ""

        transcript_parts: list[str] = []
        for entry in transcript_entries:
            text = (
                entry.get("text", "")
                if isinstance(entry, dict)
                else getattr(entry, "text", "")
            )
            if text:
                transcript_parts.append(str(text).replace("\n", " ").strip())

        return " ".join(transcript_parts)

    async def generate_recipe_from_youtube(
        self, url: str, include_image: bool = False
    ) -> tuple[Recipe, bytes | None]:
        if not self.is_youtube_url(url):
            raise ValueError("URL must be a YouTube URL")

        video_id = self.extract_video_id(url)
        if not video_id:
            raise ValueError("Unable to determine YouTube video ID")

        video_info, transcript = await asyncio.gather(
            asyncio.to_thread(self._extract_video_info, video_id),
            asyncio.to_thread(self._extract_transcript, video_id),
        )

        prompt = self._build_prompt(url, video_info, transcript)
        recipe, image_data = await self.generate_recipe_with_image(
            prompt, include_image=include_image
        )
        recipe.org_url = url
        return recipe, image_data

    def _build_prompt(self, url: str, video_info: dict, transcript: str) -> str:
        title = str(video_info.get("title") or "").strip()
        channel = str(video_info.get("channel") or "").strip()
        description = str(video_info.get("description") or "").strip()

        if not title and not description and not transcript:
            raise ValueError(
                "Unable to extract any usable content from this YouTube video"
            )

        description = description[: self.MAX_TRANSCRIPT_CHARS]
        transcript = transcript[: self.MAX_TRANSCRIPT_CHARS]

        description_section = description or "No description available."
        transcript_section = (
            transcript or "No transcript was available. Use the title and description only."
        )

        return f"""
Extract exactly one cooking recipe from this YouTube video. Prefer explicit recipe details from the description and transcript. Ignore sponsorships, unrelated chatter, comments, hashtags, and channel promotion. If quantities, times, or yields are implied but not exact, make the best conservative estimate and keep the recipe usable.

YouTube URL: {url}
Video title: {title}
Channel: {channel}

Video description:
{description_section}

Transcript:
{transcript_section}
""".strip()
