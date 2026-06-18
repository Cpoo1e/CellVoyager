@echo off
setlocal

REM CellVoyager analysis-generation sweep

set "REPEATS=1"
set "ROOT=C:\Users\ckcPo\Documents\Masters\Main_Project"
set "H5AD=C:\Users\ckcPo\Documents\Masters\Main_Project\data\processed\60k_cells_filtered.h5ad"
set "PAPER=C:\Users\ckcPo\Documents\Masters\Main_Project\data\summaries\Basic_Processed_60k.txt"
set "LOGS=C:\Users\ckcPo\Documents\Masters\Main_Project\msc-project\results\logs\Analysis_sweep"
set "ANALYSIS_JSON=C:\Users\ckcPo\Documents\Masters\Main_Project\outputs\Analysis_tests\60kHypothesis_analysis_1_plan.json"
set "output_dir=C:\Users\ckcPo\Documents\Masters\Main_Project\outputs\Analysis_tests"

cd /d "%ROOT%"

REM -------- Local models --------
call :RUN_LOCAL "gemma3:4b" "gemma3_4b"
call :RUN_LOCAL "llama3.1:8b" "llama31_8b"
call :RUN_LOCAL "mistral-nemo:12b" "mistral_nemo_12b"
call :RUN_LOCAL "qwen3:30b-a3b-instruct-2507-q4_K_M" "qwen3_30b_a3b_instruct2507"

REM -------- Cloud models --------
@REM call :RUN_CLOUD "gpt-4o" "gpt4o"
@REM call :RUN_CLOUD "o3-mini" "o3mini"
@REM call :RUN_CLOUD "gpt-5.5" "gpt55"

pause
exit /b


:RUN_LOCAL
set "MODEL=%~1"
set "NAME=%~2"

echo.
echo Loading local model: %MODEL%
ollama run "%MODEL%" "Reply with exactly OK" >nul

for /L %%R in (1,1,%REPEATS%) do (
    echo Running %NAME% repeat %%R...
    python .\CellVoyager\run_cellvoyager.py ^
      --h5ad-path "%H5AD%" ^
      --paper-path "%PAPER%" ^
      --from-analysis-json "%ANALYSIS_JSON%" ^
      --output-dir "%output_dir%" ^
      --analysis-name "%NAME%_r%%R_60k_no_critique" ^
      --model-name "ollama_chat/%MODEL%" ^
      --api-base-url "http://localhost:11434" ^
      --log-home "%LOGS%" ^
      --execution-mode legacy ^
      --no-vlm ^
      --log-prompts ^
      --no-self-critique

)

ollama stop "%MODEL%" >nul
exit /b


:RUN_CLOUD
set "MODEL=%~1"
set "NAME=%~2"

for /L %%R in (1,1,%REPEATS%) do (
    echo Running %NAME% repeat %%R...
    python .\CellVoyager\run_cellvoyager.py ^
      --h5ad-path "%H5AD%" ^
      --paper-path "%PAPER%" ^
      --from-analysis-json "%ANALYSIS_JSON%" ^
      --output-dir "%output_dir%" ^
      --analysis-name "%NAME%_r%%R_60k" ^
      --model-name "%MODEL%" ^
      --log-home "%LOGS%" ^
      --execution-mode legacy ^
      --no-vlm ^
      --log-prompts
)

exit /b
