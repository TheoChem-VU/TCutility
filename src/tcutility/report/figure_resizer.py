'''
This module is used for resizing pictures containing molecules.
'''
import numpy as np
import cv2
import matplotlib.pyplot as plt
import os
from typing import Optional, Dict, Union


def _analyse_img(file, plot=False):
    '''
    Function used for analysing and getting useful information from an image.
    This includes circle locations and sizes.
    '''
    # Read image
    img = cv2.imread(file, cv2.IMREAD_UNCHANGED)
    img = _remove_padding(img)
    # Smooth it
    img_copy = img.copy()

    # Convert to greyscale
    img_gray = cv2.medianBlur(img_copy, 3)
    img_gray = cv2.cvtColor(img_gray, cv2.COLOR_BGRA2GRAY)

    # Apply Hough transform to greyscale image
    circles = cv2.HoughCircles(img_gray, cv2.HOUGH_GRADIENT, 1, 100,
                               param1=60, param2=40, minRadius=0, maxRadius=200)
    circles = np.uint16(np.around(circles))[0]
    circles = circles[(-circles[:, 2]).argsort()]

    if plot:
        img_copy = cv2.cvtColor(img_copy, cv2.COLOR_BGR2RGB)
        for i, circle in enumerate(circles):
            # draw the outer circle
            cv2.circle(img_copy,(circle[0],circle[1]),circle[2],(0,255,0),2)
            # draw the center of the circle
            cv2.circle(img_copy,(circle[0],circle[1]),2,(0,0,255),3)
            cv2.putText(img_copy, str(i), (circle[0] - 40, circle[1] + 44), cv2.FONT_HERSHEY_SIMPLEX, 4, (0, 0, 0), 16, cv2.LINE_AA)
            cv2.putText(img_copy, str(i), (circle[0] - 40, circle[1] + 44), cv2.FONT_HERSHEY_SIMPLEX, 4, (255, 255, 255), 8, cv2.LINE_AA)

        plt.imshow(img_copy)
        plt.draw()
        plt.pause(0.001)
    return circles, img


def _remove_padding(img):
    '''
    Function used to remove padding from an image.
    '''
    gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)
    gray = 255*(gray < 240).astype(np.uint8) # To invert the text to white
    coords = cv2.findNonZero(gray) # Find all non-zero points (text)
    x, y, w, h = cv2.boundingRect(coords) # Find minimum spanning bounding box
    rect = img[y:y+h, x:x+w] # Crop the image - note we do this on the original image
    return rect


def resize(d, circle_numbers: Optional[Dict] = None, padding: Union[str, int | float] = 0):
    '''
    The main function for this module.
    Takes a directory `d` and selected circles and resizes and moves images in order to produce new aligned images.

    Args:
        d: the directory to take images from.
        circle_numbers: a dictionary containing the image names as keys and circle indices as the values.
            The new images will be aligned based on these selected circles.
        padding: the amount of padding to add to the new images.
            If given an integer, it adds `padding` number of pixels.
            Alternatively a string consisting of a number and a `%` sign can be given to add relative padding.
            E.g. `padding='10%'` will add a 10% padding to the images.
    '''
    circles = {}
    imgs = {}
    for file in os.listdir(d):
        if file == '.DS_Store':
            continue
        if file not in circle_numbers:
            continue
        circles_, img_ = _analyse_img(os.path.join(d, file))
        circles[file] = circles_[circle_numbers[file]]
        imgs[file] = img_

    # get the atom sizes, which is simply the radius of the circle we selected
    atom_sizes = {file: circle[2] for file, circle in circles.items()}
    # calculate ratios for resizing the images
    ratios = {file: max(atom_sizes.values())/size for file, size in atom_sizes.items()}
    # resize old images to make new ones
    imgs = {file: cv2.resize(img, [int(round(img.shape[1] * ratios[file])), int(round(img.shape[0] * ratios[file]))]) for file, img in imgs.items()}
    # also resize circles to match the new ratio
    circles = {file: circle * ratios[file] for file, circle in circles.items()}

    # now find out where to place the circles
    circle_x = [circle[0] for circle in circles.values()]
    circle_y = [circle[1] for file, circle in circles.items()]

    pad_left = {file: int((max(circle_x) - circle[0])) for file, circle in circles.items()}
    pad_top = {file: int((max(circle_y) - circle[1])) for file, circle in circles.items()}

    pad = {file: [(pad_top[file], 0), (pad_left[file], 0), (0, 0)] for file in imgs}
    imgs = {file: np.pad(img, pad[file], constant_values=0) for file, img in imgs.items()}

    imsize_x = [img.shape[1] for img in imgs.values()]
    imsize_y = [img.shape[0] for img in imgs.values()]

    pad_right = {file: int(max(imsize_x) - img.shape[1]) for file, img in imgs.items()}
    pad_bottom = {file: int(max(imsize_y) - img.shape[0]) for file, img in imgs.items()}

    pad = {file: [(0, pad_bottom[file]), (0, pad_right[file]), (0, 0)] for file in imgs}
    imgs = {file: np.pad(img, pad[file], constant_values=0) for file, img in imgs.items()}

    # add final padding
    if isinstance(padding, str) and padding.endswith('%'):
        padding = float(padding.removesuffix('%'))/100
        padding = int(padding * list(imgs.values())[0].shape[1]), int(padding * list(imgs.values())[0].shape[0])
    else:
        padding = int(padding), int(padding)

    pad = {file: [(padding[0], padding[0]), (padding[1], padding[1]), (0, 0)] for file in imgs}
    imgs = {file: np.pad(img, pad[file], constant_values=0) for file, img in imgs.items()}

    os.makedirs(d + '_fixed', exist_ok=True)
    for file, img in imgs.items():
        cv2.imwrite(os.path.join(d + '_fixed', file), img)

    cv2.imwrite(os.path.join(d + '_fixed', 'empty.png'), np.zeros_like(img) + np.array([255, 255, 255, 0]))
    ret = {file: os.path.join(d + '_fixed', file) for file in imgs}
    ret['empty.png'] = os.path.join(d + '_fixed', 'empty.png')
    return ret
