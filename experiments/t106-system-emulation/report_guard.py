"""Exact JSON comparison and non-destructive verification-report refresh.

Container normalization is not a tolerance. A changed scientific payload or
trace archive is rejected before writing. Only verification provenance may
change, with its previous report digest retained in the new report.
"""
import hashlib
import json


def canonical(value):
    return json.loads(json.dumps(value, allow_nan=False))


def encoded(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def payload(report):
    return {k: v for k, v in report.items()
            if k not in ('sha256', 'verification_history')}


def prepare(report, previous=None):
    """Return canonical report; never bless a changed result as a refresh."""
    current = canonical(report)
    if previous is None:
        return current
    old = canonical(previous)
    assert encoded(payload(current)) == encoded(payload(old)), 'scientific result changed; preserve and investigate'
    old_traces = {p: h for p, h in old['sha256'].items() if '.trace.' in p}
    new_traces = {p: h for p, h in current['sha256'].items() if '.trace.' in p}
    assert old_traces == new_traces, 'trace archive changed; preserve and investigate'
    history = old.get('verification_history', [])
    if current['sha256'] != old['sha256']:
        history = history + [dict(
            previous_canonical_report_sha256=hashlib.sha256(encoded(old)).hexdigest(),
            previous_sha256=old['sha256'],
            reason='verification provenance refreshed; scientific payload and trace hashes unchanged')]
    if history:
        current['verification_history'] = history
    return current


def publish_or_compare(path, report, record=False):
    old = json.loads(path.read_text()) if path.exists() else None
    current = prepare(report, old)
    if record:
        path.write_text(json.dumps(current, indent=2, allow_nan=False) + '\n')
    else:
        assert old is not None, 'verification report is missing'
        assert encoded(current) == encoded(old), 'verification provenance changed; review before explicit --record'
    return current
