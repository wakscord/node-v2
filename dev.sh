source venv/bin/activate

export PYTHONPATH='.'
celery -A app.main.worker worker --loglevel=info --pool=gevent --concurrency=1000 && python app/main.py