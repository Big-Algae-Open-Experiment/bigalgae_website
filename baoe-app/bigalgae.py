import random
import string
# Required to send confirmation emails
import smtplib
from email.mime.text import MIMEText
#import piexif
import cv2
import numpy as np

def generate_digit_code(N):
    ''' Returns a random string of digits of length N '''
    return(''.join(random.SystemRandom().choice(string.digits)     \
                   for _ in range(N)))    
    
def generate_validation_key(N):
    ''' Returns a random string of letters and digits of length N '''
    return(''.join(random.SystemRandom().choice(string.uppercase + \
                                                string.lowercase + \
                                                string.digits)     \
                   for _ in range(N)))

def send_email(message, recipient_address):
    me = 'bigalgaeopenexperiment@gmail.com'
    password = get_email_password()
    
    message['From'] = me
    message['To'] = recipient_address
    
    email_server = smtplib.SMTP('smtp.gmail.com:587')
    email_server.ehlo()
    email_server.starttls()
    email_server.login(me, password)
    email_server.sendmail(me, recipient_address, message.as_string())
    email_server.quit()
        
    return(True)
    
def get_email_password():
    with open('/var/www/html/baoe-app/.google_password') as f:
        return(f.readline().strip())

def process_advanced_measurements_string(input_string):
    return_list = []
    for value in input_string.split(','):
        if not value == '':
            return_list.append(float(value))
    return(return_list)

def extract_exif_data(image_filepath):
    try:
        exif_dict = piexif.load(image_filepath)
    except ValueError:
        return({})
    output_dict = {}
    for ifd in exif_dict.keys():
        if ifd in ("0th", "Exif", "GPS", "1st"):
            for tag in exif_dict[ifd]:
                output_dict[piexif.TAGS[ifd][tag]["name"]] = exif_dict[ifd][tag]
    return(output_dict)
        
def within_range(test_value, mid_point, error):
    # A function which tests to see whether the variable mid_point
    # is within an interval defined by test_value - error and
    # test_value + error
    return( (test_value - error) <= mid_point <= (test_value + error) )

def handle_test(contour_idx, contour_list, hierarchy_list, child_area,
    parent_area, grandparent_area, error):
    # Goes through the hierarchy checking whether the contour with
    # index contour_idx has a parent and a grandparent. If so, it tests
    # to see whether the parent's and grandparent's areas are in the
    # correct ratio to be corners
    parent_idx = hierarchy_list[:,contour_idx][0][3]
    # initialize the grandparent_idx at -1. This cleans up the code
    # a little bit as we only need a single else statement
    grandparent_idx = -1
    # if the contour has a parent
    if parent_idx != -1:
        grandparent_idx = hierarchy_list[:,parent_idx][0][3]
        # if the contour has a grandparent
    if grandparent_idx != -1:
        child_contour_area = cv2.contourArea(contour_list[contour_idx])
        parent_contour_area = cv2.contourArea(contour_list[parent_idx])
        grandp_contour_area = cv2.contourArea(contour_list[grandparent_idx])
        return(child_contour_area != 0 and parent_contour_area != 0 and \
               within_range( parent_contour_area / child_contour_area, \
                   parent_area / child_area, error ) and \
               within_range( grandp_contour_area / parent_contour_area, \
                   grandparent_area / parent_area, error))
    else:
        return(False)

def get_corner_handles(contour_list, hierarchy_list, max_error):
    error = 0.0
    matches = 0
    while matches < 3 and error <= max_error:
        matches = 0
        corner_idx = []
        for idx in range(0, len(contour_list)):
            if handle_test(idx, contour_list, hierarchy_list, \
                9.0, 25.0, 49.0, error):
                matches += 1
                
                parent_idx = hierarchy_list[:,idx][0][3]
                grandparent_idx = hierarchy_list[:,parent_idx][0][3]
                corner_idx.append([idx, parent_idx, grandparent_idx])
        error += 0.2

    if matches == 3:
        return(corner_idx)
    else:
        return(None)

def get_centre_of_contour(contour):
    M = cv2.moments(contour)
    cx = int(M['m10']/M['m00'])
    cy = int(M['m01']/M['m00'])
    return((cx, cy))

def sort_corner_handles(corner_list, contour_list):
    '''Takes the corner list, as outputted by get_corner_handles, and returns
    them in a list in the order bottom_left, top_left, top_right. The code does
    not make a distinction between the bottom_left and the top_right as the
    calibration strip is symmetrical about the top left to bottom right
    diagonal'''
    
    corner_centres = [get_centre_of_contour(contour_list[corner[2]]) \
        for corner in corner_list]
    combinations = [[0,1],[0,2],[1,2]]

    distances = [ (corner_centres[i][0]-corner_centres[j][0])**2 + \
                  (corner_centres[i][1]-corner_centres[j][1])**2 \
                  for (i, j) in combinations ]
    comb_idx = 0
    top_left = 2
              
    for idx in range(1, len(distances)):
        if distances[idx] == max(distances):
            if idx == 1:
                comb_idx = 1
                top_left = 1
            elif idx == 2:
                comb_idx = 2
                top_left = 0
    return([corner_list[combinations[comb_idx][0]], \
            corner_list[top_left], \
            corner_list[combinations[comb_idx][1]]])

def get_colour_contours_idx(sorted_corner_list, contour_list):
    corner_centres = [get_centre_of_contour(contour_list[corner[2]]) \
        for corner in sorted_corner_list]

    bottom_left_point = corner_centres[0]
    top_left_point = corner_centres[1]
    top_right_point = corner_centres[2]
    bottom_right_point = [corner_centres[2][0], corner_centres[0][1]]
    
    mean_grandp_area = np.mean(tuple([cv2.contourArea(contour_list[corner[2]]) \
        for corner in sorted_corner_list]))
    
    left_vertical_distance = bottom_left_point[1]-top_left_point[1]
    right_vertical_distance = bottom_right_point[1]-top_right_point[1]
    top_horizontal_distance = top_right_point[0]-top_left_point[0]
    bottom_horizontal_distance = bottom_right_point[0]-bottom_left_point[0]
    
    colour_square_dict = {}
    
    for colour in ['blue', 'green', 'red']:
        test_points = []
        if colour == 'blue':
            test_points.append((bottom_left_point[0], \
                top_left_point[1] + int(0.75*(left_vertical_distance))))
            test_points.append((top_right_point[0], \
                top_right_point[1] + int(0.25*(right_vertical_distance))))
            test_points.append((top_left_point[0] + \
                int(0.75*(top_horizontal_distance)), top_left_point[1]))
            test_points.append((bottom_left_point[0] + \
                int(0.25*(bottom_horizontal_distance)), bottom_left_point[1]))
        elif colour == 'red':
            test_points.append((bottom_left_point[0], \
                top_left_point[1] + int(0.25*(left_vertical_distance))))
            test_points.append((top_right_point[0], \
                top_right_point[1] + int(0.75*(right_vertical_distance))))
            test_points.append((top_left_point[0] + \
                int(0.25*(top_horizontal_distance)), top_left_point[1]))
            test_points.append((bottom_left_point[0] + \
                int(0.75*(bottom_horizontal_distance)), bottom_left_point[1]))
        elif colour == 'green':
            test_points.append((bottom_left_point[0], \
                top_left_point[1] + int(0.5*(left_vertical_distance))))
            test_points.append((top_right_point[0], \
                top_right_point[1] + int(0.5*(right_vertical_distance))))
            test_points.append((top_left_point[0] + \
                int(0.5*(top_horizontal_distance)), top_left_point[1]))
            test_points.append((bottom_left_point[0] + \
                int(0.5*(bottom_horizontal_distance)), bottom_left_point[1]))
    
        error = 100
        matches = 0
        while matches < 4:
            matches = 0
            error += 5
            colour_square_dict[colour] = []
            for idx in range(0, len(contour_list)):
                if within_range(cv2.contourArea(contour_list[idx]), \
                    mean_grandp_area, error):
                    test_results = [cv2.pointPolygonTest(contour_list[idx], \
                        midpoint, False) for midpoint in test_points]
                    if 1 in test_results:
                        matches += 1
                        colour_square_dict[colour].append(idx)
                        
    return(colour_square_dict)

def get_central_window_idx(sorted_corner_list, contour_list):
    corner_centres = [get_centre_of_contour(contour_list[corner[2]]) \
        for corner in sorted_corner_list]
    centre_point = (int((corner_centres[0][0]+corner_centres[2][0])/2),
                    int((corner_centres[0][1]+corner_centres[2][1])/2))
    mean_grandp_area = np.mean(tuple([cv2.contourArea(contour_list[corner[2]]) \
        for corner in sorted_corner_list]))
    central_window_area = (23*((mean_grandp_area**0.5)/7))**2
    error = 500
    match_idx = None
    while match_idx == None:
        error += 50
        for idx in range(0, len(contour_list)):
            if within_range(cv2.contourArea(contour_list[idx]), \
                central_window_area, error) and \
                cv2.pointPolygonTest(contour_list[idx], centre_point, False)==1:
                match_idx = idx
    return(match_idx)

def rect_crop(contour, image, size):
    x, y, cnt_width, cnt_height = cv2.boundingRect(contour)
    y1 = int(y + (cnt_height/size[1]))
    y2 = int(y + (((size[1]-1)*cnt_height)/size[1]))
    x1 = int(x + (cnt_width/size[0]))
    x2 = int(x + (((size[0]-1)*cnt_width)/size[0]))
    roi = image[y1:y2, x1:x2]
    return(roi)
    
def get_time_handles(contour_list, hierarchy_list, max_error):
    error = 0.0
    time_handle_idx = [None, None, None]
    while None in time_handle_idx and error <= max_error:
        time_handle_idx = [None, None, None]
        for idx in range(0, len(contour_list)):
            if handle_test(idx, contour_list, hierarchy_list, \
                1.0, 25.0, 49.0, error):
                parent_idx = hierarchy_list[:,idx][0][3]
                grandparent_idx = hierarchy_list[:,parent_idx][0][3]
                time_handle_idx[0] = [idx, parent_idx, grandparent_idx]
            if handle_test(idx, contour_list, hierarchy_list, \
                1.0, 9.0, 49.0, error):
                parent_idx = hierarchy_list[:,idx][0][3]
                grandparent_idx = hierarchy_list[:,parent_idx][0][3]
                time_handle_idx[1] = [idx, parent_idx, grandparent_idx]
            if handle_test(idx, contour_list, hierarchy_list, \
                1.0, 9.0, 25.0, error):
                parent_idx = hierarchy_list[:,idx][0][3]
                grandparent_idx = hierarchy_list[:,parent_idx][0][3]
                time_handle_idx[2] = [idx, parent_idx, grandparent_idx]
        error += 0.2

    if not None in time_handle_idx:
        return(time_handle_idx)
    else:
        return(None)

def extract_algae_window(contour_list, hierarchy_list, original_image, \
    max_error):
    corners = get_corner_handles(contour_list, hierarchy_list, max_error)
    if corners == None:
        return((1, None, 'No corners detected'))
    corners = sort_corner_handles(corners, contour_list)
    corner_centres = [get_centre_of_contour(contour_list[corner[2]]) \
        for corner in corners]

    distance = max(corner_centres[0][1] - corner_centres[1][1], \
        corner_centres[2][0] - corner_centres[1][0]) 
              
    short_distance = 5.5*(distance/32.0)
    long_distance = 37.5*(distance/32.0)
    total_distance = int(np.ceil(43.0*(distance/32.0)))
    
    model_points = np.array([ [short_distance,long_distance], \
        [short_distance,short_distance], [long_distance,short_distance] ], \
        dtype='float32')
    corner_points = np.array(corner_centres, dtype='float32')
              
    M = cv2.getAffineTransform(corner_points, model_points)
    
    rotated_cropped_img = cv2.warpAffine( np.copy(original_image), M, \
        (total_distance, total_distance) )
    return((0, rotated_cropped_img, 'Success'))

def extract_time_window(contour_list, hierarchy_list, original_image, \
    max_error):
    time_handles = get_time_handles(contour_list, hierarchy_list, max_error)
    if time_handles == None:
        return((1, None, 'No time handle detected'))
    
    time_handle_centres = [get_centre_of_contour(contour_list[handle[2]]) \
        for handle in time_handles]

    distance = abs(time_handle_centres[1][0] - time_handle_centres[0][0])
    one_unit = (distance / (81.5/2.3))
    total_vertical_distance = int(np.ceil(17.0 * one_unit))
    total_horizontal_distance = int(np.ceil((11.0+(81.5/2.3)) * one_unit))
    
    short_horizontal_distance = 5.5 * one_unit
    long_vertical_distance = 12.5 * one_unit
    long_horizontal_distance = (5.5+(81.5/2.3)) * one_unit
    
    model_points = np.array([ [short_horizontal_distance, \
        short_horizontal_distance], [long_horizontal_distance, \
        short_horizontal_distance], [(short_horizontal_distance + \
        long_horizontal_distance) / 2, long_vertical_distance] ], \
        dtype='float32')
    time_handle_points = np.array(time_handle_centres, dtype='float32')
              
    M = cv2.getAffineTransform(time_handle_points, model_points)
    
    rotated_cropped_img = cv2.warpAffine( np.copy(original_image), M, \
        (total_horizontal_distance, total_vertical_distance) )
    return((0, rotated_cropped_img, 'Success'))
    
def threshold_image(original_image, gaussian_blur_kernel_size):
    img_grey = cv2.cvtColor(np.copy(original_image),cv2.COLOR_BGR2GRAY)
    img_grey = cv2.GaussianBlur(img_grey, (gaussian_blur_kernel_size, \
        gaussian_blur_kernel_size), 0)
    retval, thresh_img = cv2.threshold(img_grey, 0, 255, \
        cv2.THRESH_BINARY | cv2.THRESH_OTSU)
    contours, hierarchy = cv2.findContours(np.copy(thresh_img), \
        cv2.RETR_TREE,cv2.CHAIN_APPROX_SIMPLE)
    return((thresh_img, contours, hierarchy))
    
def get_central_time_window_idx(time_handle_list, contour_list):
    time_handle_centres = [get_centre_of_contour(contour_list[handle[2]]) \
        for handle in time_handle_list[0:2]]
    centre_point = (int((time_handle_centres[0][0] + \
        time_handle_centres[1][0])/2), int((time_handle_centres[0][1])/2))
    mean_grandp_area = np.mean(tuple([cv2.contourArea(contour_list[handle[2]]) \
        for handle in time_handle_list[0:2]]))
    central_window_area = 60.1*(mean_grandp_area/16.1)
    error = 500
    match_idx = None
    while match_idx == None:
        error += 50
        for idx in range(0, len(contour_list)):
            if within_range(cv2.contourArea(contour_list[idx]), \
                central_window_area, error) and \
                cv2.pointPolygonTest(contour_list[idx], centre_point, False)==1:
                match_idx = idx
    return(match_idx)
    
def convert_binary(binary_array, start_idx, end_idx):
    return(np.sum(binary_array[start_idx:end_idx] * \
        np.array([2**i for i in reversed(range(end_idx-start_idx))])))

def get_time_and_sensor_information(binary_array):
    days = convert_binary(binary_array, 0, 5)
    hours = convert_binary(binary_array, 5, 10)
    minutes = convert_binary(binary_array, 10, 16)
    light = convert_binary(binary_array, 16, 24)
    return({'days': days, 'hours': hours, 'minutes': minutes, 'light': light})

def extract_time_and_sensor_information(img, contours, hierarchy):
    time_window_img = extract_time_window(contours, hierarchy, img, 5.0)
    if time_window_img[0] != 0:
        return(time_window_img)
    else:
        time_window_img = time_window_img[1]
    thresh_time_img, time_contours, time_hierarchy = threshold_image(time_window_img, 21)
    time_img_grey = cv2.cvtColor(np.copy(time_window_img),cv2.COLOR_BGR2GRAY)
    time_handles = get_time_handles(time_contours, time_hierarchy, 5.0)
    time_idx = get_central_time_window_idx(time_handles, time_contours)
    roi = rect_crop(time_contours[time_idx], time_img_grey, ((60.8/2.3),7))    
    roi_h, roi_w = roi.shape
    cell_w = int(roi_w / 16.0)
    cell_h = int(roi_h / 2.0)
    cell_means = []
    for row_idx in range(2):
        for col_idx in range(16):
            cell = roi[(row_idx*cell_h):((row_idx+1)*cell_h), \
                (col_idx*cell_w):((col_idx+1)*cell_w)]
            cell_means.append(np.mean(cell))
    cell_means = np.array(cell_means[0:24])
    normalized_cell_means = (255 * (cell_means-min(cell_means))) / \
        (max(cell_means)-min(cell_means))
    binary = np.array([int(150 < mean) for mean in normalized_cell_means])
    time_information = get_time_and_sensor_information(binary)
    return((0, time_information, 'Finished'))

def analyse_image(image_filepath):
    img = cv2.imread(image_filepath, cv2.CV_LOAD_IMAGE_COLOR)
    width, height, channels = img.shape
    thresh_img, contours, hierarchy = threshold_image(img, 21)
    algae_window_img = extract_algae_window(contours, hierarchy, img, 5.0)
    if algae_window_img[0] != 0:
        return(algae_window_img)
    else:
        print('Yep!')
        algae_window_img = algae_window_img[1]
              
            
    time_and_sensor = extract_time_and_sensor_information(img, contours, hierarchy)
    
    print(time_and_sensor)
              
    return((0, None, 'Finished'))
