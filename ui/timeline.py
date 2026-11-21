"""Timeline controls for deterministic Streamlit playback snapshots."""

from __future__ import annotations

from .components import format_relative_time


def render_timeline(st, max_relative_ms: int) -> int:
    """Render a slider-first playback control.

    Streamlit reruns on user interaction, so the slider is the canonical and
    reliable playback state. Play advances one UI tick using the selected speed;
    repeated Play clicks are intentional, deterministic steps rather than a
    hidden client-side animation with fabricated event times.
    """
    st.subheader("Timeline playback")
    maximum = max(0, int(max_relative_ms))
    step = max(1, maximum // 250)
    state_key = "playback_relative_ms"
    if state_key not in st.session_state:
        st.session_state[state_key] = 0
    current = st.slider("Playback position", 0, maximum, int(st.session_state[state_key]), step=step, key="timeline_slider")
    st.session_state[state_key] = current
    st.caption(f"Relative playback offset: {format_relative_time(current)} — not verified wall-clock time.")
    controls = st.columns([1, 1, 1, 4])
    if controls[0].button("Reset"):
        st.session_state[state_key] = 0
        st.session_state.timeline_slider = 0
        st.rerun()
    speed = controls[3].selectbox("Step speed", ["0.5×", "1×", "2×", "4×"], index=1, key="speed")
    multipliers = {"0.5×": 0.5, "1×": 1.0, "2×": 2.0, "4×": 4.0}
    if controls[1].button("Play next"):
        st.session_state[state_key] = min(maximum, current + int(1_000 * multipliers[speed]))
        st.session_state.timeline_slider = st.session_state[state_key]
        st.rerun()
    controls[2].button("Pause", disabled=True, help="Playback is user-stepped to keep Streamlit filters deterministic.")
    return int(st.session_state[state_key])
