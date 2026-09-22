from pathlib import Path
import hashlib,importlib.util
SOURCE_PATH=r"qseries_v2\oracle_predictive_data\opd_017_discovery_feature_primitive_materialization.py"
SOURCE_SHA256="c0455590b2de0560552bdfd503dfbe0bf8a97a105617695581d2df0c56a00917"
execution_authority=False
probability_enabled=False
direction_enabled=False
publication_allowed=False
def _load(root):
 p=Path(root)/SOURCE_PATH
 if hashlib.sha256(p.read_bytes()).hexdigest()!=SOURCE_SHA256: raise RuntimeError("OPD-017 frozen source hash changed")
 s=importlib.util.spec_from_file_location("_opd017_frozen",p);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
 if not callable(getattr(m,"_tokens",None)): raise RuntimeError("OPD-017 frozen _tokens helper disappeared")
 return m._tokens
def materialize_exact_live_tokens(root,state_at_t):
 if not isinstance(state_at_t,dict): raise TypeError("state_at_t must be dict")
 return tuple(_load(root)(state_at_t))
