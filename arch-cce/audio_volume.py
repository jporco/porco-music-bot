#!/usr/bin/env python3
"""Controle unico do volume global e compatibilidade com terminais antigos."""
import argparse
import contextlib
import fcntl
import json
import math
import os
from pathlib import Path
import re
import selectors
import socket
import subprocess
import sys
import time

BASE = Path(__file__).resolve().parent
SINK = 'alsa_output.pci-0000_00_1b.0.analog-stereo'
SOCKET = Path('/tmp/porco.sock')
SINKS = (SINK, 'normalize', 'radio_level')
P2_TRIM_DB = 6.0


def run(*args):
    env = dict(os.environ)
    env['XDG_RUNTIME_DIR'] = f'/run/user/{os.getuid()}'
    env['PULSE_SERVER'] = f'unix:{env["XDG_RUNTIME_DIR"]}/pulse/native'
    env['LC_ALL'] = 'C'
    result = subprocess.run(args, capture_output=True, text=True, env=env, timeout=5)
    if result.returncode:
        raise RuntimeError(f'{args[0]}: {result.stderr.strip()}')
    return result.stdout.strip()


def number(path, fallback, minimum=0):
    try:
        value = int(path.read_text().strip())
        return value if minimum <= value <= 100 else fallback
    except (OSError, ValueError):
        return fallback


def save(path, value):
    text = str(value) + '\n'
    if path.exists() and path.read_text() == text:
        return
    temporary = path.with_name('.' + path.name + f'.tmp.{os.getpid()}')
    try:
        temporary.write_text(text)
        temporary.replace(path)
    finally:
        temporary.unlink(missing_ok=True)


def default_value():
    return number(BASE / 'volume-padrao.txt', 43, 1)


def last_value():
    return number(BASE / 'volume-atual.txt', default_value(), 1)


def limit(value):
    return min(value, number(BASE / 'test-volume-limit.txt', 100))


def mpv(command):
    if not SOCKET.exists():
        return None
    with socket.socket(socket.AF_UNIX) as conn:
        conn.settimeout(1)
        conn.connect(str(SOCKET))
        conn.sendall((json.dumps({'command': command}) + '\n').encode())
        for line in conn.makefile('r'):
            response = json.loads(line)
            if 'error' in response:
                if response['error'] != 'success':
                    raise RuntimeError('mpv: ' + response['error'])
                return response.get('data')
    raise RuntimeError('mpv nao confirmou o comando')


def sink_state():
    for sink in json.loads(run('pactl', '--format=json', 'list', 'sinks')):
        if sink['name'] == SINK:
            return sink
    raise RuntimeError('Saida analogica do CCE indisponivel')


def targets(value):
    right = number(BASE / 'balance-right.txt', 100, 50)
    return value, value * right // 100


def db_for_volume(value):
    if value <= 0:
        return -64.0
    return max(-64.0, min(0.0, 60.0 * math.log10(value / 100.0)))


def volume_for_db(db):
    return 100.0 * 10.0 ** (db / 60.0)


def output_db_targets(value):
    left, right = targets(value)
    ceiling = db_for_volume(number(BASE / 'test-volume-limit.txt', 100))
    return {
        'Line Out': [min(db_for_volume(channel) + P2_TRIM_DB, ceiling)
                     for channel in (left, right)],
        'Speaker': [db_for_volume(channel) for channel in (left, right)],
    }


def mixer_levels(control):
    text = run('amixer', '-c', '0', 'sget', control)
    matches = re.findall(
        r'Playback\s+(\d+)\s+\[\d+(?:\.\d+)?%\]\s+'
        r'\[(-?\d+(?:\.\d+)?)dB\](?:\s+\[(on|off)\])?', text)
    if not matches:
        raise RuntimeError(f'Nao foi possivel ler o controle ALSA {control}')
    return [{'raw': int(raw), 'db': float(db), 'on': state != 'off'}
            for raw, db, state in matches]


def set_output_levels(value):
    controls = run('amixer', '-c', '0', 'controls').splitlines()
    for name, control in (('Line Out', 'Line Out Playback Volume'),
                          ('Speaker', 'Speaker Playback Volume')):
        raw_values = [max(0, min(64, round(db + 64)))
                      for db in output_db_targets(value)[name]]
        match = next((re.search(r'numid=(\d+)', line) for line in controls
                      if f"name='{control}'" in line), None)
        if not match:
            raise RuntimeError(f'Controle ALSA ausente: {control}')
        run('amixer', '-c', '0', 'cset', f'numid={match.group(1)}',
            f'{raw_values[0]},{raw_values[1]}')


def state():
    sink = sink_state()
    muted = bool(sink['mute'])
    line_out = mixer_levels('Line Out')
    speaker = mixer_levels('Speaker')
    left = volume_for_db(line_out[0]['db'])
    right = volume_for_db(line_out[-1]['db'])
    base_left = volume_for_db(speaker[0]['db'])
    base_right = volume_for_db(speaker[-1]['db'])
    return {'volume': 0 if muted else round(max(base_left, base_right)),
            'muted': muted, 'saved': last_value(), 'left': left, 'right': right,
            'speaker_left': base_left, 'speaker_right': base_right,
            'p2_gain_db': round(line_out[0]['db'] - speaker[0]['db'], 1)}


def verify(value, muted):
    actual = state()
    if actual['muted'] != muted:
        raise RuntimeError('A saida nao confirmou o estado de mute solicitado')
    sink = sink_state()
    if any(abs(channel['value'] - 65536) > 655 for channel in sink['volume'].values()):
        raise RuntimeError('O ganho geral do dispositivo nao ficou neutro')
    control_value = last_value() if muted else value
    expected_outputs = output_db_targets(control_value)
    for name, prefix in (('Line Out', ''), ('Speaker', 'speaker_')):
        levels = mixer_levels(name)
        if len(levels) < 2 or any(not level['on'] for level in levels):
            raise RuntimeError(f'A saida {name} nao confirmou os dois canais ligados')
        for index, expected_db in enumerate(expected_outputs[name]):
            if abs(levels[index]['db'] - expected_db) > 0.75:
                label = 'P2' if not prefix else 'alto-falante interno'
                raise RuntimeError(f'Volume {label} esperado {expected_db:.1f} dB; '
                                   f'lido {levels[index]["db"]:.1f} dB')
    for control in ('Master', 'PCM'):
        levels = mixer_levels(control)
        if any(level['db'] < -0.5 or not level['on'] for level in levels):
            raise RuntimeError(f'O controle geral {control} ainda atenua a saida')
    if SOCKET.exists():
        if mpv(['get_property', 'volume']) != 100:
            raise RuntimeError('O player continua aplicando um segundo volume')
        if mpv(['get_property', 'mute']) != muted:
            raise RuntimeError('O player nao confirmou o mute solicitado')
    for stream in json.loads(run('pactl', '--format=json', 'list', 'sink-inputs')):
        if stream.get('properties', {}).get('application.process.binary') in ('mpv', 'spotifyd'):
            if stream['mute'] or any(abs(v['value'] - 65536) > 655 for v in stream['volume'].values()):
                raise RuntimeError('O fluxo de audio ainda aplica mute ou outro ganho')
    return actual


def fast_path_ready():
    """Return true only when a normal volume change needs ALSA levels alone."""
    try:
        sinks = json.loads(run('pactl', '--format=json', 'list', 'sinks'))
        by_name = {sink['name']: sink for sink in sinks}
        if any(name not in by_name for name in SINKS):
            return False
        physical = by_name[SINK]
        if physical.get('mute') or physical.get('active_port') != 'analog-output-lineout':
            return False
        for sink in by_name.values():
            if sink['name'] in SINKS:
                channels = list(sink.get('volume', {}).values())
                if sink.get('mute') or any(
                        abs(channel['value'] - 65536) > 655 for channel in channels):
                    return False
                if not channels:
                    return False

        sink_inputs = json.loads(run('pactl', '--format=json', 'list', 'sink-inputs'))
        expected_sinks = {'spotifyd': 'normalize', 'mpv': 'radio_level'}
        for stream in sink_inputs:
            binary = stream.get('properties', {}).get('application.process.binary')
            if binary not in expected_sinks:
                continue
            if stream.get('sink') != by_name[expected_sinks[binary]]['index']:
                return False
            channels = list(stream.get('volume', {}).values())
            if stream.get('mute') or any(
                    abs(channel['value'] - 65536) > 655 for channel in channels):
                return False
            if not channels:
                return False

        for control in ('Master', 'PCM'):
            levels = mixer_levels(control)
            if any(level['db'] < -0.5 or not level['on'] for level in levels):
                return False
        for control in ('Line Out', 'Speaker'):
            levels = mixer_levels(control)
            if len(levels) < 2 or any(not level['on'] for level in levels):
                return False
        if "Item0: 'Disabled'" not in run('amixer', '-c', '0', 'sget', 'Auto-Mute Mode'):
            return False
        if SOCKET.exists() and (mpv(['get_property', 'volume']) != 100
                                or mpv(['get_property', 'mute']) is not False):
            return False
        return True
    except (KeyError, RuntimeError, OSError, subprocess.TimeoutExpired, ValueError):
        return False


def apply(value, muted):
    """Apply one shared volume; avoid a global mute on healthy level changes."""
    value = limit(value)
    if not muted and fast_path_ready():
        try:
            set_output_levels(value)
            return verify(value, False)
        except (RuntimeError, OSError, subprocess.TimeoutExpired):
            # If a readback fails, use the complete repair path below.
            pass

    # Mute only for mute/unmute or when route/gain invariants need repair.
    run('pactl', 'set-sink-mute', SINK, '1')
    sink = sink_state()
    if sink.get('active_port') != 'analog-output-lineout':
        run('pactl', 'set-sink-port', SINK, 'analog-output-lineout')
    run('amixer', '-c', '0', 'sset', 'Auto-Mute Mode', 'Disabled')
    run('pactl', 'set-sink-volume', SINK, '100%', '100%')
    run('amixer', '-c', '0', 'sset', 'PCM', '100%')
    run('amixer', '-c', '0', 'sset', 'Master', '100%', 'unmute')
    run('amixer', '-c', '0', 'sset', 'Line Out', 'unmute')
    run('amixer', '-c', '0', 'sset', 'Speaker', 'unmute')
    set_output_levels(last_value() if muted else value)
    mpv(['set_property', 'mute', True])
    mpv(['set_property', 'volume', 100])
    for stream in json.loads(run('pactl', '--format=json', 'list', 'sink-inputs')):
        if stream.get('properties', {}).get('application.process.binary') in ('mpv', 'spotifyd'):
            run('pactl', 'set-sink-input-volume', str(stream['index']), '100%')
            run('pactl', 'set-sink-input-mute', str(stream['index']), '0')
    available = {s['name'] for s in json.loads(run('pactl', '--format=json', 'list', 'sinks'))}
    for name in ('normalize', 'radio_level'):
        if name in available:
            run('pactl', 'set-sink-mute', name, '1' if muted else '0')
    if not muted:
        mpv(['set_property', 'mute', False])
        run('pactl', 'set-sink-mute', SINK, '0')
    return verify(value, muted)


def remember_mute(muted):
    flag = BASE / 'mute-ativo.txt'
    if muted:
        if not flag.exists():
            save(BASE / 'volume-antes-mute.txt', last_value())
            flag.touch()
    else:
        flag.unlink(missing_ok=True)


def set_value(value):
    value = limit(value)
    remember_mute(value == 0)
    if value:
        save(BASE / 'volume-atual.txt', value)
    return apply(value, value == 0)


def parse_value(text, current):
    if text == '+':
        return min(100, current + 5)
    if text == '-':
        return max(0, current - 5)
    if not re.fullmatch(r'[0-9]{1,3}', text):
        raise ValueError('Uso: volume [0-100 | + | - | atual]')
    value = int(text)
    if value > 100:
        raise ValueError('Uso: volume [0-100 | + | - | atual]')
    return value


def needs_repair(value, muted):
    try:
        verify(value, muted)
        if not muted:
            for sink in json.loads(run('pactl', '--format=json', 'list', 'sinks')):
                if sink['name'] in SINKS and sink['mute']:
                    return True
        return False
    except RuntimeError:
        return True


@contextlib.contextmanager
def locked():
    with (BASE / '.audio-volume.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        yield


def sync():
    with locked():
        actual = state()
        muted = (BASE / 'mute-ativo.txt').exists() or actual['muted']
        value = limit(last_value())
        if muted:
            remember_mute(True)
        if needs_repair(value, muted):
            apply(value, muted)
            print(f'Compatibilidade aplicada: volume={value}, mute={muted}', flush=True)


def fingerprint():
    result = []
    for name in ('volume-atual.txt', 'mute-ativo.txt'):
        try:
            stat = (BASE / name).stat()
            result.append((stat.st_mtime_ns, stat.st_ino))
        except FileNotFoundError:
            result.append(None)
    return tuple(result)


def watch():
    """Repara apenas comandos legados, depois de terminarem suas escritas."""
    process = subprocess.Popen(['stdbuf', '-oL', 'pactl', 'subscribe'], stdout=subprocess.PIPE, bufsize=0,
                               env={**os.environ, 'LC_ALL': 'C',
                                    'PULSE_SERVER': f'unix:/run/user/{os.getuid()}/pulse/native'})
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ)
    stamp = fingerprint()
    deadline = time.monotonic() + 1.2
    try:
        while process.poll() is None:
            for key, _ in selector.select(0.2):
                events = os.read(key.fileobj.fileno(), 65536).decode(errors='replace')
                if ' on sink ' in events or ' on sink-input ' in events:
                    deadline = time.monotonic() + 1.2
            current = fingerprint()
            if current != stamp:
                stamp = current
                deadline = time.monotonic() + 1.2
            if deadline and time.monotonic() >= deadline:
                try:
                    sync()
                except (RuntimeError, OSError, subprocess.TimeoutExpired) as error:
                    print(f'Falha de sincronizacao: {error}', file=sys.stderr, flush=True)
                deadline = None
    finally:
        process.terminate()
        process.wait(timeout=3)
    raise RuntimeError('Conexao de eventos PulseAudio encerrada')


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=('volume', 'apply', 'mute', 'unmute', 'restore', 'morning',
                                           'default', 'default-value', 'status', 'sync', 'watch'))
    parser.add_argument('value', nargs='?')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.action == 'watch':
            watch()
            return 0
        if args.action == 'sync':
            sync()
            return 0
        with locked():
            if args.action == 'default-value':
                print(default_value())
                return 0
            if args.action == 'default':
                if args.value is not None:
                    value = parse_value(args.value, default_value())
                    if not 1 <= value <= 100 or args.value in ('+', '-'):
                        raise ValueError('Uso: volume-padrao [1-100]')
                    save(BASE / 'volume-padrao.txt', value)
                print(f'Volume padrao: {default_value()}%')
                return 0
            if args.action == 'status' or (args.action == 'volume' and args.value in (None, 'atual', 'agora')):
                result = state()
            elif args.action in ('volume', 'apply'):
                if args.value is None:
                    raise ValueError('Informe o volume entre 0 e 100')
                result = set_value(parse_value(args.value, last_value()))
            elif args.action == 'mute':
                result = set_value(0)
            elif args.action == 'morning':
                result = set_value(default_value())
            else:
                result = set_value(last_value())
        if args.json:
            print(json.dumps(result))
        elif args.action != 'apply':
            print(f'Volume: {result["volume"]}%' + (' (mudo)' if result['muted'] else ''))
        return 0
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as error:
        print(f'Falha no controle de volume: {error}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
