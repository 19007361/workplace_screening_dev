import tensorflow as tf
try:
    from workplace_screening.core.core import ImageAndVideo
except ModuleNotFoundError:
    from core.core import ImageAndVideo
from imutils import resize
import cv2


class FaceMaskDetector(ImageAndVideo):
    """
    Class used to predict the probability of a face
    wearing a face mask. 

    Arguments:
        mask_detect_model {str}:
            Path to the tf lite model that will be used to detect
            the face mask in an image.

    Example of usage:
        face_mask_detector = FaceMaskDetector(mask_detect_model=mask_detect_model)
        face_mask_detector.start_video_stream()
        face_mask_detector.capture_frame_and_detect_facemask()
        face_mask_detector.display_predictions()
    """

    def __init__(self, mask_detect_model):
        super().__init__()
        self.mask_detect_model_location = mask_detect_model
        self.mask_model = tf.lite.Interpreter(model_path=mask_detect_model)
        self.mask_model.allocate_tensors()
        self.input_details = self.mask_model.get_input_details()
        self.output_details = self.mask_model.get_output_details()     

    def detect_facemask(self, mask_probability=0.995, verbose=False):
        """
        This function detects if the various faces in an image is wearing a face mask.
        In order to work, an image must first be loaded with either load_image_from_file
        or load_image_from_frame and then the detect_faces function also need to be run.

        For ease of use, rather implement the capture_frame_and_detect_facemask function.


        Arguments:
            mask_probability {float, default=0.995}:
                Minimum probability required to say mask is identified.
            verbose {boolean, default=False}:
                If true, will print the probability of wearing a mask.
        """

        self.labels = []
        self.colors = []
        
        for face in self.faces:
            
            self.mask_model.set_tensor(self.input_details[0]['index'], face)
            self.mask_model.invoke()
            mask_prob = self.mask_model.get_tensor(self.output_details[0]['index'])
           
            if verbose:
                print('-'*100)
                print(f'Probability of wearing mask: {1-mask_prob[0][0]}')

            label = "Wearing Mask" if (1-mask_prob[0][0]) >= mask_probability else "No Mask"

            color = (0, 102, 0) if "Wearing Mask" in label  else (33, 33, 183)

            print(label)
            self.labels.append(label)
            self.colors.append(color)


            if "Wearing Mask" in label:
                return True

            return False
            
    
    def capture_frame_and_detect_facemask(self, mask_probability=0.995, face_probability=0.9, verbose = False):
        """
        Capture the current frame of the video stream and predict of the 
        people in question are wearing face masks.

        Arguments:
            mask_probability {float, default=0.995}:
                Minimum probability required to say mask is identified.
            face_probability {float, default = 0.9}:
                Minimum probability required to say face is identified.
            verbose {boolean, default=False}:
                If true, will print the probability of wearing a mask. 
        
        Returns:
            Boolean indicating if mask is found or not. True for detection.
        """

        self.capture_frame_and_load_image()
        self.detect_faces(probability=face_probability)
        self.detect_facemask(mask_probability=mask_probability, verbose=verbose)
        self.draw_boxes_around_faces()
        
        for label in self.labels:
            if "Wearing Mask" in label:
                return True

        return False


    def capture_frame_and_detect_facemask_live(self, mask_probability=0.975, face_probability=0.9, verbose = False):
        """
        Start a video stream and show if a mask is detected or not. To stop the video stream
        press Q.

        Arguments:
            mask_probability {float, default=0.995}:
                Minimum probability required to say mask is identified.
            face_probability {float, default = 0.9}:
                Minimum probability required to say face is identified.
            verbose {boolean, default=False}:
                If true, will print the probability of wearing a mask 
        """

        while True:

            # grab the frame from the threaded video stream and resize it to have a maximum width of 400 pixels
            frame = self.vs.read()
            frame = resize(frame, width=400)

            self.load_image_from_frame(frame)
            self.detect_faces(probability=face_probability)
            self.detect_facemask(mask_probability=mask_probability, verbose=verbose)
            self.draw_boxes_around_faces()

            key = cv2.waitKey(1) & 0xFF
            cv2.imshow("Frame", cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB))
            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                break
                
        cv2.destroyAllWindows()    
            
    def clean_up(self):
        """
        Stop video stream.
        """
        self.vs.stop()

    
    def get_labels(self):
        """
        Return the labels generated by prediction.
        """
        return self.labels
