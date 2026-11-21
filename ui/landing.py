"""Premium tactical landing view for the Player Journey Explorer."""

from __future__ import annotations

from pathlib import Path

import streamlit as st


def inject_landing_styles() -> None:
    st.markdown(
        """
        <style>
        .stApp { background: #090d13; color: #f5f7fa; }
        [data-testid="stHeader"] { background: rgba(9,13,19,.72); }
        .landing-shell { position:relative; overflow:hidden; margin:-3.5rem -1rem 0; padding:2rem 6vw 6rem; min-height:100vh;
          background: radial-gradient(circle at 76% 22%,rgba(107,145,185,.16),transparent 29%), radial-gradient(circle at 14% 82%,rgba(141,175,117,.12),transparent 24%), #090d13; }
        .landing-shell:before { content:""; position:absolute; inset:0; opacity:.34; pointer-events:none;
          background-image: linear-gradient(rgba(198,243,107,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(198,243,107,.05) 1px,transparent 1px);
          background-size:52px 52px; mask-image:linear-gradient(to bottom,black,transparent 78%); }
        .landing-shell:after { content:""; position:absolute; width:720px;height:720px;border:1px solid rgba(198,243,107,.12);border-radius:50%;right:-280px;top:60px;box-shadow:0 0 0 80px rgba(198,243,107,.025),0 0 0 160px rgba(198,243,107,.018);pointer-events:none; }
        .landing-nav { position:relative; z-index:1; display:flex;align-items:center;justify-content:space-between;gap:1rem; padding:.8rem 1rem; border:1px solid rgba(255,255,255,.08); background:rgba(16,23,34,.72); backdrop-filter:blur(16px); }
        .brand { font:700 14px/1 "Space Grotesk",Inter,sans-serif; letter-spacing:.14em; color:#f5f7fa; } .brand b { color:#c6f36b; font-size:20px; vertical-align:-2px; margin-right:7px; }
        .nav-items { display:flex; gap:1.7rem; color:#8c98a8; font-size:.82rem; letter-spacing:.08em; text-transform:uppercase; }
        .nav-status { color:#c6f36b; font:600 .71rem monospace; letter-spacing:.1em; }
        .hero-grid { position:relative;z-index:1; display:grid;grid-template-columns:minmax(0,1.05fr) minmax(320px,.95fr);gap:4.2rem;align-items:center;max-width:1300px;margin:7rem auto 5rem; }
        .kicker { color:#c6f36b; font:600 .78rem monospace; letter-spacing:.18em; margin-bottom:1.4rem; }
        .hero-title { max-width:700px;font:800 clamp(3.2rem,6.4vw,6.7rem)/.91 "Space Grotesk",Inter,sans-serif;letter-spacing:-.075em;margin:0; }
        .lime { color:#c6f36b; } .hero-copy { max-width:570px;color:#aeb8c5;font-size:1.08rem;line-height:1.65;margin:1.75rem 0; }
        .hero-proof { color:#8c98a8;font:600 .74rem monospace;letter-spacing:.11em;margin-top:1.5rem; }
        .cta { display:inline-flex;align-items:center;gap:.65rem;margin-top:1.8rem;padding:.9rem 1.15rem;border:1px solid #c6f36b;background:#c6f36b;color:#18200e;text-decoration:none;font:700 .78rem "Space Grotesk",Inter,sans-serif;letter-spacing:.1em;text-transform:uppercase;transition:transform .2s ease,box-shadow .2s ease; }
        .cta:hover { transform:translateY(-2px);box-shadow:0 10px 32px rgba(198,243,107,.17); }.cta:after{content:"→";font-size:1.1rem;}
        .map-frame { position:relative;border:1px solid rgba(198,243,107,.28);background:#101722;padding:.7rem;box-shadow:0 22px 80px rgba(0,0,0,.38); }
        .map-frame:before { content:"LIVE MAP CALIBRATION";position:absolute;z-index:2;top:18px;left:18px;padding:6px 8px;background:rgba(9,13,19,.78);border:1px solid rgba(255,255,255,.12);color:#c6f36b;font:600 .62rem monospace;letter-spacing:.1em; }
        .map-frame:after { content:"LOGICAL CANVAS 1024 × 1024";position:absolute;z-index:2;bottom:18px;right:18px;padding:6px 8px;background:rgba(9,13,19,.78);color:#f5f7fa;font:.58rem monospace;letter-spacing:.08em; }
        .landing-section { position:relative;z-index:1;max-width:1300px;margin:0 auto;padding:4.5rem 0;border-top:1px solid rgba(255,255,255,.08); }
        .section-label { color:#c6f36b;font:600 .72rem monospace;letter-spacing:.16em; } .section-title { font:700 clamp(2rem,3.5vw,4rem)/1 "Space Grotesk",Inter,sans-serif;letter-spacing:-.055em;margin:.7rem 0 1rem; }
        .section-copy { color:#8c98a8;max-width:650px;line-height:1.6; }
        .stats-grid,.feature-grid { display:grid;grid-template-columns:repeat(4,1fr);gap:1rem;margin-top:2.3rem; }
        .stat,.feature { border:1px solid rgba(255,255,255,.09);background:rgba(21,31,44,.72);padding:1.4rem;min-height:135px; }
        .stat strong { display:block;color:#f5f7fa;font:700 2.1rem/1 "Space Grotesk",Inter,sans-serif;letter-spacing:-.06em; } .stat span,.feature p { color:#8c98a8;font-size:.86rem;line-height:1.55; }
        .feature-index { color:#c6f36b;font:600 .71rem monospace;letter-spacing:.14em; } .feature h3 { margin:.8rem 0 .45rem;font:650 1.1rem "Space Grotesk",Inter,sans-serif; }
        .closing { text-align:center;padding-bottom:1rem; } .closing .section-copy { margin:0 auto 1.5rem; }
        @media(max-width:800px) { .landing-shell { margin:-3.5rem -1rem 0;padding:1rem 1.2rem 3rem; } .nav-items {display:none;} .hero-grid {grid-template-columns:1fr;gap:2rem;margin:4rem auto;} .stats-grid,.feature-grid {grid-template-columns:1fr 1fr;} .hero-title {font-size:clamp(3rem,15vw,5rem);} }
        @media(max-width:480px) { .stats-grid,.feature-grid {grid-template-columns:1fr;} .landing-nav {padding:.65rem;} .nav-status{display:none;} }
        @media(prefers-reduced-motion:no-preference) { .map-frame { animation: rise .8s ease-out both; } @keyframes rise { from {opacity:0;transform:translateY(18px) scale(.98)} to {opacity:1;transform:none} } }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_landing(dataset_root: Path) -> None:
    """Render data-backed landing content; CTA state is managed by app.py."""
    inject_landing_styles()
    hero_image = dataset_root / "minimaps" / "AmbroseValley_Minimap.png"
    # The landing frame is deliberately an abstract tactical surface. It does
    # not claim that decorative routes are observed telemetry; the real,
    # calibrated minimap and journeys live in the dashboard CTA.
    image_style = "min-height:430px;background:radial-gradient(circle at 43% 38%,rgba(198,243,107,.2) 0 2px,transparent 3px),linear-gradient(135deg,transparent 49%,rgba(107,145,185,.5) 49.2% 49.6%,transparent 49.8%),linear-gradient(42deg,transparent 31%,rgba(198,243,107,.42) 31.2% 31.6%,transparent 31.8%),repeating-linear-gradient(0deg,rgba(255,255,255,.045) 0 1px,transparent 1px 42px),repeating-linear-gradient(90deg,rgba(255,255,255,.045) 0 1px,transparent 1px 42px),#101722;"
    st.markdown(
        f"""
        <div class="landing-shell">
          <nav class="landing-nav"><div class="brand"><b>◈</b>PLAYER JOURNEY EXPLORER</div><div class="nav-items"><span>Overview</span><span>Features</span><span>Insights</span><span>About</span></div><div class="nav-status">● LIVE TELEMETRY</div></nav>
          <main class="hero-grid"><div><div class="kicker">GAMEPLAY INTELLIGENCE PLATFORM</div><h1 class="hero-title">SEE HOW YOUR<br>PLAYERS <span class="lime">PLAY.</span><br>UNDERSTAND<br>EVERY MOVE.</h1><p class="hero-copy">Explore player journeys, uncover combat patterns, and understand how players interact with your maps through actual gameplay telemetry.</p><a class="cta" href="?view=dashboard">Explore dashboard</a><div class="hero-proof">796 MATCHES&nbsp;&nbsp;·&nbsp;&nbsp;89K+ EVENTS&nbsp;&nbsp;·&nbsp;&nbsp;3 MAPS&nbsp;&nbsp;·&nbsp;&nbsp;339 PLAYERS</div></div><div class="map-frame" style="{image_style}"></div></main>
          <section class="landing-section"><div class="section-label">01 / FIELD INTELLIGENCE</div><h2 class="section-title">THE BATTLEFIELD, DECODED.</h2><p class="section-copy">From individual player movement to match-wide patterns, understand what is happening across your maps. Every view is built on observed telemetry — not simulated behavior.</p><div class="stats-grid"><div class="stat"><strong>89,104</strong><span>Gameplay events</span></div><div class="stat"><strong>796</strong><span>Recorded matches</span></div><div class="stat"><strong>339</strong><span>Unique player IDs</span></div><div class="stat"><strong>03</strong><span>Active maps</span></div></div></section>
          <section class="landing-section"><div class="section-label">02 / CAPABILITIES</div><h2 class="section-title">OPERATE FROM THE EVIDENCE.</h2><div class="feature-grid"><article class="feature"><div class="feature-index">01</div><h3>Player Journeys</h3><p>Trace recorded routes and distinguish human and bot movement across an actual match.</p></article><article class="feature"><div class="feature-index">02</div><h3>Event Intelligence</h3><p>Explore recorded loot, bot-combat, death, and storm event locations without inferring relationships.</p></article><article class="feature"><div class="feature-index">03</div><h3>Match Playback</h3><p>Step through sorted, relative match time to see trails and events appear in sequence.</p></article><article class="feature"><div class="feature-index">04</div><h3>Gameplay Heatmaps</h3><p>Locate recorded movement and event density while retaining coordinate-mapping limits.</p></article></div></section>
          <section class="landing-section closing"><div class="section-label">READY FOR REVIEW</div><h2 class="section-title">STOP GUESSING.<br>START UNDERSTANDING GAMEPLAY.</h2><p class="section-copy">Open the match explorer to examine the movement, events, and patterns inside every selected match.</p><a class="cta" href="?view=dashboard">Open player journey explorer</a></section>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not hero_image.exists():
        st.info("The dashboard minimap preview is available when the local dataset is configured.")
