"""Correlate user and root setup actions into one local restoration report."""
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from backups import user_state

SYSTEM_STATE = Path('/var/lib/Fiw-Gentoo-Dots')


def selection_key(selection):
    return hashlib.sha256(json.dumps(selection, sort_keys=True).encode()).hexdigest()


def validate_run(run_id):
    if not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_.-]{0,95}', run_id):
        raise ValueError('Invalid restoration run ID.')
    return run_id


def result_status(details):
    if details.get('status'):
        return details['status']
    if any(details.get(key) for key in ('failed', 'missing', 'skipped', 'kept', 'review')):
        return 'partial'
    return 'completed'


def record(selection, run_id, action, home, details, error=None):
    state = SYSTEM_STATE if os.geteuid() == 0 else user_state(home)
    state.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    event = {'run': validate_run(run_id), 'selection_key': selection_key(selection),
             'action': action, 'time': timestamp, 'details': details,
             'status': 'failed' if error else result_status(details)}
    if error:
        event['error'] = str(error)
    path = state / ('action-' + run_id + '-' + action + '-' + timestamp + '.json')
    path.write_text(json.dumps(event, indent=2) + '\n')
    path.chmod(0o644 if os.geteuid() == 0 else 0o600)
    return event


def expected(selection, workflow):
    if workflow != 'restore':
        if workflow == 'services':
            # Scope is provided by the caller's user/root invocation.
            return ['services-user', 'services-system']
        return [workflow]
    actions = []
    if selection['groups'] or selection.get('extras') or selection.get('flatpaks') or selection.get('services') or selection['bootloader'] != 'keep':
        actions.append('packages')
    if selection.get('flatpaks'):
        actions.append('flatpaks')
    if any(service != 'audio' for service in selection.get('services', [])):
        actions.append('services-system')
    if 'audio' in selection.get('services', []):
        actions.append('services-user')
    if selection['configs']:
        actions.append('configs')
    if selection['bootloader'] != 'keep':
        actions.append('boot')
    return actions


def summarize(selection, home, requirements, manual, run_id=None, workflow='restore', execution_error=None):
    events, inaccessible = [], []
    for state in (user_state(home), SYSTEM_STATE):
        try:
            for path in state.glob('action-*.json'):
                try:
                    event = json.loads(path.read_text())
                    if event.get('selection_key') == selection_key(selection):
                        events.append(event)
                except (OSError, ValueError):
                    inaccessible.append(str(path))
        except OSError:
            inaccessible.append(str(state))
    if run_id:
        validate_run(run_id)
    elif events:
        run_id = max(events, key=lambda event: event['time'])['run']
    events = [event for event in events if event['run'] == run_id]
    latest = {}
    for event in sorted(events, key=lambda item: item['time']):
        latest[event['action']] = event
    actions = expected(selection, workflow)
    if workflow == 'services':
        actions = [action for action in expected(selection, 'restore') if action.startswith('services-')]
    actions = list(dict.fromkeys(actions + list(latest)))
    result = {'run': run_id, 'workflow': workflow,
              'steps': {action: latest.get(action, {'status': 'not attempted'}) for action in actions},
              'config_requirements': requirements, 'manual_steps': manual,
              'unreadable_reports': inaccessible}
    if execution_error:
        result['execution_error'] = execution_error
    state = user_state(home)
    state.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ')
    path = state / ('summary-' + (run_id or timestamp) + '.json')
    temporary = path.with_name('.' + path.name + '.tmp')
    temporary.write_text(json.dumps(result, indent=2) + '\n')
    temporary.chmod(0o600)
    temporary.replace(path)
    print('Restoration summary' + (': ' + run_id if run_id else ''))
    if execution_error:
        print('  Workflow stopped: ' + execution_error)
    for action, event in result['steps'].items():
        print('  ' + action + ': ' + event['status'])
        details = event.get('details', {})
        for key in ('present', 'installed', 'already_installed', 'enabled', 'applied', 'requested', 'skipped', 'missing', 'failed', 'review', 'kept', 'restored'):
            if details.get(key):
                print('    ' + key.replace('_', ' ') + ': ' + ', '.join(map(str, details[key])))
        if event.get('error'):
            print('    error: ' + event['error'])
    for config, entries in requirements.items():
        for entry in entries:
            if entry['status'] in ('missing', 'unverified'):
                print('  Config requirement ' + entry['status'] + ': ' + config + ' needs ' + entry['package'])
    for item in manual:
        print('  Manual: ' + item)
    for path in inaccessible:
        print('  Unreadable report: ' + path)
    print('Combined report: ' + str(path))
    return result
