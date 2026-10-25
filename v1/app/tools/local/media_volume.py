"""Core Audio adapter for one unambiguously matched media application's volume.

Media owns execution and locking. This adapter opens render sessions temporarily,
matches the GSMTC source to a process identity, and releases every COM reference
on the calling thread. It never changes endpoint/master volume or keyboard volume.
"""
from contextlib import contextmanager, ExitStack
import ctypes as c
from ctypes import wintypes as w
import math
import ntpath
import os
from uuid import UUID


class _Guid(c.Structure):
    _fields_ = [('a',w.DWORD),('b',w.WORD),('d',w.WORD),('e',w.BYTE*8)]


def _guid(value):
    return _Guid.from_buffer_copy(UUID(value).bytes_le)


def _call(pointer, index, types=(), *args):
    """Invoke only fixed SDK vtable slots; no caller-selected interface or method."""
    table = c.cast(pointer,c.POINTER(c.POINTER(c.c_void_p))).contents
    result = c.WINFUNCTYPE(w.LONG,c.c_void_p,*types)(table[index])(pointer,*args)
    if result < 0:raise OSError('Core Audio call failed')
    return result


def _load_audio():
    if os.name != 'nt':raise OSError('Windows audio unavailable')
    ole = c.WinDLL('ole32')
    ole.CoCreateInstance.argtypes = [c.POINTER(_Guid),c.c_void_p,w.DWORD,c.POINTER(_Guid),c.POINTER(c.c_void_p)]
    ole.CoCreateInstance.restype = w.LONG
    ole.CoTaskMemFree.argtypes = [c.c_void_p]
    ole.CoTaskMemFree.restype = None
    return ole


def _process_identity(pid):
    """Read only executable name and optional Windows app ID; never expose paths."""
    dll = c.WinDLL('kernel32',use_last_error=True)
    for name,args,result in (
        ('OpenProcess',[w.DWORD,w.BOOL,w.DWORD],w.HANDLE),
        ('CloseHandle',[w.HANDLE],w.BOOL),
        ('QueryFullProcessImageNameW',[w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)],w.BOOL),
        ('GetApplicationUserModelId',[w.HANDLE,c.POINTER(w.UINT),w.LPWSTR],w.LONG)):
        function = getattr(dll,name)
        function.argtypes,function.restype = args,result
    handle = dll.OpenProcess(0x1000,False,pid)
    if not handle:return None,None
    try:
        size = w.DWORD(32768)
        path = c.create_unicode_buffer(size.value)
        name = ntpath.basename(path.value) if dll.QueryFullProcessImageNameW(handle,0,path,c.byref(size)) else None
        count = w.UINT()
        app = None
        if dll.GetApplicationUserModelId(handle,c.byref(count),None)==122 and 0<count.value<=32768:
            buffer = c.create_unicode_buffer(count.value)
            if dll.GetApplicationUserModelId(handle,c.byref(count),buffer)==0:app = buffer.value
        return name,app
    finally:dll.CloseHandle(handle)


def _matches(source, name, app):
    """Exact app IDs or executable/stem identity only; never fuzzy application names."""
    source = source.casefold()
    return source in {s.casefold() for s in (name,app,ntpath.splitext(name)[0] if name else None) if s}


def _active_sessions(found):
    """Prefer active streams over old inactive ones, without guessing among active matches."""
    return [session for session in found if session['active']] or found


@contextmanager
def _sessions(source):
    """Yield matching sessions on active render endpoints, with thread-local cleanup."""
    from winrt.runtime import ApartmentType, init_apartment, uninit_apartment
    with ExitStack() as stack:
        init_apartment(ApartmentType.MULTI_THREADED)
        stack.callback(uninit_apartment)
        ole = _load_audio()
        def take(pointer):
            if pointer.value:stack.callback(_call,pointer,2)
            return pointer
        def out(pointer,index,types=(),*args):
            value = c.c_void_p()
            try:_call(pointer,index,(*types,c.POINTER(c.c_void_p)),*args,c.byref(value))
            finally:take(value)
            return value
        def query(pointer,iid):return out(pointer,0,(c.POINTER(_Guid),),c.byref(_guid(iid)))
        def text(pointer,index):
            value = c.c_void_p()
            try:
                _call(pointer,index,(c.POINTER(c.c_void_p),),c.byref(value))
                return c.wstring_at(value) if value.value else ''
            finally:
                if value.value:ole.CoTaskMemFree(value)
        def count(pointer):
            value = w.UINT()
            _call(pointer,3,(c.POINTER(w.UINT),),c.byref(value))
            if value.value>4096:raise OSError('Audio collection limit exceeded')
            return value.value
        enumerator = c.c_void_p()
        try:
            result = ole.CoCreateInstance(c.byref(_guid('BCDE0395-E52F-467C-8E3D-C4579291692E')),None,23,
                c.byref(_guid('A95664D2-9614-4F35-A746-DE8DB63617E6')),c.byref(enumerator))
            if result<0:raise OSError('Audio enumerator unavailable')
        finally:take(enumerator)
        devices = out(enumerator,3,(c.c_int,w.DWORD),0,1)  # eRender, DEVICE_STATE_ACTIVE.
        found = []
        for i in range(count(devices)):
            device = out(devices,4,(w.UINT,),i)
            endpoint = text(device,5)
            manager = out(device,3,(c.POINTER(_Guid),w.DWORD,c.c_void_p),
                c.byref(_guid('77AA99A0-1BD6-484F-8BC7-2C654C9A9B6F')),23,None)
            sessions = out(manager,5)
            for j in range(count(sessions)):
                session = out(sessions,4,(c.c_int,),j)
                control = query(session,'BFB7FF88-7239-4FC9-8FA2-07C950BE9C6D')
                if _call(control,15)==0:continue  # System sounds are never a target.
                state,pid = c.c_int(),w.DWORD()
                _call(control,3,(c.POINTER(c.c_int),),c.byref(state))
                if state.value==2:continue  # Expired sessions cannot be controlled.
                if _call(control,14,(c.POINTER(w.DWORD),),c.byref(pid))!=0 or not pid.value:continue
                if not _matches(source,*_process_identity(pid.value)):continue
                volume = query(control,'87CE5498-68D6-44E5-9215-6DA47EF883D8')
                found.append({'target':(endpoint,text(control,13),pid.value),'pointer':volume,'active':state.value==1})
        # Old inactive browser sessions are not competing with a single active stream.
        yield _active_sessions(found)


def _sample(session):
    level,muted = c.c_float(),w.BOOL()
    _call(session['pointer'],4,(c.POINTER(c.c_float),),c.byref(level))
    _call(session['pointer'],6,(c.POINTER(w.BOOL),),c.byref(muted))
    if not math.isfinite(level.value) or not 0<=level.value<=1:raise OSError('Invalid session volume')
    return {'status':'available','percent':round(level.value*100,2),'muted':bool(muted.value),'_target':session['target']}


def read(source):
    """No match, missing source and multiple matches disable control; never use master volume."""
    if not isinstance(source,str) or not source:return {'status':'unavailable'}
    try:
        with _sessions(source) as sessions:
            if len(sessions)!=1:return {'status':'ambiguous' if sessions else 'unavailable'}
            return _sample(sessions[0])
    except (OSError,ImportError,RuntimeError):return {'status':'unavailable'}


def set_volume(source, target, percent, cancel, still_current) -> dict:
    """One absolute write to the observed session, followed by real readback.

    Revalidate identity and Stop immediately before dispatch. A failed readback after
    dispatch is unknown; it must not cause a second write or a master-volume fallback.
    """
    sent = False
    try:
        with _sessions(source) as sessions:
            if len(sessions)!=1 or sessions[0]['target']!=target:
                return {'status':'failed','code':'media_volume_target_changed'}
            session = sessions[0]
            before = _sample(session)
            if cancel.is_set():return {'status':'cancelled','code':'cancelled'}
            if not still_current():return {'status':'failed','code':'media_target_changed'}
            if cancel.is_set():return {'status':'cancelled','code':'cancelled'}
            if abs(before['percent']-percent)>.1:
                sent = True
                _call(session['pointer'],3,(c.c_float,c.c_void_p),percent/100,None)
            with _sessions(source) as confirmed:
                if len(confirmed)!=1 or confirmed[0]['target']!=target:
                    return {'status':'unknown' if sent else 'failed','code':'media_volume_target_changed'}
                after = _sample(confirmed[0])
            if not still_current() or abs(after['percent']-percent)>.1:
                return {'status':'unknown' if sent else 'failed','code':'media_volume_not_confirmed'}
            return {'status':'succeeded','code':'verified','evidence':{'read_back':True,'scope':'application',
                'percent':after['percent'],'dispatched':sent}}
    except (OSError,ImportError,RuntimeError):
        return {'status':'unknown' if sent else 'failed','code':'media_volume_unavailable'}
