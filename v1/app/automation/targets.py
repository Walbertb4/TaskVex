"""RAM-only target references shared by future DOM/UIA/visual adapters.

Trusted adapters supply real lifetime/document generations and read-only refresh
callbacks. This owner neither discovers targets nor clicks, captures or executes.
Bare HWND/PID values without lifetime proof must not be presented as safe identities.
"""

from dataclasses import dataclass
import json
import math
from threading import Event, Lock
from time import monotonic
from typing import Callable
from uuid import uuid4

from app.core.contracts import ContractError, ToolRequest
from app.policy.task_scope import AccessRequirement, TaskScopes


class TargetError(ContractError):
    """Explicit pre-action resolution status, without provider/user content."""

    def __init__(self, code: str) -> None:
        if code not in {'target_no_match', 'target_unsupported', 'target_permission_denied',
                        'target_stale', 'target_unavailable', 'target_cancelled', 'target_capacity'}:
            raise ContractError('Invalid target resolution status')
        self.code = code
        super().__init__(code)


def can_fallback(error: TargetError, *, dispatched: bool | None) -> bool:
    """Only explicit pre-dispatch absence/unsupported can select another resolver.

    True means dispatched; None means uncertain. Neither permits replay/fallback.
    This predicate is not an execution router or permission to run another tool.
    """
    return dispatched is False and error.code in {'target_no_match', 'target_unsupported'}


@dataclass(frozen=True, kw_only=True)
class FrameGeometry:
    """Physical desktop bounds of the exact captured region and image dimensions.

    DPI is metadata, not another scaling multiplier. Adapters must reject logical/
    virtualized coordinates rather than relabel them as physical. No JPEG is stored.
    """

    frame_id: str
    captured_at: float
    coordinate_space: str
    screen_x: int
    screen_y: int
    screen_width: int
    screen_height: int
    frame_width: int
    frame_height: int
    dpi: int

    def __post_init__(self) -> None:
        if not isinstance(self.frame_id, str) or not self.frame_id.strip():
            raise ContractError('Expected a host-issued frame ID')
        if (type(self.captured_at) not in (int, float) or not math.isfinite(self.captured_at)
                or self.captured_at < 0 or self.coordinate_space != 'physical_desktop'):
            raise ContractError('Expected capture time and proven physical desktop coordinates')
        if (any(type(v) is not int for v in (self.screen_x, self.screen_y))
                or any(type(v) is not int or v <= 0 for v in (
                    self.screen_width, self.screen_height, self.frame_width, self.frame_height, self.dpi))):
            raise ContractError('Expected physical bounds, positive image dimensions and DPI')

    def point(self, x: int, y: int) -> tuple[int, int]:
        """Map one in-image pixel to the same physical capture region, never a click."""
        if (type(x) is not int or type(y) is not int
                or not 0 <= x < self.frame_width or not 0 <= y < self.frame_height):
            raise ContractError('Point is outside the referenced image')
        return (self.screen_x + x * self.screen_width // self.frame_width,
                self.screen_y + y * self.screen_height // self.frame_height)


@dataclass(frozen=True, kw_only=True)
class TargetSnapshot:
    """Adapter-observed identity/version; no labels, screenshot or document body.

    instance_id binds process/connection lifetime. window_id must distinguish window
    lifetimes, not just recycled handles. generation covers observable target/content
    changes; DOM adapters also bind tab/document and, when relevant, element IDs.
    """

    application_id: str
    instance_id: str
    window_id: str
    generation: str
    tab_id: str | None = None
    document_id: str | None = None
    element_id: str | None = None
    foreground: bool | None = None
    geometry: FrameGeometry | None = None

    def __post_init__(self) -> None:
        required = (self.application_id, self.instance_id, self.window_id, self.generation)
        optional = (self.tab_id, self.document_id, self.element_id)
        if (any(not isinstance(v, str) or not v.strip() for v in required)
                or any(v is not None and (not isinstance(v, str) or not v.strip()) for v in optional)
                or (self.tab_id is None) != (self.document_id is None)
                or (self.foreground is not None and type(self.foreground) is not bool)
                or (self.geometry is not None and not isinstance(self.geometry, FrameGeometry))):
            raise ContractError('Expected complete host-observed target identity/version')

    @property
    def resource_id(self) -> str:
        """Bind grants to the real window/tab lifetime, not a mutable button/frame."""
        return json.dumps([self.application_id, self.instance_id, self.window_id, self.tab_id],
                          ensure_ascii=True, separators=(',', ':'))


@dataclass(frozen=True)
class _Reference:
    authorization_id: str
    principal: str
    snapshot: TargetSnapshot
    reader: Callable[[Event], TargetSnapshot]


class TargetReferences:
    """One bounded reference store; every action resolution reobserves its target.

    Readers run outside the lock and cannot issue authority. Concurrent replacement,
    scope end, cancellation or identity/version changes invalidate resolution. The
    host still performs its final check at the actual driver/input boundary.
    """

    def __init__(self, scopes: TaskScopes, *, capacity: int = 256) -> None:
        if not isinstance(scopes, TaskScopes) or type(capacity) is not int or capacity < 1:
            raise ContractError('Expected scope owner and positive live-reference capacity')
        self._scopes, self._capacity = scopes, capacity
        self._lock = Lock()
        self._references: dict[str, _Reference] = {}

    def issue(self, authorization_id: str, principal: str, snapshot: TargetSnapshot,
              reader: Callable[[Event], TargetSnapshot]) -> str:
        """Register trusted observation/refresh only; do not grant control of it."""
        if not isinstance(snapshot, TargetSnapshot) or not callable(reader):
            raise ContractError('Expected a snapshot and read-only refresh callback')
        with self._lock:
            if not self._scopes.active(authorization_id, principal):
                raise TargetError('target_permission_denied')
            # Bound RAM to current scopes/latest observations, not all task history.
            for ref_id, old in list(self._references.items()):
                same_context = (old.authorization_id == authorization_id
                    and old.snapshot.resource_id == snapshot.resource_id)
                obsolete = same_context and (old.snapshot.element_id == snapshot.element_id
                    or old.snapshot.document_id != snapshot.document_id
                    or (old.snapshot.geometry is not None and snapshot.geometry is not None
                        and old.snapshot.geometry != snapshot.geometry))
                if obsolete or not self._scopes.active(old.authorization_id, old.principal):
                    del self._references[ref_id]
            if len(self._references) >= self._capacity:
                raise TargetError('target_capacity')
            ref_id = uuid4().hex
            self._references[ref_id] = _Reference(authorization_id, principal, snapshot, reader)
            return ref_id

    def _get(self, reference_id: str, request: ToolRequest) -> _Reference:
        if not isinstance(reference_id, str) or not isinstance(request, ToolRequest):
            raise ContractError('Expected a target reference and trusted request')
        if (request.authorization_id is None or request.source != 'desktop'
                or not self._scopes.active(request.authorization_id, request.principal)):
            raise TargetError('target_permission_denied')
        ref = self._references.get(reference_id)
        if ref is None:
            raise TargetError('target_stale')
        if ref.authorization_id != request.authorization_id or ref.principal != request.principal:
            raise TargetError('target_permission_denied')
        return ref

    def release(self, reference_id: str, request: ToolRequest) -> None:
        """Drop a closed/paged-out observation so capacity is not a lifetime limit."""
        with self._lock:
            self._get(reference_id, request)
            del self._references[reference_id]

    def release_scope(self, authorization_id: str) -> None:
        """Host lifecycle cleanup; permission remains solely owned by TaskScopes."""
        with self._lock:
            for ref_id, ref in list(self._references.items()):
                if ref.authorization_id == authorization_id:
                    del self._references[ref_id]

    def access(self, reference_id: str, request: ToolRequest, *, action: str,
               high_impact: bool = False, physical_input: bool = False) -> AccessRequirement:
        """Policy metadata only; resource permission still requires a separate grant."""
        with self._lock:
            ref = self._get(reference_id, request)
            kind = 'browser' if ref.snapshot.tab_id is not None else 'window'
            return AccessRequirement(resources=frozenset({(kind, ref.snapshot.resource_id, action)}),
                                     high_impact=high_impact, physical_input=physical_input)

    def resolve(self, reference_id: str, request: ToolRequest, cancel: Event, *,
                physical_input: bool = False) -> TargetSnapshot:
        """Reobserve before use; failures never manufacture a target or new permission."""
        if type(physical_input) is not bool or not isinstance(cancel, Event):
            raise ContractError('Expected cancellation event and physical-input flag')
        with self._lock:
            ref = self._get(reference_id, request)
        if cancel.is_set():
            raise TargetError('target_cancelled')
        try:
            current = ref.reader(cancel)
        except TargetError:
            raise
        except InterruptedError:
            raise TargetError('target_cancelled') from None
        except Exception:
            raise TargetError('target_unavailable') from None
        with self._lock:
            if cancel.is_set():
                raise TargetError('target_cancelled')
            if self._get(reference_id, request) is not ref:
                raise TargetError('target_stale')
            if not isinstance(current, TargetSnapshot):
                raise TargetError('target_unavailable')
            if current != ref.snapshot:
                raise TargetError('target_stale')
            if physical_input and current.foreground is not True:
                raise TargetError('target_unsupported' if current.foreground is None else 'target_stale')
            return current

    def resolve_point(self, reference_id: str, request: ToolRequest, cancel: Event,
                      x: int, y: int, *, max_frame_age: float) -> tuple[int, int]:
        """Map a current focused frame only; caller must still pass policy/input checks."""
        if type(max_frame_age) not in (int, float) or not math.isfinite(max_frame_age) or max_frame_age <= 0:
            raise ContractError('Expected an explicit positive frame-age budget')
        snapshot = self.resolve(reference_id, request, cancel, physical_input=True)
        if snapshot.geometry is None:
            raise TargetError('target_unsupported')
        age = monotonic() - snapshot.geometry.captured_at
        if not 0 <= age <= max_frame_age:
            raise TargetError('target_stale')
        return snapshot.geometry.point(x, y)
