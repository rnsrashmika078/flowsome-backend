
- **`python -m venv fastapi-env`**  
  Creates a virtual environment named `fastapi-env`

- **`Scripts\activate.bat`**  
  Activates the virtual environment (you’re now “inside” it)

- **`pip install fastapi`**  
  Installs the FastAPI framework inside the venv

- **`pip install uvicorn`**  
  Installs Uvicorn, the ASGI server to run FastAPI apps

- **`uvicorn main:app --reload`**  
  Runs the FastAPI application with auto-reload enabled
  
- **`pip install -r requirements.txt`**  
  Install dependencies 


- **`Swagger ui**

api/route/route.py

api -> package
route -> sub-package
route.py -> module