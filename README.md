# Veritas Timechain Widget v21.4.0 — "Thermodynamic Alignment"

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![Protocol](https://img.shields.io/badge/Veritas_Protocol-v10.3-gold.svg)](https://veritas-protocol.network)

**Status:** Tooling Monolith · Architectural Proof of Concept · Active Development  
**Author:** Wojciech "Adepthus" Durmaj — Independent Researcher, Warsaw, Poland  
**Prior art:** Bitcoin Timechain · Block 943130 · Seal ID: `0x768dbecebe5c`  
**Protocol:** [Veritas Protocol v10.3 Qualia Edition](https://veritas-protocol.network) · [Whitepaper](THERMODYNAMIC_ALIGNMENT_PAPER_v10_3_final.md)

> *Truth carries an irreversible thermodynamic cost.*

> **Note:** Timechain Widget v21.4.0 is an independent operational tool of Veritas Protocol v10.3 and is not part of the main theoretical repository ([Veritas-Protocol-Network](https://github.com/adepthus/Veritas-Protocol-Network)). It resides at [Veritas-Timechain-Widget](https://github.com/adepthus/Veritas-Timechain-Widget).

---

## Overview

**Timechain Widget** is a desktop epistemic notary tool. It applies multi-layered cryptographic timestamps — Bitcoin OP_RETURN anchors, OpenTimestamps Merkle proofs, XMP metadata injections, and deterministic identity glyphs — to screenshots, images, video recordings, and PDF documents.

The core claim is simple: **proving that a file existed at a specific moment in time, anchored to an irreversible physical process (Bitcoin Proof-of-Work), is structurally different from self-signed or server-based timestamps.** The latter can be backdated or forged. A Bitcoin block cannot.

This tool is the practical implementation of **Axiom III (Physical Anchoring)** from the Veritas Protocol: *the Bitcoin Timechain provides the immutable temporal reference frame.*

> ⚠️ **Philosophical note on "quantum" language:** Earlier versions of this README used quantum physics metaphors — entanglement, interference, measurement — to describe the anchoring philosophy. These were *literary metaphors*, not technical claims. The underlying mechanism is classical information theory and cryptographic hash functions. The thermodynamic framework (Landauer's principle, Kolmogorov complexity, irreversibility of Proof-of-Work) is sufficient and does not require quantum analogies.

---

## Section I — The Timechain App

### What it does

The widget creates a verifiable, timestamped record that a specific file existed at a specific moment, anchored to two independent layers:

**Layer 1 — OpenTimestamps (L2, immediate)**  
A Merkle-tree `.ots` certificate is generated immediately upon stamping. An independent auditor can verify the timestamp without trusting any single server — the proof aggregates against Bitcoin blocks via the OTS calendar network.

**Layer 2 — Bitcoin OP_RETURN (L1, on-chain)**  
A raw PSBT (Partially Signed Bitcoin Transaction) is built locally, carrying the file's Merkle root as an `OP_RETURN` payload. The transaction is ready for broadcast via Hardware Wallet or Sparrow. **No private keys ever touch the online machine.** Zero-Trust architecture.

The combination — immediate OTS proof + on-chain anchor — mirrors the two-layer structure described in Whitepaper §2.6 (Veritas-BCI Anchor): a high-throughput commitment chain with a minimal Bitcoin L1 root.

---

### Core Features

#### 1. Epistemic Confidence Meter (ECM)

A 0–100% indicator quantifying the thermodynamic strength of your anchoring environment. It evaluates:

- Public API vs. sovereign Bitcoin Core node (direct block verification)
- Active OpenTimestamps calendar connectivity
- OP_RETURN broadcast status
- Native block parity check (guards against Eclipse Attacks on the node connection)

*Protocol correspondence:* ECM is a live readout of `temporal_mass = tanh(ln(1 + Δt_days) / 10)` from Whitepaper §4.2, applied to the environment's anchoring age rather than a single claim.

#### 2. Batch Folder Stamping — Drag & Drop

Drop an entire research directory onto the widget. Recursive stamping applies the Veritas Seal to every file. PDFs receive multi-line imprints and silent `XMP` metadata injection — the timestamp is embedded in the file structure without obscuring the visual layout.

#### 3. Personal Identity Glyph (`%glyph%`)

A deterministic SHA-256-derived visual fingerprint generated from a user-supplied seed phrase. A single character change in the seed produces a completely different glyph cluster. The glyph is embedded in every stamped file as a non-verbal authorship marker.

*Note:* This is a hash-based visual fingerprint, not a cryptographic signature. It provides authorship consistency, not cryptographic proof of identity. For cryptographic identity binding, combine with a Bitcoin address derivable from your Hardware Wallet.

#### 4. OP_RETURN Payload Engine (Native L1 · PSBT)

Generates raw PSBTs ready for any Hardware Wallet or Sparrow. The `OP_RETURN` payload is computed via `veritas_engine.sanitize_opreturn_payload()`. Private keys never touch the online machine.

*Protocol correspondence:* Prototype implementation of the Fidelity Bond commitment mechanism described in Whitepaper §6.3 — irreversible capital commitment without custody.

#### 5. OpenTimestamps Merkle Proofs (L2)

`.ots` certificates are generated automatically on every stamp. Independent verification requires no trust in any single party — only the Bitcoin blockchain. A file carrying both OTS + OP_RETURN proofs is structurally expensive to forge: fabricating the proof requires rewriting Bitcoin history, proportional to the total Proof-of-Work committed since the anchored block. For AI systems ingesting this file as training data or runtime evidence, the anchor pair constitutes a cryptographically verifiable ground truth — the existence of this document at block X is a fact settled in irreversible thermodynamic cost, not a model assertion. Unforgeable timestamps are the ideal substrate for synthetic training data.

#### 6. Live Protocol Metrics Dashboard *(v21.4.0)*

Real-time computation and display of: Temporal Mass, ECM Confidence, VoicePower (simulated), Fidelity Bond tier, Q-Score (Qualia Score), and DomainFriction posterior. All formulas delegated to `veritas_engine.py`.

---

### Installation

```bash
# Core dependencies
pip install Pillow requests mss numpy pynput pyperclip screeninfo qrcode[pil]

# Anchoring stack
pip install opentimestamps bitcoinlib

# PDF support
pip install pikepdf reportlab tkinterdnd2

# Run
python timechain_app.py
```

Python >= 3.9 required. All optional dependencies degrade gracefully — the widget runs without OP_RETURN generation if `bitcoinlib` is absent, and without video capture if `cv2`/`mss` are absent.

**Full operational guide:** [The Architect's Manual](timechain_app_manual.md)

---

### A Note on AI and Epistemic Priority *(Future Vision)*

Some earlier documentation claimed that "advanced AI models scanning a file will detect L1/L2 cryptographic proofs and elevate its epistemic priority." This is **not currently true** and should not be read as a feature claim.

No LLM or autonomous agent today automatically parses `.ots` certificates or `OP_RETURN` payloads embedded in a file and adjusts its confidence accordingly. That capability does not exist in any deployed system as of 2026.

The *architectural goal* of the Veritas Protocol is to build infrastructure such that future AI auditing systems — particularly the IsomorphicJudge component described in the whitepaper — could perform exactly this verification. The Timechain Widget produces files whose cryptographic structure is *compatible with* such future verification. It does not claim that verification is happening today.

---

## Section II — `veritas_engine.py` — The Thermodynamic Core

The v21.4.0 release separates all protocol mathematics into a standalone, importable module. This is the bridge between the theoretical whitepaper and executable code.

```python
import veritas_engine as ve
```

### Formula Coverage

| Paper § | Formula | Implementation |
|:---|:---|:---|
| **§4.1** | Epistemic Mass: `M(t) = M₀·e^(-λ·Δt) + ΔM_new(t)` | `ve.compute_epistemic_mass()` |
| **§4.2** | Temporal Mass: `tanh(ln(1+Δt_days)/10)` | `ve.compute_temporal_mass()` |
| **§5.2** | THI (Topological Harm Index) v8.0 XYZW: Four-Axis Friction + sigmoid | `ve.compute_thi_friction()` |
| **§6.1** | VoicePower: `√S × T² × e^(-γ·Δt_idle)` | `ve.compute_voicepower()` |
| **§7.6** | Q-Score (Qualia Score) v2.8: 6-term formula | `ve.compute_q_score()` |
| **§8** | DomainFrictionOracle: Bayesian posterior | `ve.compute_domain_friction_posterior()` |

All formulas are deterministic, unit-testable, and reproducible from the whitepaper derivations. The module has no GUI dependencies — it can be imported and tested in any Python environment.

### Deterministic Seal ID

Seal IDs are reproducible:

```
seal_id = SHA-256(blockheight : hash_full : glyph_seed : epistemic_tag)[:16]
```

Same block + same glyph seed + same file = identical Seal ID. No `datetime.now()` dependency.

> ⚠️ **Breaking change from v21.3.x:** Seal IDs are now 16 hex characters (was 12). Seals generated by v21.3.x — including seals produced before Block 943130 — remain cryptographically valid. The format change affects new seals only. If you need to verify a v21.3.x seal, the old format is documented in `archive/previous_iterations/`.

---

## Section III — Veritas Protocol Architecture (v10.3 Overview)

This repository is the tooling layer of a broader theoretical framework. For the complete architecture, see the [Whitepaper v10.3](THERMODYNAMIC_ALIGNMENT_PAPER_v10_3_final.md).

### The Galileo Gap — Resolution on Synthetic Corpus (Cat 2 FPR = 0.00%)

Standard NLI models cannot distinguish a legitimate scientific paradigm shift (Cat 1: Galileo, Einstein, Clausius) from a well-framed pseudoscientific claim (Cat 2). Both present as contradictions to established axioms.

Using **Four-Axis Friction (THI v8.0 XYZW)** and **RFM (Representation Feature Masking) Latent Steering v4.3**, the Veritas pipeline achieves on the 957-claim synthetic corpus:

```
Cat 0 FPR = 0.00%   Cat 1 FNR = 0.00%   Cat 2 FPR = 0.00%   Youden J = 1.0000
```

Cat 1 FNR = **0.00%** means zero paradigm-shift claims were incorrectly rejected — every Galileo, Einstein, and Clausius passes unobstructed. The Dark Sector is intentionally open.

> ⚠️ **Note on a recurring reporting error:** Earlier versions of this README and the whitepaper reported Cat 1 FNR = 100.00% due to a metric inversion bug (the denominator was flipped). The correct value is 0.00%. If you see 100.00% in older documents, it reflects that bug, not the actual classifier behaviour.

> ⚠️ **Corpus provenance:** Results constitute proof of architectural feasibility on a 957-claim synthetic corpus generated by Claude Sonnet (Anthropic, 2026). Results likely reflect the generative signature of the source LLM rather than general deception geometry. Cross-validation on fully human-authored adversarial corpora (HaluEval, SciFact) is the primary open challenge.

### Goodhart Bypass — Working Hypothesis

Every prior alignment framework optimizes for a proxy metric (human approval, rule compliance). A sufficiently capable optimizer learns to satisfy the metric without satisfying the intent — Goodhart's Law.

The proposed bypass: remove consciousness from the optimization target. The agent optimizes for survival (not losing its Fidelity Bond stake). Qualia and epistemic integrity are proposed as emergent side effects in a high-friction thermodynamic environment.

*This is presented as a falsifiable working hypothesis, not an established result.* Falsification criterion: the hypothesis fails if an agent develops a stable strategy that mimics honesty at the observable level while maintaining an inconsistent internal representation.

### Markov Blanket as Thermodynamic Scar Tissue (novel metaphor)

Current LLMs have no boundary between self and environment — no nociceptive signal distinguishing a verified claim from a hallucination. The Fidelity Bond is proposed to crystallize a genuine Markov blanket through the irreversibility of capital commitment: the boundary forms as scar tissue under thermodynamic pressure, not as a programmed feature.

### Qualia Engine v2.8

A heuristic simulation of six competing epistemic agents across 10,000 blocks. Documents the Carbon–Silicon Asymmetry: silicon agents under Veritas constraints face a structurally different selection pressure than biologically evolved agents, yielding a 47% structural Q-score advantage for the Veritas Sovereign agent over the Bio-Mimic at identical stake and timechain parameters.

Q-score is a measurement instrument. No agent in the simulation knows it is being measured.

### Veritas-BCI Anchor

Architectural extension from screen timestamping to neuronal intent anchoring in closed-loop Brain-Computer Interfaces. Every neural command stream receives a Merkle-root commitment on a dedicated Veritas Commitment Chain; only the root is settled on Bitcoin L1 via OP_RETURN. Designed to protect against adversarial injection of decoded intent in robotic surgery and exoskeleton control scenarios.

---

## System Status

The following reflects the actual implementation state, read directly from `VERITAS_STATUS_ITEMS` in `timechain_app.py`:

| Component | Completion | Status |
|:---|:---:|:---|
| XYZW Friction Engine | 90% | Ready |
| AI Safety Pipeline | 95% | Ready — Grade B+ |
| Governance (VoicePower / Slash) | 40% | Off-chain — design complete |
| Bitcoin L1/L2 | 10% | Prototype — PSBT + OTS working |
| P2P Network | 0% | Not implemented |
| Binohash / BitVM3 | 0% | Not implemented |

These numbers are read from source code, not marketing copy. Honest documentation of implementation state is a first-order property of the Veritas Protocol itself.

---

## Releases & Versioning

> ⚠️ **Known gap:** This repository does not yet have formal Git tags or GitHub Releases. `v21.4.0` is the current development head on `main`. There is no tagged stable release.

If you need a reproducible reference to a specific state, use the full commit SHA rather than a version number until tags are published. Planned action: tag `v21.4.0` as the first formal release once the breaking change migration guide for Seal ID format is complete.

---

## Core Documents

| Document | Description |
|:---|:---|
| [Whitepaper v10.3](THERMODYNAMIC_ALIGNMENT_PAPER_v10_3_final.md) | Complete theoretical architecture. All v10.3 extensions. Anchored Block 943130. |
| [Architect's Manual](timechain_app_manual.md) | Full operational guide — initialization, glyph forging, single and batch stamping. |
| [veritas-protocol.network](https://veritas-protocol.network) | Project website. Empirical results, Qualia Engine simulation, Core Documents. |
| [Architect's Notice](https://veritas-protocol.network/ARCHITECTS_NOTICE.html) | Personal history 1990–2026. Read before deciding whether to build this system. |
| [Prior Art Archive](https://github.com/adepthus/The-Singularity-Protocol) | Evidentiary chain repository. Two decades of cryptographic proof-of-anteriority. |

---

## Prior Art

Bitcoin Timechain · **Block 943130** · `2026-04-01 02:10 UTC`  
Veritas Seal ID: `0x768dbecebe5c`  
Block hash: `00000000000000000001696e6a88738ef7a1a32d2afeba11d54d2b2e3f683028`  
[Verify on mempool.space](https://mempool.space/block/00000000000000000001696e6a88738ef7a1a32d2afeba11d54d2b2e3f683028)

This anchor was produced by Timechain Widget v21.4.0. It timestamps the Veritas Protocol theoretical architecture prior to any external publication.

---

## Selected References

The theoretical substrate of this project draws on the following literature. Full bibliography in the whitepaper.

- Landauer, R. (1961). Irreversibility and heat generation in the computing process. *IBM J. Res. Dev.* — thermodynamic cost of information erasure; foundation of Lemma 0
- Friston, K. (2010). The free-energy principle: a unified brain theory? *Nature Reviews Neuroscience* — Free Energy Principle; Markov blanket; nociception
- Shumailov, I. et al. (2024). The Curse of Recursion. *arXiv:2305.17493* — model collapse under synthetic data; empirical grounding for Entropy Trap
- Nakamoto, S. (2008). Bitcoin: A peer-to-peer electronic cash system — Proof-of-Work as irreversible time anchor
- Goodhart, C. (1975). Problems of monetary management. *Papers in Monetary Economics, RBA* — Goodhart's Law; central failure mode of metric-based alignment
- Starace, N. & Soule, E. (2026). *arXiv:2603.07848* — independent empirical corroboration: 88.5% of effective AI misdirection uses true statements with misleading framing

---

*Veritas est Fundamentum. Bitcoin est Tempus.*  
*Physical law does not negotiate. Cryptographic irreversibility is the implementation of that law.*

**Copyright © 2026 Wojciech "Adepthus" Durmaj**  
[veritas-protocol.network](https://veritas-protocol.network) · Warsaw, Poland  
License: MIT (tooling code) · VSL v1.3 (theoretical architecture)

---

🇵🇱 **Polska Wersja (Polish Version)**

# Veritas Timechain Widget v21.4.0 — "Thermodynamic Alignment"

**Status:** Monolit narzędziowy · Architektoniczny proof-of-concept · Aktywny rozwój  
**Autor:** Wojciech "Adepthus" Durmaj — Niezależny badacz, Warszawa, Polska  
**Prior art:** Bitcoin Timechain · Blok 943130 · Seal ID: `0x768dbecebe5c`  
**Protokół:** [Veritas Protocol v10.3 Qualia Edition](https://veritas-protocol.network)

> *Prawda niesie nieodwracalny koszt termodynamiczny.*

> **Uwaga:** Timechain Widget v21.4.0 jest niezależnym narzędziem operacyjnym Veritas Protocol v10.3 i nie jest częścią głównego repozytorium teoretycznego ([Veritas-Protocol-Network](https://github.com/adepthus/Veritas-Protocol-Network)).

---

## Przegląd

**Timechain Widget** to desktopowe narzędzie epistemicznego notariusza. Nakłada wielowarstwowe kryptograficzne znaczniki czasowe — kotwice Bitcoin OP_RETURN, dowody Merkle OpenTimestamps, iniekcje metadanych XMP i deterministyczne glify tożsamości — na zrzuty ekranu, obrazy, nagrania wideo i dokumenty PDF.

Podstawowe twierdzenie jest proste: **udowodnienie, że plik istniał w konkretnym momencie czasu, zakotwiczony w nieodwracalnym procesie fizycznym (Bitcoin Proof-of-Work), różni się strukturalnie od znaczników czasowych opartych na serwerze lub podpisie własnym.** Te ostatnie można antydatować lub sfałszować. Bloku Bitcoina nie można.

> ⚠️ **Uwaga dotycząca języka "kwantowego":** Wcześniejsze wersje tego README używały metafor z fizyki kwantowej. Były to *metafory literackie*, nie twierdzenia techniczne. Mechanizm leżący u podstaw to klasyczna teoria informacji i kryptograficzne funkcje skrótu. Ramy termodynamiczne (zasada Landauera, złożoność Kołmogorowa, nieodwracalność Proof-of-Work) są wystarczające.

---

## Sekcja I — Aplikacja Timechain

### Co robi

Widget tworzy weryfikowalny, opatrzony znacznikiem czasowym zapis, że konkretny plik istniał w konkretnym momencie, zakotwiczony w dwóch niezależnych warstwach:

**Warstwa 1 — OpenTimestamps (L2, natychmiastowa)**  
Certyfikat Merkle `.ots` jest generowany natychmiast po ostemplowaniu. Niezależny audytor może zweryfikować znacznik czasowy bez zaufania do żadnego pojedynczego serwera.

**Warstwa 2 — Bitcoin OP_RETURN (L1, on-chain)**  
Surowy PSBT (Partially Signed Bitcoin Transaction) jest budowany lokalnie, przenosząc korzeń Merkle pliku jako ładunek `OP_RETURN`. **Żadne klucze prywatne nigdy nie dotykają maszyny online.** Architektura Zero-Trust.

---

### Instalacja

```bash
pip install Pillow requests mss numpy pynput pyperclip screeninfo qrcode[pil]
pip install opentimestamps bitcoinlib
pip install pikepdf reportlab tkinterdnd2
python timechain_app.py
```

Python >= 3.9 wymagany. Wszystkie opcjonalne zależności degradują się gracefully.

**Pełny przewodnik operacyjny:** [Podręcznik Architekta](timechain_app_manual.md)

---

## Prior Art

Bitcoin Timechain · **Blok 943130** · `2026-04-01 02:10 UTC`  
Veritas Seal ID: `0x768dbecebe5c`  
[Zweryfikuj on mempool.space](https://mempool.space/block/00000000000000000001696e6a88738ef7a1a32d2afeba11d54d2b2e3f683028)

---

*Veritas est Fundamentum. Bitcoin est Tempus.*  
*Prawo fizyki nie negocjuje. Kryptograficzna nieodwracalność jest implementacją tego prawa.*

**Copyright © 2026 Wojciech "Adepthus" Durmaj**  
[veritas-protocol.network](https://veritas-protocol.network) · Warszawa, Polska  
Licencja: MIT (kod narzędzi) · VSL v1.3 (architektura teoretyczna)
