install:

pip install fastapi
pip install "uvicorn[standard]"
run server:

uvicorn main:app --reload
run tests:

pytest test_app.py
