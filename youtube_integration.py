"""YouTube integration for learning resources.

This module provides functionality to search and integrate YouTube videos
into the learning roadmap and flashcard systems.
"""

import httpx
import json
from typing import List, Dict, Any, Optional
from urllib.parse import quote
import re


class YouTubeIntegration:
    """YouTube integration for finding educational content."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube integration.
        
        Args:
            api_key: YouTube Data API key (optional - will use mock data if not provided)
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    async def search_educational_videos(
        self, 
        topic: str, 
        max_results: int = 10,
        video_duration: str = "medium"
    ) -> List[Dict[str, Any]]:
        """
        Search for educational videos on YouTube.
        
        Args:
            topic: The topic to search for
            max_results: Maximum number of results to return
            video_duration: Video duration filter (short, medium, long)
            
        Returns:
            List of video information
        """
        if self.api_key:
            return await self._search_with_api(topic, max_results, video_duration)
        else:
            return self._get_mock_videos(topic, max_results)
    
    async def _search_with_api(
        self, 
        topic: str, 
        max_results: int, 
        video_duration: str
    ) -> List[Dict[str, Any]]:
        """Search using YouTube Data API."""
        try:
            async with httpx.AsyncClient() as client:
                search_url = f"{self.base_url}/search"
                params = {
                    "part": "snippet",
                    "q": f"{topic} tutorial educational",
                    "type": "video",
                    "maxResults": max_results,
                    "videoDuration": video_duration,
                    "key": self.api_key,
                    "relevanceLanguage": "en",
                    "safeSearch": "moderate"
                }
                
                response = await client.get(search_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                videos = []
                
                for item in data.get("items", []):
                    video_info = {
                        "video_id": item["id"]["videoId"],
                        "title": item["snippet"]["title"],
                        "description": item["snippet"]["description"],
                        "channel": item["snippet"]["channelTitle"],
                        "published_at": item["snippet"]["publishedAt"],
                        "thumbnail": item["snippet"]["thumbnails"]["medium"]["url"],
                        "url": f"https://www.youtube.com/watch?v={item['id']['videoId']}"
                    }
                    videos.append(video_info)
                
                # Get video details including duration
                video_ids = [v["video_id"] for v in videos]
                detailed_videos = await self._get_video_details(video_ids)
                
                # Combine search results with detailed information
                for i, video in enumerate(videos):
                    if i < len(detailed_videos):
                        video.update(detailed_videos[i])
                
                return videos
                
        except Exception as e:
            print(f"YouTube API error: {e}")
            return self._get_mock_videos(topic, max_results)
    
    async def _get_video_details(self, video_ids: List[str]) -> List[Dict[str, Any]]:
        """Get detailed video information including duration."""
        try:
            async with httpx.AsyncClient() as client:
                details_url = f"{self.base_url}/videos"
                params = {
                    "part": "contentDetails,statistics",
                    "id": ",".join(video_ids),
                    "key": self.api_key
                }
                
                response = await client.get(details_url, params=params)
                response.raise_for_status()
                
                data = response.json()
                details = []
                
                for item in data.get("items", []):
                    duration = self._parse_duration(item["contentDetails"]["duration"])
                    view_count = item["statistics"].get("viewCount", "0")
                    like_count = item["statistics"].get("likeCount", "0")
                    
                    detail = {
                        "duration": duration,
                        "duration_seconds": self._duration_to_seconds(duration),
                        "view_count": int(view_count),
                        "like_count": int(like_count)
                    }
                    details.append(detail)
                
                return details
                
        except Exception as e:
            print(f"Error getting video details: {e}")
            return [{"duration": "Unknown", "duration_seconds": 0, "view_count": 0, "like_count": 0}] * len(video_ids)
    
    def _parse_duration(self, duration: str) -> str:
        """Parse ISO 8601 duration to human-readable format."""
        # PT4M13S -> 4:13
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
        return "Unknown"
    
    def _duration_to_seconds(self, duration: str) -> int:
        """Convert duration string to seconds."""
        match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 0
    
    def _get_mock_videos(self, topic: str, max_results: int) -> List[Dict[str, Any]]:
        """Get mock video data when API key is not available."""
        mock_videos = [
            {
                "video_id": "dQw4w9WgXcQ",
                "title": f"Introduction to {topic} - Complete Beginner's Guide",
                "description": f"Learn the fundamentals of {topic} from scratch. This comprehensive tutorial covers all the essential concepts you need to get started.",
                "channel": "EduTech Academy",
                "published_at": "2024-01-15T10:00:00Z",
                "thumbnail": "https://via.placeholder.com/320x180/667eea/ffffff?text=Intro+Video",
                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                "duration": "15:30",
                "duration_seconds": 930,
                "view_count": 125000,
                "like_count": 3500
            },
            {
                "video_id": "abc123def456",
                "title": f"Advanced {topic} Techniques and Best Practices",
                "description": f"Take your {topic} skills to the next level with these advanced techniques and industry best practices.",
                "channel": "Tech Masters",
                "published_at": "2024-01-10T14:30:00Z",
                "thumbnail": "https://via.placeholder.com/320x180/764ba2/ffffff?text=Advanced+Video",
                "url": "https://www.youtube.com/watch?v=abc123def456",
                "duration": "25:45",
                "duration_seconds": 1545,
                "view_count": 89000,
                "like_count": 2100
            },
            {
                "video_id": "xyz789uvw012",
                "title": f"{topic} Project Tutorial - Build Something Amazing",
                "description": f"Follow along as we build a practical {topic} project from start to finish. Perfect for hands-on learners.",
                "channel": "CodeCraft",
                "published_at": "2024-01-08T09:15:00Z",
                "thumbnail": "https://via.placeholder.com/320x180/f093fb/ffffff?text=Project+Tutorial",
                "url": "https://www.youtube.com/watch?v=xyz789uvw012",
                "duration": "45:20",
                "duration_seconds": 2720,
                "view_count": 156000,
                "like_count": 4200
            }
        ]
        
        return mock_videos[:max_results]
    
    async def get_video_transcript(self, video_id: str) -> Optional[str]:
        """
        Get video transcript (mock implementation).
        
        In a real implementation, this would use YouTube's transcript API
        or a third-party service to extract video transcripts.
        """
        # Mock transcript for demonstration
        mock_transcripts = {
            "dQw4w9WgXcQ": """
            Welcome to this comprehensive introduction to the topic. 
            In this video, we'll cover the fundamental concepts that every beginner needs to know.
            
            First, let's start with the basic terminology. Understanding these key terms is essential
            for building a strong foundation in this subject.
            
            Next, we'll explore the core principles that govern how everything works. These principles
            are the building blocks that you'll use throughout your learning journey.
            
            Finally, we'll look at some practical examples that demonstrate these concepts in action.
            By the end of this video, you'll have a solid understanding of the fundamentals.
            """,
            "abc123def456": """
            In this advanced tutorial, we dive deep into sophisticated techniques that will elevate
            your skills to a professional level.
            
            We'll explore complex patterns and strategies that experts use in real-world scenarios.
            These techniques have been tested and proven in production environments.
            
            Pay close attention to the implementation details, as small nuances can make a significant
            difference in performance and maintainability.
            """,
            "xyz789uvw012": """
            Let's build a complete project from scratch! This hands-on tutorial will guide you through
            every step of the development process.
            
            We'll start by setting up our development environment and gathering the necessary tools.
            Then, we'll implement the core functionality step by step, explaining each decision
            along the way.
            
            By the end of this project, you'll have a fully functional application that you can
            include in your portfolio.
            """
        }
        
        return mock_transcripts.get(video_id, "Transcript not available for this video.")
    
    def get_embed_url(self, video_id: str, start_time: Optional[int] = None) -> str:
        """
        Get embeddable YouTube URL.
        
        Args:
            video_id: YouTube video ID
            start_time: Start time in seconds (optional)
            
        Returns:
            Embeddable YouTube URL
        """
        url = f"https://www.youtube.com/embed/{video_id}"
        if start_time:
            url += f"?start={start_time}"
        return url
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL.
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID or None if not found
        """
        patterns = [
            r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None


# Utility functions for video processing
def format_duration(seconds: int) -> str:
    """Format seconds into human-readable duration."""
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes}:{secs:02d}"


def calculate_engagement_score(views: int, likes: int) -> float:
    """Calculate engagement score based on views and likes."""
    if views == 0:
        return 0.0
    return (likes / views) * 100


def filter_videos_by_duration(videos: List[Dict[str, Any]], max_minutes: int) -> List[Dict[str, Any]]:
    """Filter videos by maximum duration in minutes."""
    max_seconds = max_minutes * 60
    return [video for video in videos if video.get("duration_seconds", 0) <= max_seconds]


def sort_videos_by_relevance(videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Sort videos by relevance (engagement score and recency)."""
    def relevance_score(video):
        engagement = calculate_engagement_score(
            video.get("view_count", 0), 
            video.get("like_count", 0)
        )
        # Newer videos get a slight boost
        recency_boost = 1.0  # Would calculate based on published_at
        return engagement * recency_boost
    
    return sorted(videos, key=relevance_score, reverse=True)