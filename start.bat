@echo off
REM Set the image name
set IMAGE_NAME=my_docker_image

REM Set the container name
set CONTAINER_NAME=my_docker_container

REM Set the host folder to be mounted
set HOST_FOLDER=.\ws

REM Set the folder inside the container where the host folder will be mounted
set CONTAINER_FOLDER=/workspace

REM Remove any existing container with the same name
echo Checking if the container exists...
docker ps -a -q --filter "name=%CONTAINER_NAME%" > nul
if %ERRORLEVEL% == 0 (
    echo Container with name %CONTAINER_NAME% exists. Removing it...
    docker rm -f %CONTAINER_NAME%
)

REM Build the Docker image
echo Building Docker image...
docker build -t %IMAGE_NAME% .

REM Check if the image was successfully built
if %ERRORLEVEL% neq 0 (
    echo Failed to build Docker image.
    exit /b %ERRORLEVEL%
)

REM Run the Docker container interactively with the mounted folder
echo Running Docker container...
docker run -it --rm --name %CONTAINER_NAME% -v %cd%\%HOST_FOLDER%:%CONTAINER_FOLDER% %IMAGE_NAME%

REM Check if the container is running
if %ERRORLEVEL% neq 0 (
    echo Failed to run Docker container.
    exit /b %ERRORLEVEL%
)

echo Docker container is running interactively with the folder mounted at %CONTAINER_FOLDER%.
