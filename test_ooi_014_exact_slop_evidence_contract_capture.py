"""Capture source contracts only; do not import or call live evidence readers."""
import ast
import hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / 'OOI_014_EXACT_SLOP_EVIDENCE_CONTRACTS.txt'
BASE = 'qseries_v2/oracle_strategy_intelligence/solana_live_opportunity/'
SEEDS = (
    BASE + 'slop_061_canonical_prospective_learning_evidence.py',
    BASE + 'slop_067_opportunity_level_exactly_once_learning_lineage.py',
    BASE + 'slop_062_native_ocl_prospective_outcome_bridge.py',
    'qseries_v2/oracle_strategy_intelligence/oracle_opportunity_intelligence/ooi_006_slop_universal_opportunity_materializer.py',
    'qseries_v2/oracle_intelligence/universal_opportunity_model/universal_opportunity.py',
)


def require(value, message):
    if not value:
        raise AssertionError(message)


def read_source(relative):
    path = ROOT / relative
    raw = path.read_bytes()
    source = raw.decode('utf-8-sig')
    return source, ast.parse(source, filename=relative), hashlib.sha256(raw).hexdigest()


def local_dependencies(relative, tree):
    package = relative[:-3].split('/')[:-1]
    modules = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level:
                parent = package[:len(package) - node.level + 1]
                prefix = '.'.join(parent + ([node.module] if node.module else []))
            else:
                prefix = node.module or ''
            modules.add(prefix)
            modules.update(prefix + '.' + a.name for a in node.names if a.name != '*')
    result = set()
    for module in modules:
        if not module.startswith('qseries_v2.'):
            continue
        candidate = module.replace('.', '/') + '.py'
        if (ROOT / candidate).is_file():
            result.add(candidate)
    return sorted(result)


def capture():
    sources = {}
    edges = {}
    for relative in SEEDS:
        require((ROOT / relative).is_file(), 'Missing exact required source: ' + relative)
        sources[relative] = read_source(relative)
    # Follow only the two existing evidence readers, two dependency levels deep.
    frontier = list(SEEDS[:2])
    for depth in range(2):
        following = []
        for relative in sorted(frontier):
            dependencies = local_dependencies(relative, sources[relative][1])
            edges[relative] = dependencies
            for dependency in dependencies:
                if dependency not in sources:
                    require(len(sources) < 40, 'Dependency capture exceeded 40 files; no silent truncation')
                    sources[dependency] = read_source(dependency)
                    following.append(dependency)
        frontier = following
    for relative, symbol in ((SEEDS[0], 'learning_evidence'), (SEEDS[1], 'independent_evidence'),
                             (SEEDS[3], 'materialize_slop')):
        require(any(isinstance(n, ast.FunctionDef) and n.name == symbol for n in sources[relative][1].body),
                'Required existing function missing: ' + symbol)
    lines = ['OOI-014 EXACT SLOP EVIDENCE CONTRACTS',
             'SOURCE INSPECTION ONLY; execution_authority=FALSE',
             'No live calls, database writes, learning-state changes, or production-source edits.',
             'No confidence, edge, calibration, or nonempty-admission claim.',
             'Frozen thesis unchanged: BUY_PRESSURE / 60 seconds / +10% / -5% / 200 bps.',
             '', '[DEPENDENCIES]']
    for relative in sorted(edges):
        lines.append(relative + ' -> ' + repr(edges[relative]))
    manifest = {}
    for relative in sorted(sources):
        source, tree, digest = sources[relative]
        manifest[relative] = digest
        lines.extend(['', '[BEGIN_FILE] ' + relative, '[SHA256] ' + digest,
                      source.rstrip(), '[END_FILE] ' + relative])
    lines.extend(['', '[FILE_COUNT] ' + str(len(sources)), '[END_OF_COMPLETE_REPORT]'])
    return '\n'.join(lines) + '\n', manifest


def main():
    text, before = capture()
    replay, after = capture()
    require(text == replay and before == after, 'Source changed during capture; no report written')
    payload = text.encode('utf-8')
    REPORT.write_bytes(payload)
    require(REPORT.read_bytes() == payload, 'Report writeback mismatch')
    print('[PASS] OOI-014 exact evidence-reader and materializer contracts captured')
    print('[PASS] deterministic source capture; production sources unchanged')
    print('[FILES]', len(before))
    print('[REPORT]', REPORT)
    print('[BYTES]', len(payload))
    print('[SHA256]', hashlib.sha256(payload).hexdigest())
    print('[NEXT] Attach OOI_014_EXACT_SLOP_EVIDENCE_CONTRACTS.txt directly; do not paste console scrollback')
    print('[HOLD] Evidence mapping and nonempty admission remain pending; execution_authority=FALSE')

if __name__ == '__main__':
    main()
