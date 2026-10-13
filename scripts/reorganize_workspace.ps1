$ErrorActionPreference = 'Stop'
$root = (Get-Location).Path
$log = New-Object System.Collections.Generic.List[object]

function Move-Safe($src, $dstDir, $newName) {
    if (-not (Test-Path -LiteralPath $src)) { throw "Missing source: $src" }
    New-Item -ItemType Directory -Force -Path $dstDir | Out-Null
    if (-not $newName) { $newName = Split-Path $src -Leaf }
    $dst = Join-Path $dstDir $newName
    if (Test-Path -LiteralPath $dst) { throw "Destination exists, refusing to overwrite: $dst" }
    Move-Item -LiteralPath $src -Destination $dst
    $log.Add([pscustomobject]@{ old = $src; new = $dst })
}

# ---- C2 ----
$c2 = Join-Path $root 'c2'
$map = [ordered]@{
  '01_task_datasets'  = @('c2_event_classification.csv','c2_next_technique.csv','c2_escalation.csv',
                          'c2_demo_inputs.csv','c2_demo_ground_truth.csv','fused_network_attacks_master.csv',
                          'feature_dictionary.csv','label_dictionary.csv','scenario_manifest.csv',
                          'validation_report.csv','c2_pipeline_reproducible.py')
  '02_network_data'   = @('apt_network_dataset_clean.csv','fused_network_attacks.csv','network_attacks_curated_features.csv',
                          'network_attacks_master.csv','network_c2_lateral_movement.csv','network_connections_sysmon_eid3.csv',
                          'network_discovery_recon.csv','network_dns_activity.csv')
  '03_mordor_data'    = @('mordor_normalized.csv','mordor_benign_audit.csv')
  '04_mitre_reference'= @('mitre_id_crossref.csv','technique_transitions.csv')
  '05_archives'       = @('c2_escalation.zip')
}
foreach ($d in $map.Keys) { foreach ($f in $map[$d]) { Move-Safe (Join-Path $root $f) (Join-Path $c2 $d) $null } }
Move-Safe (Join-Path $root 'README.md') (Join-Path $c2 '00_docs') 'README_c2_dataset.md'

# ---- C4 ----
if (Test-Path -LiteralPath (Join-Path $root 'c4')) { throw 'c4 already exists' }
Move-Item -LiteralPath (Join-Path $root 'c4_forensics') -Destination (Join-Path $root 'c4')
$log.Add([pscustomobject]@{ old = (Join-Path $root 'c4_forensics'); new = (Join-Path $root 'c4') })

$log | Export-Csv -NoTypeInformation -Encoding UTF8 (Join-Path $root 'reorganization_undo_log.csv')
"moved: $($log.Count) items"
