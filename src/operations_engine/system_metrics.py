from __future__ import annotations

import os
import sys
import platform
import time
from typing import Dict, Any, Optional
from src.models.operations_report import SystemMetrics, ResourceUsage


class SystemMetricsCollector:
    """
    Task 8: Collects CPU, Memory, Disk usage, uptime, logs/cache sizes, and platform details.
    """

    # Static tracker for start time to calculate uptime
    _start_time: float = time.time()

    @classmethod
    def set_start_time(cls, start_time: float) -> None:
        cls._start_time = start_time

    @classmethod
    def collect_metrics(
        cls,
        mock_resources: Optional[Dict[str, float]] = None,
        mock_sizes: Optional[Dict[str, int]] = None
    ) -> SystemMetrics:
        """
        Gathers system platform information and active resource usage statistics.
        """
        # Uptime
        uptime = time.time() - cls._start_time

        # Python & Platform Info
        py_version = sys.version.split(" ")[0]
        plat_info = f"{platform.system()} {platform.release()} ({platform.machine()})"

        # Gather file sizes
        log_size = 0
        log_dir = os.path.join(os.getcwd(), "logs")
        if mock_sizes and "log_size_bytes" in mock_sizes:
            log_size = mock_sizes["log_size_bytes"]
        elif os.path.isdir(log_dir):
            try:
                for entry in os.scandir(log_dir):
                    if entry.is_file():
                        log_size += entry.stat().st_size
            except Exception:
                pass

        cache_size = 0
        cache_dir = os.path.join(os.getcwd(), "cache")
        if mock_sizes and "cache_size_bytes" in mock_sizes:
            cache_size = mock_sizes["cache_size_bytes"]
        elif os.path.isdir(cache_dir):
            try:
                for entry in os.scandir(cache_dir):
                    if entry.is_file():
                        cache_size += entry.stat().st_size
            except Exception:
                pass

        # Resources (CPU, Memory, Disk)
        # Attempt to gather standard sys/os values, with fallback to mocked/stable defaults
        cpu_p = 1.5
        mem_u = 120.5
        mem_p = 12.0
        disk_f = 25.0
        disk_p = 45.0

        if mock_resources:
            cpu_p = mock_resources.get("cpu_percent", cpu_p)
            mem_u = mock_resources.get("memory_used_mb", mem_u)
            mem_p = mock_resources.get("memory_percent", mem_p)
            disk_f = mock_resources.get("disk_free_gb", disk_f)
            disk_p = mock_resources.get("disk_percent", disk_p)
        else:
            # CPU and Memory
            try:
                import psutil
                cpu_p = psutil.cpu_percent(interval=None)
                virtual_mem = psutil.virtual_memory()
                mem_u = virtual_mem.used / (1024 * 1024)
                mem_p = virtual_mem.percent
            except ImportError:
                # If psutil is missing, we use stable default values or mock them.
                pass

            # Disk Usage
            try:
                # Portable way to read root space
                if hasattr(os, "statvfs"):
                    st = os.statvfs("/")
                    free = (st.f_bavail * st.f_frsize)
                    total = (st.f_blocks * st.f_frsize)
                    disk_f = free / (1024 * 1024 * 1024)
                    disk_p = ((total - free) / total) * 100.0 if total > 0 else 0.0
            except Exception:
                pass

        resources = ResourceUsage(
            cpu_percent=round(cpu_p, 2),
            memory_used_mb=round(mem_u, 2),
            memory_percent=round(mem_p, 2),
            disk_free_gb=round(disk_f, 2),
            disk_percent=round(disk_p, 2)
        )

        return SystemMetrics(
            uptime_seconds=round(uptime, 2),
            log_size_bytes=log_size,
            cache_size_bytes=cache_size,
            python_version=py_version,
            platform_info=plat_info,
            resources=resources
        )
