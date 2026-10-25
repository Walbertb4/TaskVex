"""A limited, RAM-only conversation record of the same desktop conversation.

Live socket is temporary; This recording belongs to TextChat. Old messages new tool
The request or provider is not a functionCall object. To summarize model/API
does not run; leaves the oldest turns. Permanent user profile/not is not a repository.
"""
import json


class ConversationMemory:
    """Use TextChat under single chat lock; It does not have its own worker/lock."""

    def __init__(self):
        self._turns: list[dict] = []

    def clear(self):
        """Leave only the RAM register in the new chat/closing/key replacement."""
        self._turns.clear()

    def snapshot(self) -> str:
        """Immutable data copy; In an empty record, no content is sent to the provider."""
        return json.dumps(self._turns, ensure_ascii=False) if self._turns else ''

    def remember(self, user: str, report: dict):
        """Store text and limited tool status without assuming the result is successful.

        The actual input_text is used in the voice message; raw PCM, secret repository,
        tool arguments/result.data or resume handle are not included in this record.
        The truncated response remains truncated. 12 rounds / 16,000 JSON characters
        If the limit is exceeded, the oldest round is completely removed and no new instructions are generated.
        """
        def clip(value):
            return value[:2000] + (' [truncated]' if len(value) > 2000 else '') if isinstance(value, str) else ''

        tools = [{'name': item.get('name'), 'status': item.get('status'),
                  'verified': (item.get('result') or {}).get('verified') is True}
                 for item in report.get('tool_results', [])[:8]]
        if not user and not report.get('text') and not tools:
            return
        self._turns.append({'user': clip(user), 'assistant': clip(report.get('text')),
            'outcome': 'unknown' if report.get('unknown') else 'stopped' if report.get('stopped')
                       else 'completed' if report.get('ok') else 'failed', 'tools': tools})
        while len(self._turns) > 12 or len(self.snapshot()) > 16000:
            self._turns.pop(0)
