import cv2
import numpy as np
import matplotlib.pyplot as plt
import onnxruntime as ort
from yt_dlp import YoutubeDL
import os
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_video_from_url(url, output_path):
    """Télécharge une vidéo YouTube avec yt-dlp."""
    options = {
        'outtmpl': output_path,
        'format': 'bestvideo[ext=mp4]',
        'quiet': False,
        'no_warnings': False,
        'retries': 3,
        'merge_output_format': 'mp4'
    }

    try:
        with YoutubeDL(options) as ydl:
            ydl.download([url])
        logger.info(f"Vidéo téléchargée avec succès : {output_path}")
        return True
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement : {e}")
        return False

def load_onnx_model(model_path):
    """Charge le modèle ONNX."""
    try:
        # Configuration de ONNX Runtime pour optimiser les performances
        options = ort.SessionOptions()
        options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
        
        # Pour GPU si disponible (plus rapide)
        providers = ['CUDAExecutionProvider', 'CPUExecutionProvider'] if 'CUDAExecutionProvider' in ort.get_available_providers() else ['CPUExecutionProvider']
        
        session = ort.InferenceSession(model_path, sess_options=options, providers=providers)
        logger.info("Modèle ONNX chargé avec succès")
        return session
    except Exception as e:
        logger.error(f"Erreur lors du chargement du modèle : {e}")
        raise

def preprocess_frame(frame):
    """Prétraitement des frames pour le modèle."""
    # Utilisation de cv2.resize avec interpolation plus rapide pour la taille fixe
    resized = cv2.resize(frame, (224, 224), interpolation=cv2.INTER_AREA)
    # Normalisation plus efficace
    normalized = resized.astype(np.float32) * (1.0/255.0)
    return np.expand_dims(normalized, axis=0)

def analyze_video(video_path, model_session, max_frames=150):
    """Analyse une vidéo pour détecter la violence."""
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Impossible d'ouvrir la vidéo : {video_path}")

    frame_ids, scores = [], []
    count = 0
    input_name = model_session.get_inputs()[0].name  # Récupéré une seule fois

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret or count >= max_frames:
            break
            
        count += 1
        input_frame = preprocess_frame(frame)
        
        # Prédiction avec ONNX Runtime (plus rapide que Keras)
        pred = model_session.run(None, {input_name: input_frame})[0][0][0]
        
        frame_ids.append(count)
        scores.append(float(pred))

    cap.release()

    if not frame_ids:
        raise ValueError("Aucune frame traitée")

    # Génération du graphique
    plot_path = generate_plot(frame_ids, scores)
    
    # Calcul du score moyen
    average_score = np.mean(scores)
    status = "🟥 Violente" if average_score > 0.5 else "🟩 Non-Violente"
    
    return {
        "average_score": float(average_score),
        "status": status,
        "graph_path": plot_path,
        "frames_analyzed": count
    }

def generate_plot(frame_ids, scores):
    """Génère et sauvegarde le graphique d'analyse."""
    os.makedirs("static", exist_ok=True)
    plot_path = "static/analysis_graph.png"
    
    plt.figure(figsize=(10, 4))
    plt.plot(frame_ids, scores, color='red', label="Score de violence")
    plt.axhline(0.5, linestyle='--', color='green', label="Seuil (0.5)")
    
    # Remplissage conditionnel plus efficace
    scores_arr = np.array(scores)
    plt.fill_between(frame_ids, 0, scores_arr, 
                    where=(scores_arr > 0.5), 
                    color='red', alpha=0.3, interpolate=True)
    plt.fill_between(frame_ids, 0, scores_arr,
                    where=(scores_arr <= 0.5),
                    color='green', alpha=0.3, interpolate=True)
    
    plt.xlabel("Frame")
    plt.ylabel("Score")
    plt.title("🔍 Analyse Vidéo")
    plt.legend()
    plt.tight_layout()
    
    # Sauvegarde optimisée
    plt.savefig(plot_path, dpi=100, bbox_inches='tight', facecolor='white')
    plt.close()
    
    return plot_path

# Exemple d'utilisation
if __name__ == "__main__":
    # Initialisation
    MODEL_PATH = "model/modele_final.onnx"
    VIDEO_URL = input("Veuillez entrer l'URL de la vidéo YouTube : ")
    OUTPUT_PATH = "temp_video.mp4"
    
    try:
        # Chargement du modèle
        model = load_onnx_model(MODEL_PATH)
        
        # Téléchargement de la vidéo
        if download_video_from_url(VIDEO_URL, OUTPUT_PATH):
            # Analyse de la vidéo
            result = analyze_video(OUTPUT_PATH, model)
            print(f"\nRésultats d'analyse :")
            print(f"Score moyen : {result['average_score']:.2f}")
            print(f"Statut : {result['status']}")
            print(f"Graphique généré : {result['graph_path']}")
            print(f"Frames analysées : {result['frames_analyzed']}")
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution : {e}")
    finally:
        # Nettoyage
        if os.path.exists(OUTPUT_PATH):
            os.remove(OUTPUT_PATH)