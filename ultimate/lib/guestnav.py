"""The Switch screen's guest slot for the tests (outfit.c cycle and look, Nov 12): Up and Down go from fighter to fighter (a fighter is a
bench group: Pan's five looks, Teen Gohan's two, Future Trunks's two, Broly and Full Power Broly), in the order of each one's first
look in outfits.json's guest list, to his first open look; L and R go through his own looks."""
import json, os
HERE = os.path.dirname(os.path.abspath(__file__))
OLD = ('broly', 'broly_fp', 'android13', 'piccolo', 'future_trunks', 'android17', 'android18', 'krillin', 'videl', 'majin_buu', 'super_janemba', 'kid_buu', 'tien', 'yamcha', 'pikkon', 'hercule')


def guests():
    return [o['form'] for o in json.load(open(os.path.join(HERE, '..', 'outfits.json')))['characters']['8']]


def groups():
    """each guest look's fighter, as build.py bench_groups gives it"""
    cfg = json.load(open(os.path.join(HERE, '..', 'outfits.json')))['characters']['8']
    out = [0, 0] + list(range(1, len(OLD) - 1)); shared = dict(zip(OLD, out))
    for o in cfg[len(OLD):]:
        key = o.get('bench', o['form'])
        if key not in shared: shared[key] = max(out) + 1
        out.append(shared[key])
    return out


def keys(target, start='broly', open_=None, wait=40):
    """key presses on the guest slot from look `start` to look `target`: Downs between fighters, then Rs through his looks.
    open_: the looks open (default all)."""
    names, gs = guests(), groups()
    open_ = set(open_ if open_ is not None else names)
    fighters = []                                   # each fighter's group, by its first look, if any of its looks is open
    for i, g in enumerate(gs):
        if g not in fighters and gs.index(g) == i and any(gs[j] == g and names[j] in open_ for j in range(len(names))): fighters.append(g)
    looks = lambda g: [names[j] for j in range(len(names)) if gs[j] == g and names[j] in open_]
    g0, g1 = gs[names.index(start)], gs[names.index(target)]
    downs = (fighters.index(g1) - fighters.index(g0)) % len(fighters)
    at = looks(g1)[0] if downs else start                    # a new fighter comes in his first open look
    rs = (looks(g1).index(target) - looks(g1).index(at)) % len(looks(g1))
    move = ['tap DOWN %d' % wait] * downs if downs <= len(fighters) // 2 else ['tap UP %d' % wait] * (len(fighters) - downs)     # the shorter way round
    return move + ['tap R %d' % wait] * rs
