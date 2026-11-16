# Design: MLOps Platforms Directory

Locked Hallmark system for all pages in `docs/`.

## System
- Genre: modern-minimal
- Theme: Console (`deal 3/3, seed mlops-platforms-directory-comparison-8938·ec679f1f·2026-11-16·r0`, `console: graphite`)
- Axes: dark/grotesk-sans/chromatic-amber · posture: restrained

## Tokens
`docs/styles/tokens.css` is the source of truth.
- Ground & panels: `--color-paper`, `--color-paper-2`, `--color-paper-3`
- Ink & rules: `--color-ink`, `--color-ink-2`, `--color-muted`, `--color-rule`, `--color-rule-2`
- Signals: `--color-accent` (amber for operator/primary action/selected state), `--color-cool` (cool blue for instrument readings/IDs/versions), `--color-ok` / `--color-bad` (capability & diff states)
- Typography: `--font-display` & `--font-body` ("Host Grotesk"), `--font-outlier` ("Atkinson Hyperlegible Mono" for measured values, CLI commands, capability matrix markers, and tabular IDs only).

## Controls
- Primary action: `--color-accent` fill with `--color-accent-ink` (`6px` radius, Host Grotesk 500).
- Secondary action: `1px solid --color-rule-2` on `--color-paper-2`.
- Hairline panels: `.panels` grid with `1px` `--color-rule` seams and `10px` radius; no drop shadows, no glow.

## Exports
`docs/styles/tokens.css`, `docs/styles/base.css`, `docs/styles/site.css`.
