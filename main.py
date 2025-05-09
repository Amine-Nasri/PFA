from fastapi import FastAPI, Form
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os

from analyze import load_onnx_model, download_video_from_url, analyze_video

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Allow your frontend origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods (GET, POST, etc.)
    allow_headers=["*"],  # Allow all headers
)

# Remove the custom middleware unless it's necessary
# @app.middleware("http")
# async def add_middleware(request, call_next):
#     response = await call_next(request)
#     return response

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Load the model once
model = load_onnx_model("model/modele_final.onnx")

# ... (vos imports existants)

app = FastAPI()

# Configuration CORS élargie
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Pour développement seulement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# ... (le reste de votre code existant)

@app.post("/analyze")
async def analyze(video_url: str = Form(...)):
    video_id = str(uuid.uuid4())
    output_path = f"temp_{video_id}.mp4"
    
    try:
        if not video_url.startswith(('http://', 'https://')):
            return JSONResponse(
                status_code=400,
                content={"error": "URL invalide. Doit commencer par http:// ou https://"}
            )

        if download_video_from_url(video_url, output_path):
            result = analyze_video(output_path, model)
            
            # S'assurer que le graph_path est accessible
            if 'graph_path' in result:
                result['graph_url'] = f"/static/{result['graph_path']}"
                
            return JSONResponse(content=result)
        else:
            return JSONResponse(
                status_code=400,
                content={"error": "Échec du téléchargement de la vidéo"}
            )
            
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": f"Erreur lors de l'analyse: {str(e)}"}
        )
    finally:
        if os.path.exists(output_path):
            os.remove(output_path)