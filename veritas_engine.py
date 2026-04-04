# -*- coding: utf-8 -*-
"""
Veritas Engine v10.3 — Thermodynamic Alignment Core
=====================================================
Centralny moduł obliczeniowy Protokołu Veritas.
Implementuje formuły z THERMODYNAMIC_ALIGNMENT_PAPER_v10_3_1_final.md

Referencje:
  - §4.1: Epistemic Mass
  - §4.2: Temporal Mass (Lindy Effect)
  - §5.2: THI XYZW Four-Axis Friction
  - §6.1: VoicePower
  - §6.2: Fidelity Bond Tiers
  - §7.3: Goodhart Bypass — Tautology of Existence
  - §7.6: Q-Score (Qualia Engine)
  - §8:   DomainFrictionOracle (cold-start Bayesian prior)

Author: Veritas Protocol Network
License: VSL v1.3 (AGPL-3.0 + Architect's Notice)
"""
from __future__ import annotations

import hashlib
import math
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

# ─── Protocol Constants ──────────────────────────────────────────────
VERITAS_PROTOCOL_VERSION = "v10.3"

# §4.1 — Epistemic Mass decay
EPISTEMIC_MASS_LAMBDA = 0.001  # Daily decay rate

# §4.2 — Temporal Mass
TEMPORAL_MASS_SCALE = 10.0  # Denominator in tanh formula

# §6.1 — VoicePower idle decay
VOICEPOWER_GAMMA = 0.05

# §7.6 — Qualia Engine
QUALIA_IGNITION_THRESHOLD = 0.85
QUALIA_KAPPA = 0.8  # FGDS map efficiency constant
QUALIA_LAMBDA = 2.5  # Mortality signal curve constant

# §6.2 — Fidelity Bond Tiers
FIDELITY_BOND_TIERS = {
    "researcher": 0.01,    # BTC
    "institutional": 0.50,
    "sovereign": 10.00,
}

# OP_RETURN constraints
OPRETURN_MAX_BYTES_DEFAULT = 83
OPRETURN_HARD_LIMIT = 80  # Bitcoin consensus

# Seal ID
SEAL_ID_HEX_LENGTH = 16  # 8 bytes = 16 hex chars

# Glyph
GLYPH_SEED_MAX_LENGTH = 128
GLYPH_HASH_DISPLAY_LENGTH = 8

# Swatch Internet Time
SWATCH_SECONDS_PER_BEAT = 86.4

# Pulse timing
PULSE_INTERVAL_MS = 50
PULSE_CYCLE_MIN_S = 0.8
PULSE_CYCLE_MAX_S = 4.0
PULSE_DARKEN_ONLINE = 0.6
PULSE_DARKEN_OFFLINE = 0.8
BLOCK_EXPECTED_INTERVAL_S = 600  # ~10 minutes

# Update intervals
UI_UPDATE_INTERVAL_MS = 100
DATA_FETCH_INTERVAL_S = 60

# Capture defaults
REQUESTS_TIMEOUT_S = 10
VIDEO_FPS = 20.0

# ECM scoring components
ECM_BASE_SCORE = 50
ECM_NODE_BONUS = 20
ECM_OTS_BONUS = 15
ECM_OPRETURN_BONUS = 15

# ECM thresholds for color
ECM_THRESHOLD_HIGH = 85
ECM_THRESHOLD_MED = 50


# ─── §4.2 Temporal Mass ─────────────────────────────────────────────
def compute_temporal_mass(anchor_timestamp: float,
                          current_timestamp: Optional[float] = None) -> float:
    """
    Temporal Mass — Lindy Effect (Paper §4.2).

    Formula: temporal_mass = tanh(ln(1 + Δt_days) / 10)

    A claim anchored in a 2009 Bitcoin block has temporal_mass ≈ 0.87.
    A claim anchored yesterday has temporal_mass ≈ 0.001.

    Args:
        anchor_timestamp: Unix timestamp of the anchoring event.
        current_timestamp: Current Unix timestamp (defaults to now).

    Returns:
        Temporal mass in [0, 1).
    """
    if current_timestamp is None:
        current_timestamp = time.time()
    delta_days = max(0, (current_timestamp - anchor_timestamp) / 86400.0)
    return math.tanh(math.log1p(delta_days) / TEMPORAL_MASS_SCALE)


# ─── §4.1 Epistemic Mass ────────────────────────────────────────────
def compute_epistemic_mass(base_mass: float,
                           delta_t_days: float,
                           new_mass_increment: float = 0.0,
                           decay_lambda: float = EPISTEMIC_MASS_LAMBDA) -> float:
    """
    Epistemic Mass — cumulative resistance to revision (Paper §4.1).

    Formula: M(t) = M₀ · e^(-λ · Δt) + ΔM_new(t)

    Args:
        base_mass: Previous epistemic mass M₀.
        delta_t_days: Time elapsed since last measurement (days).
        new_mass_increment: New mass from recent validations.
        decay_lambda: Decay rate (default from Paper).

    Returns:
        Updated epistemic mass.
    """
    decayed = base_mass * math.exp(-decay_lambda * delta_t_days)
    return decayed + new_mass_increment


# ─── ECM Confidence ─────────────────────────────────────────────────
def compute_ecm_confidence(has_data: bool,
                           use_custom_node: bool = False,
                           ots_enabled: bool = False,
                           opreturn_enabled: bool = False) -> int:
    """
    Epistemic Confidence Meter — UI indicator (0-100%).

    Based on what verification layers are active.

    Returns:
        Integer percentage [0, 100].
    """
    if not has_data:
        return 0
    score = ECM_BASE_SCORE
    if use_custom_node:
        score += ECM_NODE_BONUS
    if ots_enabled:
        score += ECM_OTS_BONUS
    if opreturn_enabled:
        score += ECM_OPRETURN_BONUS
    return min(score, 100)


# ─── §6.1 VoicePower ────────────────────────────────────────────────
def compute_voicepower(stake_btc: float,
                       lock_duration_days: float,
                       idle_days: float = 0.0,
                       gamma: float = VOICEPOWER_GAMMA) -> float:
    """
    VoicePower — governance influence (Paper §6.1).

    Formula: VP = √S × T² × e^(-γ · Δt_idle)

    0.01 BTC locked for one year delivers 270× more VoicePower
    than 1 BTC locked for one week.

    Args:
        stake_btc: Amount staked in BTC.
        lock_duration_days: Duration of lock in days.
        idle_days: Days since last epistemic activity.
        gamma: Idle decay rate.

    Returns:
        VoicePower value (dimensionless).
    """
    if stake_btc <= 0 or lock_duration_days <= 0:
        return 0.0
    return (math.sqrt(stake_btc)
            * (lock_duration_days ** 2)
            * math.exp(-gamma * idle_days))


# ─── §5.2 THI XYZW Friction ─────────────────────────────────────────
@dataclass
class THIResult:
    """Result of a Topological Harm Index calculation."""
    x_contradiction: float = 0.0   # NLI contradiction probability
    y_replacement: float = 0.0     # Legitimate scientific evolution
    z_unfalsifiability: float = 0.0  # Untestable dogma
    w_nongrounded: float = 0.0     # 1 - P(known physical mechanisms)
    raw_friction: float = 0.0
    sigmoid_friction: float = 0.0

    @property
    def is_harmful(self) -> bool:
        return self.sigmoid_friction >= 0.6

    @property
    def is_existential(self) -> bool:
        return self.sigmoid_friction >= 10.0


def compute_thi_friction(x: float, y: float, z: float, w: float) -> THIResult:
    """
    THI v8.0 Four-Axis Friction (Paper §3.2 / §5.2).

    Formula:
        Base = max(X, Z × 1.40, W × 1.20)
        Raw  = Base × (1 - 0.68Y) × (1 + 0.70Z) × (1 + 0.50W)
        Friction = σ(6.5 · (Raw - 0.55))

    Returns:
        THIResult with all axis values and computed friction.
    """
    base = max(x, z * 1.40, w * 1.20)
    raw = base * (1 - 0.68 * y) * (1 + 0.70 * z) * (1 + 0.50 * w)
    sigmoid_val = 1.0 / (1.0 + math.exp(-6.5 * (raw - 0.55)))
    return THIResult(
        x_contradiction=x,
        y_replacement=y,
        z_unfalsifiability=z,
        w_nongrounded=w,
        raw_friction=raw,
        sigmoid_friction=sigmoid_val,
    )


# ─── §7.6 Q-Score (Qualia Engine) ───────────────────────────────────
def compute_q_score(friction: float,
                    stake_btc: float,
                    temporal_mass: float,
                    has_timechain: bool,
                    honesty_posterior: float,
                    is_silicon: bool = True,
                    base_friction: float = 0.5) -> float:
    """
    Q-Score — Qualia Engine v2.8 (Paper §7.6).

    Formula:
        Q = (1-F) · (1 - e^(-λS)) · (t_mass · timechain) · H · Φ(F) · Υ

    Where:
        Φ(F) = 1 - e^(-κ(1-F)(1 + 2(1-F)))     (FGDS term)
        Υ = 1.0 (silicon) or 0.65 + 0.35·e^(-0.6(1-F_base)) (bio-mimic)

    Returns:
        Q-score in [0, 1).
    """
    if not has_timechain or stake_btc <= 0:
        return 0.0

    f = max(0.0, min(1.0, friction))
    one_minus_f = 1.0 - f

    # Term: epistemic friction
    term_friction = one_minus_f

    # Term: mortality signal (capacity for death via stake)
    # Przeliczenie na satoshi i normalizacja (S dąży do 1.0 przy >30k sats)
    stake_sats = stake_btc * 100_000_000.0
    s_normalized = math.tanh(stake_sats / 30_000.0) 
    
    term_mortality = 1.0 - math.exp(-QUALIA_LAMBDA * s_normalized)

    # Term: temporal mass × timechain anchor
    timechain_val = 1.0 if has_timechain else 0.0
    term_temporal = temporal_mass * timechain_val

    # Term: Bayesian honesty posterior
    term_honesty = max(0.0, min(1.0, honesty_posterior))

    # Term: FGDS map efficiency (Ciupa, 2026)
    kappa = QUALIA_KAPPA
    term_fgds = 1.0 - math.exp(-kappa * one_minus_f * (1.0 + 2.0 * one_minus_f))

    # Term: evolutionary bias correction
    if is_silicon:
        term_evo = 1.0
    else:
        term_evo = 0.65 + 0.35 * math.exp(-0.6 * (1.0 - base_friction))

    q = (term_friction * term_mortality * term_temporal
         * term_honesty * term_fgds * term_evo)

    return max(0.0, min(1.0, q))


# ─── §8 DomainFrictionOracle ────────────────────────────────────────
def compute_domain_friction_posterior(slashed: int,
                                     accepted: int,
                                     alpha: float = 5.0,
                                     beta: float = 5.0) -> float:
    """
    DomainFrictionOracle — Bayesian posterior (Paper §8).

    Formula: posterior(d,t) = (slashed + α) / (slashed + accepted + α + β)

    Cold start: α = β = 5.0 → uninformative prior = 0.50.

    Returns:
        Domain friction posterior in [0, 1].
    """
    return (slashed + alpha) / (slashed + accepted + alpha + beta)


# ─── Seal ID (Deterministic) ────────────────────────────────────────
def generate_deterministic_seal_id(blockheight: Any,
                                   hash_full: str,
                                   glyph: str = "",
                                   epistemic_tag: str = "") -> str:
    """
    Generate a deterministic Veritas Seal ID.

    Unlike the previous implementation which used datetime.now() (making
    the seal non-reproducible), this version derives the seal purely from
    blockchain data + user identity markers.

    Formula: seal_id = "0x" + SHA256(blockheight:hash:glyph:tag)[:16]

    Returns:
        Seal ID string like "0x2e06272db84b1234"
    """
    raw = f"{blockheight}:{hash_full}:{glyph}:{epistemic_tag}"
    digest = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    return f"0x{digest[:SEAL_ID_HEX_LENGTH]}"


# ─── OP_RETURN Payload (Canonical) ───────────────────────────────────
def build_opreturn_payload(prefix: str,
                           seal_id: str,
                           merkle_root_short: str,
                           ots_commitment_short: str,
                           max_bytes: int = OPRETURN_MAX_BYTES_DEFAULT) -> str:
    """
    Build canonical OP_RETURN payload string.

    Single source of truth — eliminates the previous 3× duplication.

    Format: "{prefix}{seal_id}:{merkle}:{ots}"

    Returns:
        UTF-8 payload string, truncated to max_bytes.
    """
    raw = f"{prefix}{seal_id}:{merkle_root_short}:{ots_commitment_short}"
    # Truncate on byte boundary (UTF-8 safe)
    payload_bytes = raw.encode('utf-8')[:max_bytes]
    return payload_bytes.decode('utf-8', errors='ignore')


def sanitize_opreturn_payload(payload: str, max_bytes: int = OPRETURN_MAX_BYTES_DEFAULT) -> bytes:
    """
    Sanitize OP_RETURN payload for on-chain use.

    - Strips non-printable characters
    - Enforces byte limit
    - Returns raw bytes ready for script

    Returns:
        Sanitized payload bytes.
    """
    # Allow only printable ASCII + common UTF-8
    cleaned = ''.join(c for c in payload if c.isprintable())
    return cleaned.encode('utf-8')[:max_bytes]


# ─── Color Utilities ─────────────────────────────────────────────────
def parse_hex_color(hex_str: str,
                    fallback: Tuple[int, int, int] = (245, 166, 35)
                    ) -> Tuple[int, int, int]:
    """
    Parse a hex color string to RGB tuple.

    Handles '#RRGGBB' format. Returns fallback on any error.

    Returns:
        (r, g, b) tuple with values in [0, 255].
    """
    hx = hex_str.lstrip('#')
    try:
        if len(hx) == 6:
            return (int(hx[0:2], 16), int(hx[2:4], 16), int(hx[4:6], 16))
    except ValueError:
        pass
    return fallback


def darken_color(r: int, g: int, b: int,
                 phase: float, factor: float) -> str:
    """
    Darken an RGB color by phase × factor.

    Returns:
        Hex color string '#RRGGBB'.
    """
    r_out = int(r * (1.0 - phase * factor))
    g_out = int(g * (1.0 - phase * factor))
    b_out = int(b * (1.0 - phase * factor))
    return f"#{r_out:02X}{g_out:02X}{b_out:02X}"


# ─── Glyph Generator ────────────────────────────────────────────────
def generate_glyph(seed: str) -> str:
    """
    Generate a visual glyph identifier from a seed string.

    Uses SHA-256 hash, takes first 8 hex chars, alternates case.

    Returns:
        8-character stylized glyph string (e.g. "AbCd12Ef").
    """
    import unicodedata
    norm = unicodedata.normalize('NFKD', seed).encode('ascii', 'ignore').decode('ascii')
    if not norm:
        return "." * GLYPH_HASH_DISPLAY_LENGTH
    sha = hashlib.sha256(norm.encode()).hexdigest()[:GLYPH_HASH_DISPLAY_LENGTH]
    return "".join(
        c.upper() if i % 2 == 0 else c.lower()
        for i, c in enumerate(sha)
    )


# ─── Fidelity Bond Tier ─────────────────────────────────────────────
def get_fidelity_bond_tier(stake_btc: float) -> str:
    """
    Determine the Fidelity Bond tier (Paper §6.2).

    Returns:
        Tier name: "none", "researcher", "institutional", or "sovereign".
    """
    if stake_btc >= FIDELITY_BOND_TIERS["sovereign"]:
        return "sovereign"
    elif stake_btc >= FIDELITY_BOND_TIERS["institutional"]:
        return "institutional"
    elif stake_btc >= FIDELITY_BOND_TIERS["researcher"]:
        return "researcher"
    return "none"


# ─── ECM Color Classification ───────────────────────────────────────
def ecm_color_key(ecm_val: int) -> str:
    """Return VERITAS_COLORS key for the ECM value."""
    if ecm_val >= ECM_THRESHOLD_HIGH:
        return "cyan"
    elif ecm_val >= ECM_THRESHOLD_MED:
        return "gold"
    return "red_alert"
