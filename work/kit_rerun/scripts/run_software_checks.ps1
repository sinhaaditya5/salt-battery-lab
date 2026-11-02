$ErrorActionPreference = 'Stop'
Set-Location (Join-Path $PSScriptRoot '..')

Write-Host '1/5 Python syntax check'
py -3 -m py_compile simulation/*.py economics/*.py

Write-Host '2/5 Literature-quantity arithmetic check'
py -3 simulation/cell_sizing_calculator.py --cells 3

Write-Host '3/5 Cycler analyser smoke test (synthetic fixture only)'
py -3 simulation/analyze_cycler_csv.py simulation/demo_synthetic_data.csv --positive-active-mg 5 --negative-active-mg 5 --out-dir simulation/demo_analysis_output

Write-Host '4/5 Equivalent-circuit smoke test (synthetic fixture only)'
py -3 simulation/equivalent_circuit_model.py simulation/rc_model_demo_synthetic_parameters.json simulation/current_profile_demo_synthetic.csv --output simulation/rc_demo_synthetic_output.csv

Write-Host '5/5 Moonshot arithmetic check'
py -3 simulation/moonshot_requirements.py --range-km 1500 --charge-minutes 5 --consumption-low 15 --consumption-high 20 --cell-whkg 875

Write-Host 'Cost-model guard check (expected to refuse incomplete inputs)'
$costOutput = & py -3 economics/cost_model.py economics/cost_inputs_template.json 2>&1
$costExit = $LASTEXITCODE
if ($costExit -eq 0) { throw 'Cost model unexpectedly ran with incomplete inputs.' }
if (($costOutput | Out-String) -notmatch 'Cost model not run: enter actual values') {
    throw 'Cost model exited unsuccessfully for an unexpected reason.'
}
Write-Host 'PASS: cost model correctly refuses to invent unit economics.'

Write-Host 'PASS: software smoke tests completed.'
Write-Host 'NOTE: demo cycler/current/RC inputs are synthetic. No battery chemistry, cell performance or safety was tested.'
