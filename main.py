"""Learn Anything MCP server - Roadmap and Anki-style flashcard learning app.

This server provides tools for generating personalized learning roadmaps and
interactive flashcard systems to help users learn any topic effectively.
"""

from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import random
from datetime import datetime

import mcp.types as types
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, ConfigDict, Field, ValidationError
from fastapi import Request

# Import our custom modules
from youtube_integration import YouTubeIntegration
from content_extraction import ContentExtractor


@dataclass(frozen=True)
class LearningWidget:
    identifier: str
    title: str
    template_uri: str
    invoking: str
    invoked: str
    html: str
    response_text: str


ASSETS_DIR = Path(__file__).resolve().parent / "assets"


@lru_cache(maxsize=None)
def _load_widget_html(component_name: str) -> str:
    html_path = ASSETS_DIR / f"{component_name}.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf8")

    fallback_candidates = sorted(ASSETS_DIR.glob(f"{component_name}-*.html"))
    if fallback_candidates:
        return fallback_candidates[-1].read_text(encoding="utf8")

    raise FileNotFoundError(
        f'Widget HTML for "{component_name}" not found in {ASSETS_DIR}. '
        "Run `pnpm run build` to generate the assets before starting the server."
    )


# Learning widget definitions
widgets: List[LearningWidget] = [
    LearningWidget(
        identifier="learning-roadmap",
        title="Generate Learning Roadmap",
        template_uri="ui://widget/learning-roadmap.html",
        invoking="Creating your personalized learning roadmap",
        invoked="Your learning roadmap is ready",
        html=_load_widget_html("learning-roadmap"),
        response_text="Generated a personalized learning roadmap!",
    ),
    LearningWidget(
        identifier="flashcard-session",
        title="Start Flashcard Session",
        template_uri="ui://widget/flashcard-session.html",
        invoking="Preparing your flashcard session",
        invoked="Flashcard session ready",
        html=_load_widget_html("flashcard-session"),
        response_text="Started an interactive flashcard session!",
    ),
    LearningWidget(
        identifier="learning-dashboard",
        title="Learning Dashboard",
        template_uri="ui://widget/learning-dashboard.html",
        invoking="Loading your learning dashboard",
        invoked="Dashboard loaded",
        html=_load_widget_html("learning-dashboard"),
        response_text="Loaded your learning dashboard!",
    )
]


MIME_TYPE = "text/html+skybridge"

WIDGETS_BY_ID: Dict[str, LearningWidget] = {widget.identifier: widget for widget in widgets}
WIDGETS_BY_URI: Dict[str, LearningWidget] = {widget.template_uri: widget for widget in widgets}


class RoadmapInput(BaseModel):
    """Schema for roadmap generation."""
    
    topic: str = Field(
        ...,
        description="The topic the user wants to learn about",
    )
    current_level: str = Field(
        default="beginner",
        description="Current knowledge level (beginner, intermediate, advanced)",
    )
    learning_style: str = Field(
        default="visual",
        description="Preferred learning style (visual, auditory, kinesthetic, reading)",
    )
    time_commitment: str = Field(
        default="medium",
        description="Time commitment level (low, medium, high)",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class FlashcardInput(BaseModel):
    """Schema for flashcard sessions."""
    
    topic: str = Field(
        ...,
        description="The topic for flashcard practice",
    )
    difficulty: str = Field(
        default="mixed",
        description="Difficulty level (easy, medium, hard, mixed)",
    )
    card_count: int = Field(
        default=10,
        description="Number of flashcards to generate",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class DashboardInput(BaseModel):
    """Schema for learning dashboard."""
    
    user_id: Optional[str] = Field(
        default="default",
        description="User identifier for session persistence",
    )

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


mcp = FastMCP(
    name="learn-anything",
    stateless_http=True,
)


async def _generate_learning_roadmap(topic: str, current_level: str, learning_style: str, time_commitment: str) -> Dict[str, Any]:
    """Generate a personalized learning roadmap with integrated resources."""
    
    # Initialize integrations
    youtube = YouTubeIntegration()
    content_extractor = ContentExtractor()
    
    # Get resources from various sources
    try:
        # Get YouTube videos
        videos = await youtube.search_educational_videos(topic, max_results=6)
        
        # Get academic papers
        papers = await content_extractor.search_academic_papers(topic, max_results=3)
        
        # Get books
        books = await content_extractor.search_books(topic, max_results=3)
        
    except Exception as e:
        print(f"Error fetching resources: {e}")
        videos, papers, books = [], [], []
    
    # Build roadmap with real resources
    roadmap_data = {
        "topic": topic,
        "current_level": current_level,
        "learning_style": learning_style,
        "time_commitment": time_commitment,
        "generated_at": datetime.now().isoformat(),
        "modules": [
            {
                "id": 1,
                "title": f"Foundations of {topic}",
                "description": "Build your understanding of core concepts",
                "duration": "2-3 weeks",
                "difficulty": "beginner",
                "resources": [
                    {
                        "type": "video",
                        "title": videos[0]["title"] if videos else f"Introduction to {topic}",
                        "source": "YouTube",
                        "url": videos[0]["url"] if videos else "https://youtube.com/watch?v=example",
                        "duration": videos[0]["duration"] if videos else "15:30",
                        "thumbnail": videos[0]["thumbnail"] if videos else "",
                        "views": videos[0]["view_count"] if videos else 0
                    },
                    {
                        "type": "article",
                        "title": f"Getting Started with {topic}",
                        "source": "Educational Blog",
                        "url": "https://example.com/getting-started",
                        "read_time": "8 min"
                    }
                ],
                "milestones": [
                    "Understand basic terminology",
                    "Complete first practical exercise",
                    "Explain concepts to others"
                ]
            },
            {
                "id": 2,
                "title": f"Intermediate {topic} Concepts",
                "description": "Deepen your knowledge with advanced topics",
                "duration": "3-4 weeks",
                "difficulty": "intermediate",
                "resources": [
                    {
                        "type": "video",
                        "title": videos[1]["title"] if len(videos) > 1 else f"Advanced {topic} Techniques",
                        "source": "YouTube",
                        "url": videos[1]["url"] if len(videos) > 1 else "https://youtube.com/watch?v=example2",
                        "duration": videos[1]["duration"] if len(videos) > 1 else "25:45",
                        "thumbnail": videos[1]["thumbnail"] if len(videos) > 1 else "",
                        "views": videos[1]["view_count"] if len(videos) > 1 else 0
                    },
                    {
                        "type": "book",
                        "title": books[0]["title"] if books else f"The {topic} Handbook",
                        "source": books[0]["publisher"] if books else "Tech Publications",
                        "url": books[0]["url"] if books else "https://amazon.com/example",
                        "pages": str(books[0]["pages"]) if books else "350",
                        "rating": books[0]["rating"] if books else 4.5
                    }
                ],
                "milestones": [
                    "Apply concepts to real projects",
                    "Solve complex problems",
                    "Create original work"
                ]
            },
            {
                "id": 3,
                "title": f"Master {topic}",
                "description": "Become an expert through practice and application",
                "duration": "4-6 weeks",
                "difficulty": "advanced",
                "resources": [
                    {
                        "type": "research",
                        "title": papers[0]["title"] if papers else f"Latest {topic} Research",
                        "source": papers[0]["journal"] if papers else "Academic Journal",
                        "url": papers[0]["url"] if papers else "https://scholar.google.com/example",
                        "papers": str(len(papers)),
                        "citations": str(papers[0]["citations"]) if papers else "15"
                    },
                    {
                        "type": "video",
                        "title": videos[2]["title"] if len(videos) > 2 else f"{topic} Mastery Course",
                        "source": "YouTube",
                        "url": videos[2]["url"] if len(videos) > 2 else "https://youtube.com/watch?v=example3",
                        "duration": videos[2]["duration"] if len(videos) > 2 else "45:20",
                        "thumbnail": videos[2]["thumbnail"] if len(videos) > 2 else "",
                        "views": videos[2]["view_count"] if len(videos) > 2 else 0
                    }
                ],
                "milestones": [
                    "Contribute to community",
                    "Teach others",
                    "Innovate in the field"
                ]
            }
        ],
        "learning_path": {
            "total_duration": "9-13 weeks",
            "estimated_hours": "120-180 hours",
            "key_skills": [
                f"Fundamental {topic} concepts",
                f"Practical {topic} applications",
                f"Advanced {topic} techniques",
                "Problem-solving abilities",
                "Critical thinking"
            ]
        },
        "additional_resources": {
            "videos": videos[3:] if len(videos) > 3 else [],
            "papers": papers,
            "books": books[1:] if len(books) > 1 else []
        }
    }
    
    # Cleanup
    await content_extractor.close()
    
    return roadmap_data


async def _generate_flashcards(topic: str, difficulty: str, card_count: int) -> Dict[str, Any]:
    """Generate flashcards for a given topic using content extraction."""
    
    # Initialize content extractor
    content_extractor = ContentExtractor()
    
    try:
        # Get academic papers and books to generate better flashcards
        papers = await content_extractor.search_academic_papers(topic, max_results=2)
        books = await content_extractor.search_books(topic, max_results=2)
        
        # Combine content for flashcard generation
        combined_content = ""
        for paper in papers:
            combined_content += f"Paper: {paper['title']}\n{paper['abstract']}\n\n"
        
        for book in books:
            combined_content += f"Book: {book['title']}\n{book['description']}\n\n"
        
        # Generate study questions from combined content
        if combined_content:
            questions = await content_extractor.generate_study_questions(combined_content, difficulty)
        else:
            # Fallback to sample questions
            questions = [
                {
                    "question": f"What is the definition of {topic}?",
                    "type": "definition",
                    "difficulty": difficulty,
                    "answer": f"{topic} is a systematic approach to understanding and applying specific principles in a structured manner."
                },
                {
                    "question": f"Name three key concepts in {topic}",
                    "type": "comprehension",
                    "difficulty": difficulty,
                    "answer": f"The key concepts include: fundamental principles, practical applications, and advanced techniques."
                },
                {
                    "question": f"How would you explain {topic} to a beginner?",
                    "type": "application",
                    "difficulty": difficulty,
                    "answer": f"{topic} can be understood as a framework that helps organize thoughts and actions in a logical sequence."
                }
            ]
        
        # Create flashcards
        flashcards = []
        for i, question_data in enumerate(questions[:card_count]):
            flashcards.append({
                "id": i + 1,
                "front": question_data["question"],
                "back": question_data["answer"],
                "difficulty": difficulty,
                "category": topic,
                "type": question_data.get("type", "general"),
                "created_at": datetime.now().isoformat(),
                "source": "AI Generated" if combined_content else "Template"
            })
        
        # If we need more cards, add template-based ones
        while len(flashcards) < card_count:
            i = len(flashcards)
            template_questions = [
                f"What are the main applications of {topic}?",
                f"Describe a common problem in {topic} and its solution",
                f"What are the best practices for {topic}?",
                f"How has {topic} evolved over time?",
                f"What skills are essential for mastering {topic}?"
            ]
            
            template_answers = [
                f"Main applications include: problem-solving, decision-making, and innovation in various fields.",
                f"A common problem is the lack of structured approach, which can be solved through systematic planning and execution.",
                f"Best practices include: continuous learning, practical application, and seeking feedback from experts.",
                f"{topic} has evolved from basic principles to sophisticated methodologies with technological integration.",
                f"Essential skills include: analytical thinking, creativity, technical proficiency, and communication abilities."
            ]
            
            if i < len(template_questions):
                flashcards.append({
                    "id": i + 1,
                    "front": template_questions[i],
                    "back": template_answers[i],
                    "difficulty": difficulty,
                    "category": topic,
                    "type": "template",
                    "created_at": datetime.now().isoformat(),
                    "source": "Template"
                })
        
    except Exception as e:
        print(f"Error generating flashcards: {e}")
        # Fallback to basic flashcards
        flashcards = []
        for i in range(card_count):
            flashcards.append({
                "id": i + 1,
                "front": f"Question {i+1} about {topic}",
                "back": f"Answer {i+1} about {topic}",
                "difficulty": difficulty,
                "category": topic,
                "type": "fallback",
                "created_at": datetime.now().isoformat(),
                "source": "Fallback"
            })
    
    finally:
        await content_extractor.close()
    
    return {
        "topic": topic,
        "difficulty": difficulty,
        "total_cards": len(flashcards),
        "flashcards": flashcards,
        "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "sources_used": {
            "papers": len(papers) if 'papers' in locals() else 0,
            "books": len(books) if 'books' in locals() else 0
        }
    }


def _get_dashboard_data(user_id: str) -> Dict[str, Any]:
    """Get learning dashboard data for a user."""
    
    # Sample dashboard data - in real implementation, this would fetch from database
    dashboard_data = {
        "user_id": user_id,
        "last_updated": datetime.now().isoformat(),
        "stats": {
            "total_sessions": 12,
            "cards_studied": 156,
            "topics_learned": 5,
            "study_streak": 7,
            "average_accuracy": 78
        },
        "recent_sessions": [
            {
                "topic": "Python Programming",
                "date": "2024-01-15",
                "cards_completed": 20,
                "accuracy": 85
            },
            {
                "topic": "Machine Learning",
                "date": "2024-01-14",
                "cards_completed": 15,
                "accuracy": 72
            },
            {
                "topic": "Data Structures",
                "date": "2024-01-13",
                "cards_completed": 18,
                "accuracy": 80
            }
        ],
        "current_roadmaps": [
            {
                "topic": "Web Development",
                "progress": 65,
                "next_milestone": "Advanced JavaScript"
            },
            {
                "topic": "Data Science",
                "progress": 40,
                "next_milestone": "Statistical Analysis"
            }
        ],
        "achievements": [
            {
                "title": "Week Warrior",
                "description": "7-day study streak",
                "earned_date": "2024-01-15"
            },
            {
                "title": "Knowledge Seeker",
                "description": "Completed 5 topics",
                "earned_date": "2024-01-10"
            }
        ]
    }
    
    return dashboard_data


def _resource_description(widget: LearningWidget) -> str:
    return f"{widget.title} widget markup"


def _tool_meta(widget: LearningWidget) -> Dict[str, Any]:
    return {
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True
    }


def _embedded_widget_resource(widget: LearningWidget) -> types.EmbeddedResource:
    return types.EmbeddedResource(
        type="resource",
        resource=types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
            title=widget.title,
        ),
    )


@mcp._mcp_server.list_tools()
async def _list_tools() -> List[types.Tool]:
    return [
        types.Tool(
            name=widget.identifier,
            title=widget.title,
            description=widget.title,
            inputSchema=deepcopy(_get_input_schema(widget.identifier)),
            _meta=_tool_meta(widget),
            annotations={
                "destructiveHint": False,
                "openWorldHint": False,
                "readOnlyHint": True,
            },
        )
        for widget in widgets
    ]


def _get_input_schema(tool_name: str) -> Dict[str, Any]:
    """Get input schema for a specific tool."""
    if tool_name == "learning-roadmap":
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic you want to learn about",
                },
                "current_level": {
                    "type": "string",
                    "enum": ["beginner", "intermediate", "advanced"],
                    "description": "Your current knowledge level",
                },
                "learning_style": {
                    "type": "string",
                    "enum": ["visual", "auditory", "kinesthetic", "reading"],
                    "description": "Your preferred learning style",
                },
                "time_commitment": {
                    "type": "string",
                    "enum": ["low", "medium", "high"],
                    "description": "Your time commitment level",
                }
            },
            "required": ["topic"],
            "additionalProperties": False,
        }
    elif tool_name == "flashcard-session":
        return {
            "type": "object",
            "properties": {
                "topic": {
                    "type": "string",
                    "description": "The topic for flashcard practice",
                },
                "difficulty": {
                    "type": "string",
                    "enum": ["easy", "medium", "hard", "mixed"],
                    "description": "Difficulty level",
                },
                "card_count": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 50,
                    "description": "Number of flashcards to generate",
                }
            },
            "required": ["topic"],
            "additionalProperties": False,
        }
    elif tool_name == "learning-dashboard":
        return {
            "type": "object",
            "properties": {
                "user_id": {
                    "type": "string",
                    "description": "User identifier for session persistence",
                }
            },
            "additionalProperties": False,
        }
    else:
        return {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }


@mcp._mcp_server.list_resources()
async def _list_resources() -> List[types.Resource]:
    return [
        types.Resource(
            name=widget.title,
            title=widget.title,
            uri=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


@mcp._mcp_server.list_resource_templates()
async def _list_resource_templates() -> List[types.ResourceTemplate]:
    return [
        types.ResourceTemplate(
            name=widget.title,
            title=widget.title,
            uriTemplate=widget.template_uri,
            description=_resource_description(widget),
            mimeType=MIME_TYPE,
            _meta=_tool_meta(widget),
        )
        for widget in widgets
    ]


async def _handle_read_resource(req: types.ReadResourceRequest) -> types.ServerResult:
    widget = WIDGETS_BY_URI.get(str(req.params.uri))
    if widget is None:
        return types.ServerResult(
            types.ReadResourceResult(
                contents=[],
                _meta={"error": f"Unknown resource: {req.params.uri}"},
            )
        )

    contents = [
        types.TextResourceContents(
            uri=widget.template_uri,
            mimeType=MIME_TYPE,
            text=widget.html,
            _meta=_tool_meta(widget),
        )
    ]

    return types.ServerResult(types.ReadResourceResult(contents=contents))


async def _call_tool_request(req: types.CallToolRequest) -> types.ServerResult:
    widget = WIDGETS_BY_ID.get(req.params.name)
    if widget is None:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Unknown tool: {req.params.name}",
                    )
                ],
                isError=True,
            )
        )

    arguments = req.params.arguments or {}
    
    try:
        if widget.identifier == "learning-roadmap":
            payload = RoadmapInput.model_validate(arguments)
            structured_content = await _generate_learning_roadmap(
                payload.topic, payload.current_level, payload.learning_style, payload.time_commitment
            )
        elif widget.identifier == "flashcard-session":
            payload = FlashcardInput.model_validate(arguments)
            structured_content = await _generate_flashcards(
                payload.topic, payload.difficulty, payload.card_count
            )
        elif widget.identifier == "learning-dashboard":
            payload = DashboardInput.model_validate(arguments)
            structured_content = _get_dashboard_data(payload.user_id)
        else:
            structured_content = {"message": "Tool executed successfully"}
            
    except ValidationError as exc:
        return types.ServerResult(
            types.CallToolResult(
                content=[
                    types.TextContent(
                        type="text",
                        text=f"Input validation error: {exc.errors()}",
                    )
                ],
                isError=True,
            )
        )

    widget_resource = _embedded_widget_resource(widget)
    meta: Dict[str, Any] = {
        "openai.com/widget": widget_resource.model_dump(mode="json"),
        "openai/outputTemplate": widget.template_uri,
        "openai/toolInvocation/invoking": widget.invoking,
        "openai/toolInvocation/invoked": widget.invoked,
        "openai/widgetAccessible": True,
        "openai/resultCanProduceWidget": True,
    }

    return types.ServerResult(
        types.CallToolResult(
            content=[
                types.TextContent(
                    type="text",
                    text=widget.response_text,
                )
            ],
            structuredContent=structured_content,
            _meta=meta
        )
    )


mcp._mcp_server.request_handlers[types.CallToolRequest] = _call_tool_request
mcp._mcp_server.request_handlers[types.ReadResourceRequest] = _handle_read_resource


app = mcp.streamable_http_app()

try:
    from starlette.middleware.cors import CORSMiddleware

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=False,
    )
except Exception:
    pass


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=9000)
