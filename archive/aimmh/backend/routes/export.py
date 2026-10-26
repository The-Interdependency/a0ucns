# ratios: loc_comments=106:1 imports_exports=12:1 calls_definitions=47:1
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import Response
from datetime import datetime, timezone
from typing import Literal
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.units import inch
import json

from db import db
from services.auth import get_current_user, get_user_id

router = APIRouter(prefix="/api", tags=["export"])


@router.get("/conversations/{conversation_id}/export")
async def export_conversation(
    conversation_id: str,
    format: Literal["json", "txt", "pdf"] = "json",
    current_user: dict = Depends(get_current_user)
):
    """Export conversation in different formats"""
    messages = await db.messages.find(
        {"conversation_id": conversation_id, "user_id": get_user_id(current_user)},
        {"_id": 0}
    ).sort("timestamp", 1).to_list(1000)

    if not messages:
        raise HTTPException(status_code=404, detail="Conversation not found")

    conversation = await db.conversations.find_one(
        {"id": conversation_id, "user_id": get_user_id(current_user)},
        {"_id": 0}
    )
    title = conversation.get("title", "Untitled Conversation") if conversation else "Untitled Conversation"

    if format == "json":
        export_data = {
            "conversation_id": conversation_id,
            "title": title,
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "message_count": len(messages),
            "messages": messages
        }
        return Response(
            content=json.dumps(export_data, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f'attachment; filename="conversation-{conversation_id[:8]}.json"'}
        )

    elif format == "txt":
        lines = [
            f"Conversation: {title}",
            f"Exported: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
            f"Messages: {len(messages)}",
            "=" * 60,
            ""
        ]
        for msg in messages:
            timestamp = msg.get('timestamp', 'N/A')
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass
            if msg['role'] == 'user':
                lines.append(f"[{timestamp}] USER:")
                lines.append(msg['content'])
            else:
                lines.append(f"[{timestamp}] {msg['model'].upper()}:")
                lines.append(msg['content'])
            lines.append("")

        content = "\n".join(lines)
        return Response(
            content=content,
            media_type="text/plain",
            headers={"Content-Disposition": f'attachment; filename="conversation-{conversation_id[:8]}.txt"'}
        )

    elif format == "pdf":
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        styles = getSampleStyleSheet()
        story = []

        title_style = ParagraphStyle('CustomTitle', parent=styles['Heading1'], fontSize=18, spaceAfter=12)
        story.append(Paragraph(f"Conversation: {title}", title_style))
        story.append(Paragraph(f"Exported: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}", styles['Normal']))
        story.append(Paragraph(f"Messages: {len(messages)}", styles['Normal']))
        story.append(Spacer(1, 0.3 * inch))

        for msg in messages:
            timestamp = msg.get('timestamp', 'N/A')
            if isinstance(timestamp, str):
                try:
                    dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                    timestamp = dt.strftime('%Y-%m-%d %H:%M:%S')
                except Exception:
                    pass

            if msg['role'] == 'user':
                header = f"<b>[{timestamp}] USER:</b>"
            else:
                header = f"<b>[{timestamp}] {msg['model'].upper()}:</b>"

            story.append(Paragraph(header, styles['Normal']))
            content = msg['content'].replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            content = content.replace('\n', '<br/>')
            story.append(Paragraph(content, styles['Normal']))
            story.append(Spacer(1, 0.2 * inch))

        doc.build(story)
        buffer.seek(0)

        return Response(
            content=buffer.getvalue(),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="conversation-{conversation_id[:8]}.pdf"'}
        )
# ratios: loc_comments=106:1 imports_exports=12:1 calls_definitions=47:1
