import numpy as np
import cv2 as cv

def main():
    img = cv.imread('baboon.png')
    if img is None:
        print("Image not found or unable to open!")
        return
    
    cv.imshow("cong", img)

    while True:
        # Wait for a key press or window close
        key = cv.waitKey(1)
        
        # Exit the loop if the window is closed or the user presses 'q'
        if cv.getWindowProperty("cong", cv.WND_PROP_VISIBLE) < 1:
            break
        if key == ord('q'):  # Exit if 'q' is pressed
            break

    cv.destroyAllWindows()

if __name__ == "__main__":
    main()

