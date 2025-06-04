@echo off
REM Run all tests with coverage and generate reports

echo Cleaning up previous coverage data...
coverage erase

echo Running tests with coverage...
coverage run -m unittest discover tests

echo Generating coverage reports...
coverage report -m
coverage html

echo Done. HTML report is in the htmlcov directory.
