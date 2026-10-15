"""Design theme tokens, CSS styling, and WCAG 2.1 AA contrast validation.

Defines single-source-of-truth tokens for light and dark modes.
All text/background combinations enforce WCAG 2.1 AA contrast ratio >= 4.5:1.
"""
from __future__ import annotations

import math
from typing import NamedTuple


class ColorTokenPair(NamedTuple):
    name: str
    text_color: str
    bg_color: str
    theme: str
    description: str


# Semantic tokens for Light and Dark modes
THEME_TOKENS: list[ColorTokenPair] = [
    # Light mode
    ColorTokenPair("light_primary_text", "#0F172A", "#FFFFFF", "light", "Primary body text on white card background"),
    ColorTokenPair("light_muted_text", "#334155", "#FFFFFF", "light", "Muted descriptive text on white card background"),
    ColorTokenPair("light_surface_text", "#0F172A", "#F1F5F9", "light", "Primary text on light slate secondary background"),
    ColorTokenPair("light_primary_brand", "#1E40AF", "#FFFFFF", "light", "Brand blue header on white card background"),
    ColorTokenPair("light_badge_success", "#14532D", "#DCFCE7", "light", "Success badge text on light green background"),
    ColorTokenPair("light_badge_warning", "#78350F", "#FEF3C7", "light", "Warning badge text on light amber background"),
    ColorTokenPair("light_badge_danger", "#7F1D1D", "#FEE2E2", "light", "Danger/fallback badge text on light red background"),
    ColorTokenPair("light_badge_info", "#1E3A8A", "#DBEAFE", "light", "Info/CTI badge text on light blue background"),

    # Dark mode
    ColorTokenPair("dark_primary_text", "#F8FAFC", "#0F172A", "dark", "Primary text on dark slate page background"),
    ColorTokenPair("dark_card_text", "#F8FAFC", "#1E293B", "dark", "Primary text on dark card background"),
    ColorTokenPair("dark_muted_text", "#CBD5E1", "#1E293B", "dark", "Muted descriptive text on dark card background"),
    ColorTokenPair("dark_primary_brand", "#93C5FD", "#0F172A", "dark", "Brand blue header on dark slate background"),
    ColorTokenPair("dark_badge_success", "#86EFAC", "#052E16", "dark", "Success badge text on dark green background"),
    ColorTokenPair("dark_badge_warning", "#FDE68A", "#451A03", "dark", "Warning badge text on dark amber background"),
    ColorTokenPair("dark_badge_danger", "#FCA5A5", "#450A0A", "dark", "Danger/fallback badge text on dark red background"),
    ColorTokenPair("dark_badge_info", "#93C5FD", "#172554", "dark", "Info/CTI badge text on dark blue background"),
]


def calculate_relative_luminance(hex_color: str) -> float:
    """Calculate WCAG 2.1 relative luminance for a given hex color string."""
    clean_hex = hex_color.lstrip("#")
    r, g, b = [int(clean_hex[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
    
    def channel_linear(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else math.pow((c + 0.055) / 1.055, 2.4)
    
    r_lin = channel_linear(r)
    g_lin = channel_linear(g)
    b_lin = channel_linear(b)
    
    return 0.2126 * r_lin + 0.7152 * g_lin + 0.0722 * b_lin


def calculate_contrast_ratio(hex_foreground: str, hex_background: str) -> float:
    """Calculate WCAG 2.1 contrast ratio between two hex colors."""
    l1 = calculate_relative_luminance(hex_foreground)
    l2 = calculate_relative_luminance(hex_background)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)


def verify_all_tokens_contrast(min_ratio: float = 4.5) -> list[tuple[ColorTokenPair, float, bool]]:
    """Verify that all defined token pairs meet or exceed the specified contrast ratio."""
    results = []
    for pair in THEME_TOKENS:
        ratio = calculate_contrast_ratio(pair.text_color, pair.bg_color)
        results.append((pair, ratio, ratio >= min_ratio))
    return results


def get_custom_css() -> str:
    """Return unified CSS styling with 16px gutters, system font stack, and responsive rules."""
    return """
    <style>
    /* System font stack */
    html, body, [class*="css"] {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    }

    /* 16px Gutters and Container Spacing */
    .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
        padding-left: 1rem;
        padding-right: 1rem;
        max-width: 1440px;
    }

    /* Responsive adjustments for 390px (mobile) */
    @media (max-width: 600px) {
        .block-container {
            padding-left: 0.5rem;
            padding-right: 0.5rem;
        }
        .header-title {
            font-size: 1.25rem !important;
        }
        .metric-strip-card {
            margin-bottom: 8px !important;
        }
    }

    /* Header Bar */
    .header-bar {
        display: flex;
        align-items: center;
        justify-content: space-between;
        flex-wrap: wrap;
        padding: 16px;
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        margin-bottom: 16px;
        gap: 12px;
    }
    .header-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0F172A;
        margin: 0;
    }
    .badge-prototype {
        background-color: #DBEAFE;
        color: #1E40AF;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        border: 1px solid #BFDBFE;
    }

    /* Key Figure Strip */
    .metric-strip {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
        gap: 16px;
        margin-bottom: 16px;
    }
    .metric-strip-card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 16px;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }
    .metric-strip-label {
        font-size: 0.85rem;
        font-weight: 600;
        color: #475569;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .metric-strip-value {
        font-size: 1.5rem;
        font-weight: 700;
        color: #0F172A;
    }

    /* Next Step Advisor Card */
    .advisor-card {
        background: #FFFFFF;
        border: 1px solid #CBD5E1;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.06);
    }
    .advisor-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-bottom: 12px;
        border-bottom: 1px solid #E2E8F0;
        padding-bottom: 8px;
    }

    /* Badges */
    .badge-ok {
        background-color: #DCFCE7;
        color: #14532D;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .badge-fallback {
        background-color: #FEE2E2;
        color: #7F1D1D;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .badge-tie {
        background-color: #FEF3C7;
        color: #78350F;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
    }
    .badge-support {
        background-color: #F1F5F9;
        color: #334155;
        font-weight: 600;
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 0.8rem;
        border: 1px solid #CBD5E1;
    }
    .verdict-chip {
        background-color: #F3E8FF;
        color: #581C87;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 6px;
        font-size: 0.85rem;
        display: inline-block;
        border: 1px solid #E9D5FF;
    }

    /* Candidate Progress Bar */
    .cand-row {
        margin-bottom: 12px;
    }
    .cand-header {
        display: flex;
        justify-content: space-between;
        font-size: 0.9rem;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .cand-bar-container {
        height: 14px;
        background-color: #E2E8F0;
        border-radius: 7px;
        overflow: hidden;
    }
    .cand-bar-fill {
        height: 100%;
        background-color: #1E40AF;
        border-radius: 7px;
    }

    /* Evidence & Context Panels */
    .evidence-box {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 6px;
        padding: 12px;
        margin-top: 8px;
    }
    .c3-item {
        display: flex;
        justify-content: space-between;
        padding: 4px 0;
        border-bottom: 1px dashed #E2E8F0;
        font-size: 0.85rem;
    }
    .c3-label {
        font-weight: 600;
        color: #475569;
    }
    .c3-value-null {
        color: #64748B;
        font-style: italic;
    }

    /* Footer */
    .integrity-footer {
        border-top: 1px solid #CBD5E1;
        padding-top: 16px;
        margin-top: 32px;
        font-size: 0.8rem;
        color: #475569;
        display: flex;
        justify-content: space-between;
        flex-wrap: wrap;
        gap: 12px;
    }
    .provenance-chip {
        background: #F1F5F9;
        padding: 2px 6px;
        border-radius: 4px;
        font-family: monospace;
    }
    </style>
    """
