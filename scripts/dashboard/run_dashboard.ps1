param (
    [Parameter(Mandatory=$true)]
    [ValidateSet("prediction", "timeline")]
    [string]$App
)

$env:PYTHONPATH = "src"

if ($App -eq "prediction") {
    Write-Host "Launching Prediction Dashboard on port 8501..."
    python -m streamlit run src\c4\dashboard\prediction_app.py --server.port 8501
} elseif ($App -eq "timeline") {
    Write-Host "Launching Timeline Dashboard on port 8502..."
    python -m streamlit run src\c4\dashboard\app.py --server.port 8502
}
