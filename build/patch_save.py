"""Apply every current fix to a TTS save. Safe to re-run: each step removes
its own previous output first. Usage: python patch_save.py <save.json> [--fresh]
--fresh clears stored script state (new game); omit it to keep a game in progress.
"""
import json, math, sys, copy

REF = r'C:/Users/sando/Development/rftg-tts-assets/build/RollForTheGalaxy_Published.json'
QR  = 'https://raw.githubusercontent.com/ianFullStack/rftg-tts-assets/main/textures/rftg_quick_reference.png'
COUNTERS = {'Red':(-9.45,-15.75,0.0),'White':(24.57,-15.75,0.0),'Purple':(33.39,9.45,270.0),
            'Blue':(8.19,14.49,180.0),'Green':(-27.09,14.49,180.0)}
PLAYZONE = {'Red':'c72f25','White':'e86414','Purple':'7bbfef','Blue':'232dfe','Green':'134574'}
HOME_BAG = '6a3a88'
WHITE_POOL = 15

def used_guids(d):
    out=set()
    def walk(o):
        if isinstance(o,dict):
            if o.get('GUID'): out.add(o['GUID'])
            for v in o.values(): walk(v)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(d['ObjectStates']); return out

def find(d, pred):
    hit=[]
    def walk(o):
        if isinstance(o,dict):
            if pred(o): hit.append(o)
            for v in o.values(): walk(v)
        elif isinstance(o,list):
            for x in o: walk(x)
    walk(d['ObjectStates']); return hit

def patch(path, fresh):
    d = json.load(open(path, encoding='utf-8'))
    ref = json.load(open(REF, encoding='utf-8'))
    report = []

    # 1. current script
    d['LuaScript'] = ref['LuaScript']
    report.append('script updated (2-player die, resume, safe shuffle, cups)')

    # 2. hidden zones hide pointers
    n = 0
    for o in d['ObjectStates']:
        if o.get('Name') == 'FogOfWarTrigger' and 'FogHidePointers' in o:
            o['FogHidePointers'] = True; n += 1
    report.append(f'hidden zones hiding pointers: {n}')

    # 3. quick-reference sheets (one per seat, inside that seat's play zone)
    d['ObjectStates'] = [o for o in d['ObjectStates'] if o.get('Nickname') != 'Quick Reference']
    zt = {o.get('GUID'): o['Transform'] for o in d['ObjectStates'] if o.get('GUID') in PLAYZONE.values()}
    used = used_guids(d); made = 0
    for i, (colour, (cx, cz, rot)) in enumerate(COUNTERS.items()):
        if PLAYZONE[colour] not in zt:      # seat was cleared - skip it
            continue
        a = math.radians(rot)
        rx, rz = math.cos(a), -math.sin(a)
        x, z = cx - rx*8.0, cz - rz*8.0
        t = zt[PLAYZONE[colour]]
        hx, hz = t['scaleX']/2 - 4.0, t['scaleZ']/2 - 4.0
        x = min(max(x, t['posX']-hx), t['posX']+hx)
        z = min(max(z, t['posZ']-hz), t['posZ']+hz)
        g = f'qr{i:04d}'
        while g in used: g += 'x'
        used.add(g)
        d['ObjectStates'].append({
            "GUID": g, "Name": "Custom_Tile", "Nickname": "Quick Reference",
            "Description": "Phase reference - the printed side of the player screen.",
            "Transform": {"posX": x, "posY": 1.2, "posZ": z, "rotX": 0.0, "rotY": rot, "rotZ": 0.0,
                          "scaleX": 5.0, "scaleY": 5.0, "scaleZ": 5.0},
            "ColorDiffuse": {"r":1.0,"g":1.0,"b":1.0},
            "Locked": True, "Grid": True, "Snap": True, "Autoraise": True, "Sticky": True,
            "Tooltip": True, "GridProjection": False, "HideWhenFaceDown": False, "Hands": False,
            "CustomImage": {"ImageURL": QR, "ImageSecondaryURL": "", "ImageScalar": 1.0,
                            "WidthScale": 0.0,
                            "CustomTile": {"Type": 0, "Thickness": 0.1, "Stackable": False, "Stretch": True}},
        }); made += 1
    report.append(f'quick-reference sheets placed: {made}')

    # 4. stock the Home (white) dice bag
    bag = next((o for o in find(d, lambda o: o.get('GUID') == HOME_BAG)), None)
    if bag is None:
        report.append('Home bag NOT FOUND - skipped')
    else:
        sample = next((o for o in find(d, lambda o: 'Die.obj' in (o.get('CustomMesh') or {}).get('MeshURL','')
                                       and 'WhiteDie' in (o.get('CustomMesh') or {}).get('DiffuseURL',''))), None)
        if sample is None:
            report.append('no white die to clone - skipped')
        else:
            bag.setdefault('ContainedObjects', [])
            bag['ContainedObjects'] = [o for o in bag['ContainedObjects']
                                       if not str(o.get('GUID','')).startswith('wd')]
            used = used_guids(d)
            for i in range(WHITE_POOL):
                c = copy.deepcopy(sample)
                g = f'wd{i:04d}'
                while g in used: g += 'x'
                used.add(g)
                c['GUID'] = g
                c['Locked'] = False
                c['Nickname'] = ''
                bag['ContainedObjects'].append(c)
            report.append(f'white dice added to Home bag: {WHITE_POOL} (now {len(bag["ContainedObjects"])})')

    if fresh:
        d['LuaScriptState'] = ''
        report.append('script state cleared (new game)')
    else:
        report.append(f'script state preserved ({len(d.get("LuaScriptState") or "")} chars)')

    json.dump(d, open(path, 'w', encoding='utf-8'), indent=2, ensure_ascii=False)
    for r in report: print('  ' + r)
    return d

if __name__ == '__main__':
    p = sys.argv[1]
    patch(p, '--fresh' in sys.argv)
    print('  written ->', p)
