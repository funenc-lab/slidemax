#!/usr/bin/env python3
"""PPTX animation and transition XML helpers for PPT Master."""

from typing import Any, Dict, Optional


TRANSITIONS: Dict[str, Dict[str, Any]] = {
    'fade': {
        'name': 'Fade',
        'element': 'fade',
        'attrs': {},
    },
    'push': {
        'name': 'Push',
        'element': 'push',
        'attrs': {'dir': 'r'},
    },
    'wipe': {
        'name': 'Wipe',
        'element': 'wipe',
        'attrs': {'dir': 'r'},
    },
    'split': {
        'name': 'Split',
        'element': 'split',
        'attrs': {'orient': 'horz', 'dir': 'out'},
    },
    'reveal': {
        'name': 'Reveal',
        'element': 'strips',
        'attrs': {'dir': 'rd'},
    },
    'cover': {
        'name': 'Cover',
        'element': 'cover',
        'attrs': {'dir': 'r'},
    },
    'random': {
        'name': 'Random',
        'element': 'random',
        'attrs': {},
    },
}

SPEED_MAP = {
    'slow': 1.0,
    'med': 0.5,
    'fast': 0.25,
}


def duration_to_speed(duration: float) -> str:
    """Convert a transition duration in seconds to an OOXML speed key."""
    if duration >= 0.75:
        return 'slow'
    if duration >= 0.35:
        return 'med'
    return 'fast'


def create_transition_xml(
    effect: str = 'fade',
    duration: float = 0.5,
    advance_after: Optional[float] = None,
) -> str:
    """Build the OOXML transition fragment for a slide."""
    if effect not in TRANSITIONS:
        effect = 'fade'

    trans_info = TRANSITIONS[effect]
    element_name = trans_info['element']
    attrs = trans_info['attrs']

    speed = duration_to_speed(duration)
    advance_attr = ''
    if advance_after is not None:
        advance_ms = int(advance_after * 1000)
        advance_attr = f' advTm="{advance_ms}"'

    effect_attrs = ' '.join(f'{key}="{value}"' for key, value in attrs.items())
    if effect_attrs:
        effect_attrs = ' ' + effect_attrs

    return f'''  <p:transition spd="{speed}"{advance_attr}>
    <p:{element_name}{effect_attrs}/>
  </p:transition>'''


ANIMATIONS: Dict[str, Dict[str, Any]] = {
    'fade': {
        'name': 'Fade In',
        'filter': 'fade',
    },
    'fly': {
        'name': 'Fly In',
        'filter': 'fly',
        'prLst': 'from(b)',
    },
    'zoom': {
        'name': 'Zoom In',
        'filter': 'zoom',
        'prLst': 'in',
    },
    'appear': {
        'name': 'Appear',
        'filter': None,
    },
}


def create_timing_xml(
    animation: str = 'fade',
    duration: float = 1.0,
    delay: float = 0,
    shape_id: int = 2,
) -> str:
    """Build the OOXML timing fragment for a shape entrance animation."""
    if animation not in ANIMATIONS:
        animation = 'fade'

    anim_info = ANIMATIONS[animation]
    duration_ms = int(duration * 1000)
    delay_ms = int(delay * 1000)

    if anim_info['filter'] is None:
        effect_xml = f'''                            <p:set>
                              <p:cBhvr>
                                <p:cTn id="5" dur="1" fill="hold">
                                  <p:stCondLst><p:cond delay="{delay_ms}"/></p:stCondLst>
                                </p:cTn>
                                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                                <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
                              </p:cBhvr>
                              <p:to><p:strVal val="visible"/></p:to>
                            </p:set>'''
    else:
        filter_name = anim_info['filter']
        prop_attr = ''
        if 'prLst' in anim_info:
            prop_attr = f' prLst="{anim_info["prLst"]}"'

        effect_xml = f'''                            <p:set>
                              <p:cBhvr>
                                <p:cTn id="5" dur="1" fill="hold">
                                  <p:stCondLst><p:cond delay="0"/></p:stCondLst>
                                </p:cTn>
                                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                                <p:attrNameLst><p:attrName>style.visibility</p:attrName></p:attrNameLst>
                              </p:cBhvr>
                              <p:to><p:strVal val="visible"/></p:to>
                            </p:set>
                            <p:animEffect transition="in" filter="{filter_name}"{prop_attr}>
                              <p:cBhvr>
                                <p:cTn id="6" dur="{duration_ms}"/>
                                <p:tgtEl><p:spTgt spid="{shape_id}"/></p:tgtEl>
                              </p:cBhvr>
                            </p:animEffect>'''

    return f'''  <p:timing>
    <p:tnLst>
      <p:par>
        <p:cTn id="1" dur="indefinite" nodeType="tmRoot">
          <p:childTnLst>
            <p:seq concurrent="1" nextAc="seek">
              <p:cTn id="2" dur="indefinite" nodeType="mainSeq">
                <p:childTnLst>
                  <p:par>
                    <p:cTn id="3" fill="hold">
                      <p:stCondLst>
                        <p:cond delay="{delay_ms}"/>
                      </p:stCondLst>
                      <p:childTnLst>
                        <p:par>
                          <p:cTn id="4" fill="hold">
                            <p:childTnLst>
{effect_xml}
                            </p:childTnLst>
                          </p:cTn>
                        </p:par>
                      </p:childTnLst>
                    </p:cTn>
                  </p:par>
                </p:childTnLst>
              </p:cTn>
            </p:seq>
          </p:childTnLst>
        </p:cTn>
      </p:par>
    </p:tnLst>
  </p:timing>'''


def get_available_transitions() -> list[str]:
    """Return the available transition keys."""
    return list(TRANSITIONS.keys())


def get_available_animations() -> list[str]:
    """Return the available animation keys."""
    return list(ANIMATIONS.keys())


def get_transition_help() -> str:
    """Return formatted transition help text."""
    lines = ['Available transitions:']
    for key, info in TRANSITIONS.items():
        lines.append(f"  {key}: {info['name']}")
    return '\n'.join(lines)


def get_animation_help() -> str:
    """Return formatted animation help text."""
    lines = ['Available animations:']
    for key, info in ANIMATIONS.items():
        lines.append(f"  {key}: {info['name']}")
    return '\n'.join(lines)


__all__ = [
    'TRANSITIONS',
    'ANIMATIONS',
    'SPEED_MAP',
    'duration_to_speed',
    'create_transition_xml',
    'create_timing_xml',
    'get_available_transitions',
    'get_available_animations',
    'get_transition_help',
    'get_animation_help',
]


if __name__ == '__main__':
    print('=== Transition XML Example (fade) ===')
    print(create_transition_xml('fade', 0.5))
    print()
    print('=== Timing XML Example (fade) ===')
    print(create_timing_xml('fade', 1.0))
