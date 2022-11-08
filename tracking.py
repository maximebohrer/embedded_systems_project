import cv2
import numpy as np
import socket
import struct

# Create and connect socket
HOST = "10.100.249.80"  # The server's hostname or IP address
PORT = 4747  # The port used by the server
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))

def send_angle(angle):
    ba = bytearray(struct.pack("f", angle))
    s.sendall(ba)

cap = cv2.VideoCapture(0)
template, h, w, h_frame, w_frame = None, 0, 0, 0, 0

def selection_template():
    global template, h, w, h_frame, w_frame
    ret, frame = cap.read()
    #frame      = cv2.rotate(frame, cv2.ROTATE_180)
    frame      = cv2.flip(frame, 1)
    r = cv2.selectROI('Selectionnez le template', frame)
    cv2.destroyWindow('Selectionnez le template')
    template = frame[int(r[1]) : int(r[1] + r[3]), int(r[0]) : int(r[0] + r[2])]
    h, w, _ = template.shape
    h_frame, w_frame, _ = frame.shape

# Select template on 1st frame
selection_template()

delta                = 50    # Defined to look around the place where the template was found
sensibiliy                 = 0.6   # Sensibility of cv2.matchTemplate
everywhere           = True  # To search the template everywhere on the frame
current_x, current_y = 0, 0  # Global x, y coordinate of the top left point of template found
v_x, v_y             = 0, 0  # Speed along x, y of the template
a_x, a_y             = 0, 0  # Acceleration along x, y of the template
azimuth, elevation   = 0, 0  # Horizontal, vertical angle that the object makes with the center of the image

while True:
    ret, frame = cap.read()
    #frame      = cv2.rotate(frame, cv2.ROTATE_180)
    frame      = cv2.flip(frame, 1) # Flip the frame along vertical axis

    if not everywhere:
        # Prediction of the next position according to last position, speed and acceleration
        # Note that the prediction in position concerns the top left point of the template
        predict_v_x = v_x + a_x
        predict_v_y = v_y + a_y
        predict_x   = current_x + predict_v_x
        predict_y   = current_y + predict_v_y

        # Computation of the reduced searching area around prediction
        x_tl_search = min(max(predict_x - delta, 0), w_frame - w - 2 * delta) # Top left point
        y_tl_search = min(max(predict_y - delta, 0), h_frame - h - 2 * delta)
        x_br_search = max(min(predict_x + w + delta, w_frame), w + 2 * delta) # Bottom right point
        y_br_search = max(min(predict_y + h + delta, h_frame), h + 2 * delta) 

        #    ┌──────────────────────────────────────────────────────────┐
        #    │                           Full frame ↑                   │
        #    │                                                          │
        #    │          ┌────────────────┐                              │  Explanation for x_tl_search reminding that the searching area dimension is w + 2 * delta
        #    │          │     ↕ delta    │                    h_frame ↑ │  along x and h + 2 * delta along y:
        #    │          │   ┌────────┐   │                            ↓ │   - To avoid going in negative x area, we take the max between 0 and the starting point of
        #    │          │   │ temp-  │↑  │                              │     the new searching area
        #    │          │   │ late   │↓  │                              │   - To avoid going after the end of the frame, we take the min between the previous filter 
        #    │          │   │        │h  │                              │     and the last acceptable position for the searching zone
        #    │          │   └────────┘   │                              │  Explanations are the same for the other variables.
        #    │          │      ←→ w      │                              │
        #    │          └────────────────┘                              │
        #    │             ↑  Reduced search area                       │
        #    │                                                          │
        #    │                                                          │
        #    │                                ←→ w_frame                │
        #    └──────────────────────────────────────────────────────────┘
        
        # Search of template in new area
        search_area = frame[y_tl_search : y_br_search, x_tl_search : x_br_search, :]
        res         = cv2.matchTemplate(search_area, template, cv2.TM_CCOEFF_NORMED)
        pt          = np.unravel_index(res.argmax(), res.shape) # Top left point of the greatest match between template and search area

        if res[pt] > sensibiliy: # If template found
            last_x    = current_x
            last_y    = current_y
            current_x = pt[1] + x_tl_search # Adding back the offset comming from the reduced search area
            current_y = pt[0] + y_tl_search
            
            # Azimuth and elevation of template found
            azimuth   = - np.arctan(0.601 * (current_x + w / 2 - w_frame / 2) / (w_frame / 2)) # 0.601 is such that arctan(0.601) = half of horizontal camera viewing angle ~= 31° 
            elevation = - np.arctan(0.451 * (current_y + h / 2 - h_frame / 2) / (h_frame / 2)) # 0.451 is such that arctan(0.451) = half of vertical camera viewing angle ~= 24° 
            send_angle(azimuth)
            print(f"azimuth = {azimuth}     elevation = {elevation}")

            # Upgrade template
            template = (frame[current_y : current_y + h, current_x : current_x + w, :]).copy()

            # Print new template in yellow
            cv2.rectangle(frame, (current_x, current_y), (current_x + w, current_y + h), (0, 255, 255), 2)

            # Speed and acceleration
            last_v_x = v_x
            last_v_y = v_y
            v_x      = current_x - last_x
            v_y      = current_y - last_y
            a_x      = v_x - last_v_x
            a_y      = v_y - last_v_y
        else:
            everywhere = True
            
            # Reset angles
            azimuth, elevation = 0, 0
            send_angle(azimuth)
        
        # Print search area in blue
        cv2.rectangle(frame, (x_tl_search, y_tl_search), (x_br_search, y_br_search), (255, 0, 0), 2)
    
    else:
        # Search template in global frame
        res = cv2.matchTemplate(frame, template, cv2.TM_CCOEFF_NORMED)
        pt  = np.unravel_index(res.argmax(), res.shape)

        if res[pt] > sensibiliy: # If template found
            current_x = pt[1]
            current_y = pt[0]

            # Upgrade template
            template = (frame[current_y : current_y + h, current_x : current_x + w, :]).copy()

            # Print new template in yellow
            cv2.rectangle(frame, (current_x, current_y), (current_x + w, current_y + h), (0, 255, 255), 2)
            
            everywhere = False
            v_x, v_y   = 0, 0
            a_x, a_y   = 0, 0
    
    cv2.imshow('Input', frame)
    cv2.imshow('Template', template)

    key = cv2.waitKey(25)
    if key & 0xFF == ord('q'): # Press q to quit the program
        break
    elif key & 0xFF == ord('s'): # Press s to set a new template
        selection_template()

cap.release()
cv2.destroyAllWindows()
s.close()