"""Single owner of local system metrics: model tool and UI read the same instance.

Windows' documented APIs are used; new thread, shell command or external service
not initialized. Windows PDH counter is used for GPU.
The two-second common sample interval calculates the CPU difference. first CPU
instance and unsupported metrics are None; Missing data is not presented as zero.
"""
import ctypes as c
from ctypes import wintypes as w
from copy import deepcopy
import ntpath
import os
import platform
import shutil
import sys
from threading import Lock
from time import monotonic

from app.core.contracts import TaskStatus, ToolContext, ToolError, ToolResult
from app.tools.local.windows_gpu import WindowsGpu
from app.tools.local.network import Network


class _Memory(c.Structure):
    """MEMORYSTATUSEX: size field must be set before the call."""
    _fields_ = [('length',w.DWORD),('load',w.DWORD)] + [(name,c.c_ulonglong) for name in
        ('total','available','page_total','page_available','virtual_total','virtual_available','extended')]


class _Power(c.Structure):
    """SYSTEM_POWER_STATUS: 255 means unknown percentage, 128 means no battery."""
    _fields_ = [(name,w.BYTE) for name in ('ac','flags','percent','saver')] + [
        ('remaining',w.DWORD),('full',w.DWORD)]


def _read_windows() -> dict:
    """Get raw meters; reading the document title or full path of the active window.

    Each measurement may fail independently. Active application only executable
    It is indicated by the name; None remains in the protected process. Handle closes in all cases.
    """
    if os.name != 'nt':
        return {}
    kernel=c.WinDLL('kernel32',use_last_error=True)
    user=c.WinDLL('user32',use_last_error=True)
    signatures=[
        (kernel.GetSystemTimes,[c.POINTER(w.FILETIME)]*3,w.BOOL),
        (kernel.GlobalMemoryStatusEx,[c.POINTER(_Memory)],w.BOOL),
        (kernel.GetSystemPowerStatus,[c.POINTER(_Power)],w.BOOL),
        (kernel.OpenProcess,[w.DWORD,w.BOOL,w.DWORD],w.HANDLE),
        (kernel.QueryFullProcessImageNameW,[w.HANDLE,w.DWORD,w.LPWSTR,c.POINTER(w.DWORD)],w.BOOL),
        (kernel.CloseHandle,[w.HANDLE],w.BOOL),
        (user.GetForegroundWindow,[],w.HWND),
        (user.GetWindowThreadProcessId,[w.HWND,c.POINTER(w.DWORD)],w.DWORD)]
    for fn,args,result in signatures:
        fn.argtypes,fn.restype=args,result
    raw={}
    idle,kern,usr=w.FILETIME(),w.FILETIME(),w.FILETIME()
    if kernel.GetSystemTimes(c.byref(idle),c.byref(kern),c.byref(usr)):
        raw['times']=tuple((value.dwHighDateTime<<32)|value.dwLowDateTime for value in (idle,kern,usr))
    memory=_Memory();memory.length=c.sizeof(memory)
    if kernel.GlobalMemoryStatusEx(c.byref(memory)) and memory.total>0:
        raw.update(memory_total=memory.total,memory_used=memory.total-memory.available)
    power=_Power()
    if kernel.GetSystemPowerStatus(c.byref(power)):
        raw['battery_present']=None if power.flags==255 else not bool(power.flags & 128)
        if raw['battery_present'] and power.percent<=100:
            raw['battery_percent']=power.percent
        raw['ac_connected']=None if power.ac==255 else power.ac==1
    disk_root=ntpath.splitdrive(sys.executable)[0]+'\\'
    try:
        disk=shutil.disk_usage(disk_root)
        raw.update(disk_total=disk.total,disk_used=disk.used,disk_volume=ntpath.splitdrive(disk_root)[0])
    except OSError:
        pass
    window=user.GetForegroundWindow()
    if window:
        pid=w.DWORD()
        user.GetWindowThreadProcessId(window,c.byref(pid))
        handle=kernel.OpenProcess(0x1000,False,pid.value) if pid.value else None
        if handle:
            try:
                path=c.create_unicode_buffer(32768);length=w.DWORD(len(path))
                if kernel.QueryFullProcessImageNameW(handle,0,path,c.byref(length)):
                    raw['active_process']=ntpath.basename(path.value)
            finally:
                kernel.CloseHandle(handle)
    return raw


class Telemetry:
    """Single reference to cache/CPU; UI polling does not constantly grow the task log."""
    def __init__(self, *, reader=None, clock=None, gpu_reader=None, network_reader=None):
        self._reader=reader or _read_windows
        self._gpu_reader=gpu_reader or WindowsGpu()
        self._network=Network(network_reader)
        self._clock=clock or monotonic
        self._lock=Lock()
        self._previous=None
        self._sample=None

    def close(self):
        """Drop local GPU counter resource if any when Window/core shuts down."""
        with self._lock:
            close=getattr(self._gpu_reader,'close',None)
            if close is not None:
                close()

    def snapshot(self) -> dict:
        """Measure every two seconds at most; The returning copy cannot change the owner's status."""
        with self._lock:
            now=self._clock()
            if self._sample is not None and now-self._sample['sampled_at']<2:
                return deepcopy(self._sample)
            data={'os':platform.system() or None,'os_release':platform.release() or None,
                'architecture':platform.machine() or None,'logical_cpu_count':os.cpu_count(),
                'cpu_percent':None,'memory_percent':None,'memory_total':None,'memory_used':None,
                'battery_percent':None,'battery_present':None,'ac_connected':None,
                'disk_total':None,'disk_used':None,'disk_volume':None,'active_process':None,
                'gpu_percent':None,'cpu_temperature':None,'gpu_temperature':None,'sampled_at':now}
            try:
                raw=self._reader()
            except OSError:
                raw={}
            times=raw.get('times')
            if times is not None and self._previous is not None and type(data['logical_cpu_count']) is int and 0<data['logical_cpu_count']<=64:
                idle=times[0]-self._previous[0]
                total=(times[1]-self._previous[1])+(times[2]-self._previous[2])
                if total>0 and 0<=idle<=total:
                    data['cpu_percent']=round(100*(total-idle)/total,1)
            # The failed instance does not carry the old CPU reference and the old visible value.
            self._previous=times
            for key in data:
                if key in raw:
                    data[key]=raw[key]
            gpu=self._gpu_reader()
            data.update({key:gpu.get(key) for key in ('gpu_source','gpu_status','gpu_devices')})
            data['gpu_sampled_at']=now
            devices=data['gpu_devices'] or []
            data['gpu_percent']=max((device['utilization_percent'] for device in devices),default=None)
            data.update(self._network.sample(now))
            total=data['memory_total'];used=data['memory_used']
            if total and used is not None and 0<=used<=total:
                data['memory_percent']=round(100*used/total,1)
            data['unavailable']=[key for key in ('cpu_percent','memory_percent','battery_percent',
                'disk_total','active_process','gpu_percent','cpu_temperature','gpu_temperature',
                'network_link','network_receive_bps','network_send_bps','network_ping_ms','network_wifi_signal') if data[key] is None]
            self._sample=data
            return deepcopy(data)


def system_status(arguments: dict, context: ToolContext, *, monitor: Telemetry | None = None) -> ToolResult:
    """Read-only with no parameters; The model follows from the existing registry/policy/TaskManager.

    verified indicates that the sample has been read; Unavailable fields are not counted as measured.
    Failure to read the immediate source makes a single metric None; Even platform information
    If it cannot be read, a controlled error is returned. A canceled task does not start a new measurement.
    """
    if arguments:
        return ToolResult(task_id=context.task_id,status=TaskStatus.FAILED,
            error=ToolError(code='invalid_arguments',message='System status accepts no arguments'))
    if context.cancel_event.is_set():
        return ToolResult(task_id=context.task_id,status=TaskStatus.CANCELLED)
    try:
        data=(monitor or Telemetry()).snapshot()
    except OSError:
        return ToolResult(task_id=context.task_id,status=TaskStatus.FAILED,
            error=ToolError(code='system_unavailable',message='System information is unavailable'))
    return ToolResult(task_id=context.task_id,status=TaskStatus.SUCCEEDED,verified=True,
        data=data,evidence={'source':'Win32+python.platform','unavailable':data['unavailable']})
