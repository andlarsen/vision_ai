import cv2
import ollama
import base64
import os
import time
import logging
import sys

# --- Configuration & Logging Setup ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("VisionAI")

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = "moondream" 

client = ollama.Client(host=OLLAMA_HOST)

def pull_model_if_needed():
    """Checks if model exists and logs download progress if it doesn't."""
    try:
        logger.info(f"Verifying model '{MODEL}'...")
        models_info = client.list()
        
        # Check if model exists in the list
        exists = any(MODEL in m['model'] for m in models_info.get('models', []))
        
        if not exists:
            logger.info(f"Model '{MODEL}' not found. Starting pull (this may take a minute)...")
            # We use stream=True to get granular feedback during the download
            for progress in client.pull(MODEL, stream=True):
                status = progress.get('status', '')
                if 'total' in progress:
                    completed = progress.get('completed', 0)
                    total = progress.get('total', 1)
                    percent = (completed / total) * 100
                    # Log every 20% to avoid flooding the console
                    if int(percent) % 20 == 0:
                        logger.info(f"Downloading {MODEL}: {percent:.1f}%")
                elif status:
                    logger.info(f"Ollama Status: {status}")
            logger.info("Model download complete.")
        else:
            logger.info(f"Model '{MODEL}' is ready.")
    except Exception as e:
        logger.error(f"Failed to communicate with Ollama: {e}")
        sys.exit(1)

def analyze_frame(frame, prompt="Describe this image in one short sentence."):
    start_time = time.time()
    
    # --- STEP 1: RESIZE FOR CPU SPEED ---
    # Your Intel CPU takes 32s because it's crunching high-res data.
    # Moondream only needs 378x378. Resizing here can save 10-15 seconds!
    small_frame = cv2.resize(frame, (512, 512))
    _, buffer = cv2.imencode('.jpg', small_frame)
    image_b64 = base64.b64encode(buffer).decode()

    logger.info("AI is thinking... (CPU takes ~30s for vision tasks)")
    
    try:
        # --- STEP 2: BLOCKING CHAT ---
        # stream=False is critical to get the full response at once.
        response = client.chat(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt, 'images': [image_b64]}],
            stream=False 
        )
        
        # --- STEP 3: ROBUST DATA EXTRACTION ---
        # Try object access first (SDK v0.2+), fallback to dict (SDK v0.1)
        try:
            content = response.message.content
        except AttributeError:
            content = response.get('message', {}).get('content', "No content found")

        duration = time.time() - start_time
        logger.info(f"DONE! Analysis took {duration:.2f}s")
        
        # --- STEP 4: FORCE LOG OUTPUT ---
        # sys.stdout.flush() ensures the text doesn't sit in the Docker buffer.
        print(f"\nAI SAYS: {content}\n", flush=True)
        return content

    except Exception as e:
        logger.error(f"Inference error: {str(e)}")
        return "Failed to analyze image."

def main():
    pull_model_if_needed()

    # Find the camera
    cap = None
    for i in range(4):
        test = cv2.VideoCapture(i)
        if test.isOpened():
            logger.info(f"Connected to camera device /dev/video{i}")
            cap = test
            break
        test.release()

    if cap is None:
        logger.critical("No video devices found! Check docker-compose device mappings.")
        return

    photos_dir = "/app/photos"
    os.makedirs(photos_dir, exist_ok=True)
    
    logger.info("System Online. Press [SPACE] to analyze, [Q] to quit.")

    while True:
        ret, frame = cap.read()
        if not ret:
            logger.warning("Dropped frame from camera.")
            break

        cv2.imshow("Vision AI Feed", frame)
        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            logger.info("Exiting application...")
            break

        elif key == ord(' '):
            timestamp = int(time.time())
            filename = f"{photos_dir}/capture_{timestamp}.jpg"
            cv2.imwrite(filename, frame)
            
            logger.info(f"Image captured: {filename}")
            
            # Run inference
            result = analyze_frame(frame)
            
            # We use a standard print here just to make the AI's actual answer stand out
            print(f"\nAI RESPONSE: {result}\n")

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()