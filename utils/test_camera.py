import cv2
import os

folder_location = "photos"  # Change this to your desired folder location

def ensure_folder_exists(folder):
    if not os.path.exists(folder):
        os.makedirs(folder)

def list_cameras():
    index = 0
    arr = []
    while True:
        cap = cv2.VideoCapture(index)
        if not cap.read()[0]:
            break
        else:
            arr.append(index)
        cap.release()
        index += 1
    return arr

def choose_camera():
    cameras = list_cameras()
    if not cameras:
        print("No cameras found.")
        return None

    print("Available cameras:")
    for idx in cameras:
        print(f"  {idx}")

    while True:
        choice = input("Enter the camera index to use (or 'q' to quit): ")
        if choice.lower() == 'q':
            return None
        if choice.isdigit() and int(choice) in cameras:
            return int(choice)
        print("Invalid choice. Please try again.")

def main():
    camera_index = choose_camera()
    if camera_index is None:
        return

    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print("Error: Could not open webcam.")
        print("Try running: ls /dev/video* to check available cameras")
        return

    print("Controls:")
    print("  SPACE - take a picture")
    print("  Q     - quit")

    photos = []

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Failed to grab frame")
            break

        # Show live preview
        cv2.imshow("Webcam - Press SPACE to capture, Q to quit", frame)

        key = cv2.waitKey(1) & 0xFF

        if key == ord('q'):
            break

        elif key == ord(' '):
            photos.append(frame.copy())
            filename = f"photo_{len(photos)}.jpg"
            ensure_folder_exists(folder_location)
            cv2.imwrite(f"{folder_location}/{filename}", frame)
            print(f"Saved {filename}")

            # Show the captured photo in a separate window
            cv2.imshow(f"Captured photo {len(photos)}", frame)

    cap.release()
    cv2.destroyAllWindows()
    print(f"\nDone. {len(photos)} photo(s) taken.")

if __name__ == "__main__":
    main()