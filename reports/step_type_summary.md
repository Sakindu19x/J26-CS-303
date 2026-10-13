# AttackMate Step Type & Composite Step Analysis

## 1. Step Type Distribution Per Episode

| Episode | Step Type | Total Steps | Labeled Steps | Unlabeled Steps | Description / Role |
|---|---|---|---|---|---|
| **E1** | `msf-module` | 1 | 1 | 0 | Attack command / action |
| **E1** | `msf-session` | 20 | 16 | 4 | Attack command / action |
| **E1** | `shell` | 5 | 4 | 1 | Attack command / action |
| **E1** | `sleep` | 5 | 0 | 5 | Attack command / action |
| **E1** | `ssh` | 7 | 6 | 1 | Attack command / action |
| **E2** | `debug` | 1 | 0 | 1 | Attack command / action |
| **E2** | `mktemp` | 4 | 0 | 4 | Attack command / action |
| **E2** | `regex` | 1 | 1 | 0 | Attack command / action |
| **E2** | `sftp` | 1 | 1 | 0 | Attack command / action |
| **E2** | `shell` | 1 | 0 | 1 | Attack command / action |
| **E2** | `sleep` | 1 | 0 | 1 | Attack command / action |
| **E2** | `sliver` | 2 | 1 | 1 | Attack command / action |
| **E2** | `sliver-session` | 16 | 16 | 0 | Attack command / action |
| **E2** | `ssh` | 2 | 2 | 0 | Attack command / action |
| **E3** | `include` | 1 | 0 | 1 | Attack command / action |
| **E3** | `loop` | 1 | 1 | 0 | Attack command / action |
| **E3** | `mktemp` | 1 | 0 | 1 | Attack command / action |
| **E3** | `msf-module` | 1 | 0 | 1 | Attack command / action |
| **E3** | `msf-payload` | 1 | 0 | 1 | Attack command / action |
| **E3** | `msf-session` | 15 | 14 | 1 | Attack command / action |
| **E3** | `setvar` | 1 | 0 | 1 | Attack command / action |
| **E3** | `shell` | 1 | 0 | 1 | Attack command / action |
| **E3** | `sleep` | 16 | 0 | 16 | Attack command / action |
| **E3** | `vnc` | 38 | 14 | 24 | Attack command / action |
| **E3** | `webserv` | 1 | 0 | 1 | Attack command / action |
| **E4** | `shell` | 2 | 2 | 0 | Attack command / action |
| **E4** | `sleep` | 15 | 0 | 15 | Attack command / action |
| **E4** | `sliver` | 2 | 2 | 0 | Attack command / action |
| **E4** | `sliver-session` | 2 | 2 | 0 | Attack command / action |
| **E4** | `ssh` | 24 | 16 | 8 | Attack command / action |
| **E4** | `webserv` | 1 | 0 | 1 | Attack command / action |

## 2. Composite Steps Breakdown

| Episode | Event ID | Step Type | Labeled? | Techniques | Nested Commands | Overlapping Child/Subsequent Steps |
|---|---|---|---|---|---|---|
| **E3** | `E3-S006` | `loop` | True | `T1110.001, T1021.005` | 1 | `E3-S007` (T1021.005)<br>`E3-S009` (T1021.005)<br>`E3-S013` (T1021.005) |
| **E3** | `E3-S068` | `include` | False | `*(None)*` | 0 | None |

## 3. Double-Counting Assessment

Double-Counting Assessment of Composite Steps:
In CAM-LDS, composite container step E3-S006 (type 'loop', cmd 'items(LISTA)') in Episode 3 is labeled with MITRE ATT&CK techniques (['T1110.001', 'T1021.005'] for VNC password guessing). Inspection of its raw parameters shows a loop count of 3 with a single nested template command ('vnc move') iterating over password variable '$LOOP_ITEM'.
The subsequent execution steps (E3-S007, E3-S009, E3-S011, E3-S013 of type 'vnc') are independently recorded top-level lines in attackmate.json with differing commands ('click', 'type', 'key', 'type'), labeled with ['T1021.005']. Whether these subsequent steps represent runtime iterations emitted by the loop execution or are separate sequential log entries in the AttackMate playbook cannot be definitively determined from the log structure alone and is unconfirmed.
Consequence in Sequences:
1. Raw Variant: Technique T1021.005 is represented in E3-S006 and then immediately repeated in individual VNC interaction steps (E3-S007, E3-S009, E3-S013), causing repeated consecutive entries of the same technique.
2. Collapsed Variant: Because E3-S006 carries a multi-technique set {T1021.005, T1110.001} while the subsequent steps carry {T1021.005}, the merge condition (identical consecutive sets) does not merge the container with its subsequent steps. Consequently, the collapsed sequence contains a transition from {T1021.005, T1110.001} -> {T1021.005}.
3. Recommendation: The sequences remain unmodified as specified by protocol to preserve fidelity to raw AttackMate ground truth, but modeling and evaluation must note that transitions out of E3-S006 may reflect composite step container boundaries.