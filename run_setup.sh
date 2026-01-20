#!/bin/bash

echo "=== Movie Dashboard Complete Analysis ==="

echo "1. Installing dependencies..."
python -m pip install --upgrade pip setuptools wheel
python -m pip install -r requirements.txt

echo "2. Setting up database and importing data..."
python setup_database.py

echo "3. Generating query set..."
python generate_queries.py

echo "4. Starting API server in background..."
python api.py &
API_PID=$!
echo "API server started with PID: $API_PID"
sleep 5

echo "5. Running performance tests..."
python performance_test.py

echo "6. Running JMT analysis..."
python jmt_analysis.py

echo "7. Generating final report..."
python generate_report.py

echo "8. Stopping API server..."
kill $API_PID

echo ""
echo "=== ANALYSIS COMPLETE ==="
echo "Generated files:"
echo "- performance_results.json"
echo "- jmt_analysis.json"
echo "- jmt_analysis.png"
echo "- PERFORMANCE_REPORT.md"
echo ""
echo "To test improved architecture: python improved_architecture.py"