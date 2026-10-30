@echo off
setlocal
set L=C:\Users\User\lanes\p13run
cd /d %L%
if not exist allmeta git clone -q --filter=blob:none https://github.com/mahmood726-cyber/allmeta.git allmeta > clone.log 2>&1
cd /d %L%\allmeta
git fetch -q --tags origin
for %%R in (v1.7.0 63ce78e5) do call :one %%R
echo ALLDONE > %L%\done.txt
exit /b

:one
set R=%1
cd /d %L%\allmeta
git checkout -q -f %R%
git clean -q -fdx -e hub/shared/tests/node_modules
set O=%L%\out_%R%
if exist %O% rmdir /s /q %O%
mkdir %O%
(
echo ref=%R%
git rev-parse HEAD
git log -1 --format=%%cI
node -v
) > %O%\env.txt
certutil -hashfile gosh\validate\MANIFEST.json SHA256 >> %O%\env.txt
certutil -hashfile gosh\validate\MANIFEST-plus.json SHA256 >> %O%\env.txt
cd /d %L%\allmeta\hub\shared\tests
call npm ci --no-audit --no-fund > %O%\npm.log 2>&1
call npx playwright --version >> %O%\env.txt 2>&1
call npx playwright install chromium > %O%\pwinstall.log 2>&1
set PLAYWRIGHT_JSON_OUTPUT_NAME=%O%\results.json
call npx playwright test validate-gosh.spec.mjs gosh-plus.spec.mjs -g "declared replay preserves|every quantity against pinned R corpus" --workers=1 --reporter=list,json > %O%\run.log 2>&1
echo %ERRORLEVEL% > %O%\exit.txt
if exist %L%\allmeta\integration-evidence xcopy /q /e /i %L%\allmeta\integration-evidence %O%\integration-evidence > nul
exit /b
