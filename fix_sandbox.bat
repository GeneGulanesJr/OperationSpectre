@echo off
set "PATH=C:\Program Files\Docker\Docker\resources\bin;%PATH%"
cd /d C:\Users\GeneGulanes\Documents\HealthcareLogic\OperationSpectre
echo === Building and starting sandbox === > C:\Users\GeneGulanes\Documents\HealthcareLogic\OperationSpectre\sandbox_build.log 2>&1
docker compose -f docker-compose.full.yml up -d --build opspectre-sandbox >> C:\Users\GeneGulanes\Documents\HealthcareLogic\OperationSpectre\sandbox_build.log 2>&1
echo === Exit code: %ERRORLEVEL% === >> C:\Users\GeneGulanes\Documents\HealthcareLogic\OperationSpectre\sandbox_build.log 2>&1
