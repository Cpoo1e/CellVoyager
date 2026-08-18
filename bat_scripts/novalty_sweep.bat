@echo off
setlocal

set "REPEATS=3"
set "ROOT=C:\Users\ckcPo\Documents\Masters\Main_Project"
set "OUTPUT_ROOT=%ROOT%\report_results\Novelty"
set "LOG_ROOT=%OUTPUT_ROOT%"

cd /d "%ROOT%"

REM ============================================================
REM Run the three datasets
REM ============================================================

call :RUN_DATASET ^
    "RA" ^
    "%ROOT%\outputs\Analysis_tests\Data_Summary\E-MTAB-8322.project.h5ad" ^
    "C:\Users\ckcPo\Documents\Masters\Main_Project\report_results\Novelty\summaries\RA-summary-noval.txt"

call :RUN_DATASET ^
    "ME_CFS" ^
    "%ROOT%\outputs\Analysis_tests\Data_Summary\unprocessed.h5ad" ^
    "C:\Users\ckcPo\Documents\Masters\Main_Project\report_results\Novelty\summaries\ME.CFS-summary-noval.txt"

call :RUN_DATASET ^
    "Kang_IFNB" ^
    "%ROOT%\outputs\Analysis_tests\Data_Summary\kang_normalized_hvg.h5ad" ^
    "C:\Users\ckcPo\Documents\Masters\Main_Project\report_results\Novelty\summaries\Kang-summary-noval.txt"



echo.
echo All runs complete.
pause
exit /b


REM ============================================================
REM Run the four configurations for one dataset
REM ============================================================

:RUN_DATASET
set "DATASET=%~1"
set "H5AD=%~2"
set "PAPER=%~3"

echo.
echo ============================================================
echo Running dataset: %DATASET%
echo ============================================================

call :RUN_CONFIG ^
    "original" ^
    "anthropic/claude-haiku-4-5-20251001" ^
    "claude-haiku-4-5-20251001" ^
    "original_haiku"

call :RUN_CONFIG ^
    "original" ^
    "anthropic/claude-sonnet-4-6" ^
    "claude-sonnet-4-6" ^
    "original_sonnet"

call :RUN_CONFIG ^
    "original" ^
    "anthropic/claude-opus-4-8" ^
    "claude-opus-4-8" ^
    "original_opus"

call :RUN_CONFIG ^
    "multi" ^
    "anthropic/claude-opus-4-8" ^
    "claude-haiku-4-5-20251001" ^
    "multi_opus_haiku"

exit /b


REM ============================================================
REM Run one configuration three times
REM ============================================================

:RUN_CONFIG
set "PIPELINE=%~1"
set "MODEL=%~2"
set "EXECUTION_MODEL=%~3"
set "CONFIG=%~4"

if "%PIPELINE%"=="original" (
    set "RUNNER=.\Original_CellVoyager\CellVoyager\run_cellvoyager.py"
) else (
    set "RUNNER=.\CellVoyager\run_cellvoyager.py"
)

for /L %%R in (1,1,%REPEATS%) do (
    echo.
    echo Running %DATASET% - %CONFIG% - repeat %%R

    python "%RUNNER%" ^
      --h5ad-path "%H5AD%" ^
      --paper-path "%PAPER%" ^
      --output-dir "%OUTPUT_ROOT%" ^
      --analysis-name "%DATASET%_%CONFIG%_r%%R" ^
      --execution-mode claude ^
      --model-name "%MODEL%" ^
      --execution-model "%EXECUTION_MODEL%" ^
      --log-home "%LOG_ROOT%" ^
      --stop-jupyter-on-complete
)

exit /b