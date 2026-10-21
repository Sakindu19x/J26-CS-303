"""
The four contextual similarity functions (guide 01, Section 5).

Each returns a value in [0, 1]. The scalar versions are the readable definitions
and are what the unit tests check; the vectorised versions (one event against many
active groups) are what the correlation engine uses, and must give the same numbers.
"""

import numpy as np


# ---------------------------------------------------------------------------
# Scalar definitions
# ---------------------------------------------------------------------------

def s_time(t_a, t_b, window_s):
    """1 at the same second, falling linearly to 0 at window_s seconds apart."""
    return max(0.0, 1.0 - abs(t_a - t_b) / window_s)


def s_identity(session_a, session_b, ua_a, ua_b, ua_only=0.5):
    """1 for the same login session, ua_only for the same user-agent only, else 0."""
    if session_a and session_a == session_b:
        return 1.0
    if ua_a and ua_a == ua_b:
        return ua_only
    return 0.0


def path_segments(path):
    stripped = path.strip("/")
    return stripped.split("/") if stripped else []


def s_target(path_a, path_b):
    """Share of common leading path segments: /a/b/c vs /a/b/d -> 2/3."""
    a, b = path_segments(path_a), path_segments(path_b)
    if not a and not b:
        return 1.0
    common = 0
    for x, y in zip(a, b):
        if x != y:
            break
        common += 1
    return common / max(len(a), len(b))


def s_attack(labels_a, labels_b):
    """Jaccard overlap of the predicted attack label sets."""
    union = labels_a | labels_b
    return len(labels_a & labels_b) / len(union) if union else 0.0


def s_attack_with_confidence(labels_a, labels_b, probs_a, probs_b):
    """Ablation variant: half Jaccard, half cosine of the probability vectors."""
    probs_a, probs_b = np.asarray(probs_a), np.asarray(probs_b)
    cosine = probs_a @ probs_b / (np.linalg.norm(probs_a) * np.linalg.norm(probs_b) + 1e-12)
    return 0.5 * s_attack(labels_a, labels_b) + 0.5 * float(cosine)


# ---------------------------------------------------------------------------
# Vectorised versions: one event (scalars) against arrays of active groups
# ---------------------------------------------------------------------------

def v_time(t_event, t_groups, window_s):
    return np.maximum(0.0, 1.0 - np.abs(t_event - t_groups) / window_s)


def v_identity(session_event, session_groups, ua_event, ua_groups, ua_only):
    """Codes are integers; -1 means 'absent'."""
    same_session = (session_event >= 0) & (session_groups == session_event)
    same_ua = (ua_event >= 0) & (ua_groups == ua_event)
    return np.where(same_session, 1.0, np.where(same_ua, ua_only, 0.0))


def v_target(segments_event, length_event, segments_groups, lengths_groups):
    """segments_* are padded integer segment codes (-1 padding); see encode_paths()."""
    equal = segments_groups == segments_event
    common = np.cumprod(equal, axis=1).sum(axis=1)
    common = np.minimum(common, np.minimum(lengths_groups, length_event))
    longest = np.maximum(lengths_groups, length_event)
    return np.where(longest == 0, 1.0, common / np.maximum(longest, 1))


def v_attack(mask_event, mask_groups):
    inter = np.bitwise_count(mask_groups & mask_event)
    union = np.bitwise_count(mask_groups | mask_event)
    return np.where(union == 0, 0.0, inter / np.maximum(union, 1))


def v_cosine(probs_event, probs_groups):
    norms = np.linalg.norm(probs_groups, axis=1) * np.linalg.norm(probs_event)
    return (probs_groups @ probs_event) / (norms + 1e-12)


def encode_paths(paths, max_depth=12):
    """Turn URI paths into a padded matrix of integer segment codes plus segment counts."""
    vocabulary = {}
    matrix = np.full((len(paths), max_depth), -1, dtype=np.int64)
    lengths = np.zeros(len(paths), dtype=np.int64)
    for row, path in enumerate(paths):
        segments = path_segments(path)
        lengths[row] = len(segments)
        for col, segment in enumerate(segments[:max_depth]):
            matrix[row, col] = vocabulary.setdefault(segment, len(vocabulary))
    return matrix, lengths
