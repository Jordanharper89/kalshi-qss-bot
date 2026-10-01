"""Read-only source contract capture. No database access or runtime imports."""
import ast
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / 'OOI_012_SLOP_EVIDENCE_MAPPING_CONTRACT.txt'
FILES = {
    'MATERIALIZER': 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_006_slop_universal_opportunity_materializer.py',
    'BRIDGE': 'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_007b_slop_existing_oos_intake.py',
    'CANONICAL_MODEL': 'qseries_v2/oracle_intelligence/universal_opportunity_model/universal_opportunity.py',
    'VALIDATION': 'qseries_v2/oracle_intelligence/opportunity_operating_system/opportunity_validation_engine.py',
}
SLOP = ROOT / 'qseries_v2/oracle_strategy_intelligence/solana_live_opportunity'
TERMS = re.compile(r'confidence|expected_value|expected_edge|net_edge|net_return|probability|calibrat|sample_size|comparable|friction|adapter|required|execution|mean_return|outcome|learn', re.I)


def require(value, message):
    if not value:
        raise AssertionError(message)


def parse_file(path):
    raw = path.read_bytes()
    source = raw.decode('utf-8-sig')
    return source, ast.parse(source, filename=str(path)), hashlib.sha256(raw).hexdigest()


def fields(node):
    result = set()
    for item in ast.walk(node):
        if isinstance(item, ast.Constant) and isinstance(item.value, str):
            # Capture field/column names only, never arbitrary payload values.
            if re.fullmatch(r'[A-Za-z_][A-Za-z_0-9]{0,79}', item.value) and TERMS.search(item.value):
                result.add(item.value)
        elif isinstance(item, (ast.Name, ast.Attribute)):
            name = item.id if isinstance(item, ast.Name) else item.attr
            if TERMS.search(name):
                result.add(name)
    return sorted(result)


def signature(node):
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return node.name + '(' + ast.unparse(node.args) + ')'
    if isinstance(node, ast.ClassDef):
        annotated = [n.target.id for n in node.body if isinstance(n, ast.AnnAssign) and isinstance(n.target, ast.Name)]
        return 'class ' + node.name + ' fields=' + repr(annotated)
    return ''


def render():
    lines = ['OOI-012 EXACT SOURCE CONTRACT CAPTURE',
        'execution_authority=FALSE; source inspection only; no opportunity admission certified',
        'Frozen thesis: BUY_PRESSURE / 60 seconds / +10% target / -5% stop / 200 bps friction',
        'Boundary: map existing evidence into canonical fields; do not manufacture confidence/edge or adapter readiness.']
    manifest = {}
    for label, relative in FILES.items():
        path = ROOT / relative
        require(path.is_file(), 'Missing required existing file: ' + relative)
        source, tree, digest = parse_file(path)
        manifest[relative] = digest
        lines.extend(['', '[' + label + '] ' + relative, '[SHA256] ' + digest])
        if label in ('MATERIALIZER', 'BRIDGE', 'CANONICAL_MODEL'):
            # Complete definitions preserve enum/default/nested execution contracts.
            lines.append(source.rstrip())
        else:
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    lines.append(ast.get_source_segment(source, node))
                elif isinstance(node, ast.ClassDef) and node.name == 'ValidationRuleConfig':
                    lines.append(ast.get_source_segment(source, node))
                elif isinstance(node, ast.ClassDef) and node.name == 'OpportunityValidationEngine':
                    for child in node.body:
                        if isinstance(child, ast.FunctionDef) and child.name in (
                            '__init__', 'validate', '_contract_checks', '_business_rule_checks',
                            '_risk_guardrail_checks', '_informational_checks', '_required_attr',
                            '_required_bool', '_safe_fingerprint', '_float', '_enum_value'):
                            lines.append(ast.get_source_segment(source, child))
    require(SLOP.is_dir(), 'Existing SLOP subsystem missing')
    paths = sorted(SLOP.glob('slop_*.py'))
    require(paths, 'No SLOP source files found')
    lines.extend(['', '[EXISTING_SLOP_EVIDENCE_PRODUCERS]'])
    relevant = []
    for path in paths:
        source, tree, digest = parse_file(path)
        relative = path.relative_to(ROOT).as_posix()
        manifest[relative] = digest
        nodes = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                matched = fields(node)
                if matched:
                    nodes.append((node, matched))
        if not nodes:
            continue
        relevant.append(relative)
        lines.append('[MODULE] ' + relative + ' sha256=' + digest)
        for node, matched in nodes:
            lines.append('  [API] ' + signature(node))
            lines.append('  [EVIDENCE_FIELDS] ' + ', '.join(matched))
    require(relevant, 'No existing SLOP evidence contracts found')
    lines.extend(['', '[SCOPE] Static contracts captured; live evidence values were not read.',
                  '[NEXT] Resolve real evidence provenance and the adapter requirement before nonempty admission.',
                  '[SOURCE_FILES] ' + str(len(manifest))])
    return '\n'.join(lines) + '\n', manifest


def main():
    probe = ast.parse("def f(x):\n return {'confidence': x, 'mean_return': 0, 'unrelated': 1}\n")
    require(fields(probe) == ['confidence', 'mean_return'], 'field extraction self-test failed')
    first, manifest = render()
    second, repeated = render()
    require(first == second and manifest == repeated, 'Source changed during capture; no report written')
    REPORT.write_text(first, encoding='utf-8')
    print(first, end='')
    print('[REPORT]', REPORT)
    print('[PASS] OOI-012 source contract capture is deterministic; production files unchanged')
    print('[HOLD] Populated opportunity feed and live runtime activation remain uncertified')

if __name__ == '__main__':
    main()
