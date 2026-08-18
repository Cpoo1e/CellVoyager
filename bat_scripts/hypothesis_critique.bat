@echo off
setlocal

REM CellVoyager self-critique ablation sweep
REM All runs use the same unprocessed dataset and prompt.
REM Self-critique is enabled by default; --no-self-critique disables it.

set "REPEATS=3"
set "ROOT=C:\Users\ckcPo\Documents\Masters\Main_Project"
set "H5AD=C:\Users\ckcPo\Documents\Masters\Main_Project\data\processed\unprocessed.h5ad"
set "PAPER=C:\Users\ckcPo\Documents\Masters\Main_Project\data\summaries\Basic_Unprocessed.txt"
set "RUN_HOME=C:\Users\ckcPo\Documents\Masters\Main_Project\report_results\Hypothesis_Tests\critique"

cd /d "%ROOT%" || (
    echo ERROR: Could not open %ROOT%
    pause
    exit /b 1
)

REM -------- Local models --------
call :RUN_LOCAL_MODEL "gemma3:4b" "gemma3_4b"
call :RUN_LOCAL_MODEL "llama3.1:8b" "llama31_8b"
call :RUN_LOCAL_MODEL "mistral-nemo:12b" "mistral_nemo_12b"
call :RUN_LOCAL_MODEL "qwen3:30b-a3b-instruct-2507-q4_K_M" "qwen3_30b_a3b_instruct2507"

REM -------- Optional cloud models --------
REM Remove REM from any models you want to include.
REM call :RUN_CLOUD_MODEL "gpt-4o" "gpt4o"
REM call :RUN_CLOUD_MODEL "o3-mini" "o3mini"
REM call :RUN_CLOUD_MODEL "gpt-5.5" "gpt55"

echo.
echo Self-critique sweep complete.
pause
exit /b


:RUN_LOCAL_MODEL
set "OLLAMA_MODEL=%~1"
set "MODEL_NAME=ollama_chat/%~1"
set "NAME=%~2"
set "PROVIDER_ARGS=--api-base-url http://localhost:11434 --local-llm"

echo.
echo Loading local model: %OLLAMA_MODEL%
ollama run "%OLLAMA_MODEL%" "Reply with exactly OK" >nul

if errorlevel 1 (
    echo ERROR: Could not load %OLLAMA_MODEL%. Skipping this model.
    exit /b
)

call :RUN_BOTH_CONDITIONS

ollama stop "%OLLAMA_MODEL%" >nul
exit /b


:RUN_CLOUD_MODEL
set "MODEL_NAME=%~1"
set "NAME=%~2"
set "PROVIDER_ARGS="

call :RUN_BOTH_CONDITIONS
exit /b


:RUN_BOTH_CONDITIONS
for /L %%R in (1,1,%REPEATS%) do (
    call :RUN_ONE "SELF_CRITIQUE" "" %%R
    call :RUN_ONE "NO_SELF_CRITIQUE" "--no-self-critique" %%R
)
exit /b


:RUN_ONE
set "CONDITION=%~1"
set "CRITIQUE_FLAG=%~2"
set "REPEAT=%~3"
set "ANALYSIS_NAME=%NAME%_r%REPEAT%_UNPROCESSED_%CONDITION%"

echo.
echo Running %ANALYSIS_NAME%...

python .\CellVoyager\run_cellvoyager.py %CRITIQUE_FLAG% %PROVIDER_ARGS% ^
  --h5ad-path "%H5AD%" ^
  --paper-path "%PAPER%" ^
  --analysis-name "%ANALYSIS_NAME%" ^
  --model-name "%MODEL_NAME%" ^
  --log-home "%RUN_HOME%" ^
  --api-base-url "http://localhost:11434" ^
  --log-prompts ^
  --execution-mode legacy ^
  --hypothesis-debug ^
  --output-dir "%RUN_HOME%\plans\%ANALYSIS_NAME%"

if errorlevel 1 (
    echo WARNING: %ANALYSIS_NAME% failed. Continuing with the sweep.
)

exit /b
