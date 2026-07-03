# ratios: loc_comments=25:2 imports_exports=3:3 calls_definitions=0:3
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime


class EDCMMetrics(BaseModel):
    conversation_id: str
    constraint_mismatch_density: Optional[float] = None
    fixation_coefficient: Optional[float] = None
    escalation_gradient: Optional[float] = None
    context_drift_index: Optional[float] = None
    load_saturation_index: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class EDCMMetricsIngest(BaseModel):
    """Payload A0 sends to this app with EDCM analysis results"""
    conversation_id: str
    metrics: EDCMMetrics
    source: str = "agent_zero"
    timestamp: Optional[str] = None


class A0Config(BaseModel):
    """Per-user Agent Zero connection config"""
    mode: str = "local"  # "local" or "cloud"
    local_name: str = "local-device"
    local_url: str = "http://192.168.1.1"
    local_port: int = 8787
    cloud_url: str = ""
    api_key: str = ""
    route_via_a0: bool = False
    auto_ingest: bool = False
# ratios: loc_comments=25:2 imports_exports=3:3 calls_definitions=0:3
