import pyautogui
import pydirectinput
import pytesseract
import cv2
import numpy as np
from PIL import Image, ImageDraw
import time

emulatorWindowName = 'Android Emulator - Pixel_4_API_30_2:5554'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
letterPadding = 5
showImage = False
# showImage = True
showIndividualChars = False


# showIndividualChars = True

def print_hi(name):
    # Use a breakpoint in the code line below to debug your script.
    print(f'Hi, {name}')  # Press Ctrl+F8 to toggle the breakpoint.


def take_screenshot():
    myScreenshot = pyautogui.screenshot()
    myScreenshot.save(r'C:\Users\twang\Dropbox\Workspace\AutoWordscapes\screenshots\full_screenshot.png')
    myScreenshot.save(fr"C:\Users\twang\Dropbox\Workspace\AutoWordscapes\screenshots\history\full_screenshot_"
                      fr"{time.strftime('%b %d %H_%M_%S%p')}.png")
    return myScreenshot


def move_window_to_corner():
    emulatorWindow = pyautogui.getWindowsWithTitle(emulatorWindowName)[0]
    emulatorWindow.activate()
    emulatorWindow.moveTo(0, 0)


def show_image(name, image, showSpecific=False):
    if showSpecific:
        cv2.imshow(name, image)
        cv2.waitKey(0)
        return
    global showImage
    if showImage:
        cv2.imshow(name, image)
        cv2.waitKey(0)


def remove_transparency(im, bg_colour=(255, 255, 255)):
    # Only process if image has transparency (http://stackoverflow.com/a/1963146)
    if im.mode in ('RGBA', 'LA') or (im.mode == 'P' and 'transparency' in im.info):

        # Need to convert to RGBA if LA format due to a bug in PIL (http://stackoverflow.com/a/1963146)
        alpha = im.convert('RGBA').split()[-1]

        # Create a new background image of our matt color.
        # Must be RGBA because paste requires both images have the same format
        # (http://stackoverflow.com/a/8720632  and  http://stackoverflow.com/a/9459208)
        bg = Image.new("RGBA", im.size, bg_colour + (255,))
        bg.paste(im, mask=alpha)
        return bg

    else:
        return im


def screenshot_letter_circle(letterBoxX, letterBoxY):
    screenshot = take_screenshot()
    croppedLetterCircle = screenshot.crop(box=[letterBoxX, letterBoxY, 440, 1158])

    # inverse the first image
    # crop like normal

    # crop a circle
    height, width = croppedLetterCircle.size
    lum_img = Image.new('L', [height, width], 0)

    draw_black = ImageDraw.Draw(lum_img)
    draw_black.pieslice([(0, 0), (height, width)], 0, 360,
                        fill=255, outline="white")
    img_arr_normal = np.array(croppedLetterCircle)
    img_arr_inverted = np.invert(np.array(croppedLetterCircle))
    lum_img_arr = np.array(lum_img)

    Image.fromarray(lum_img_arr).save(r'screenshots\lum_img.png', format='png')
    # lum_img_saved = cv2.imread(r'screenshots\lum_img.png')
    # show_image('before', lum_img_saved)

    final_img_arr = np.dstack((img_arr_normal, lum_img_arr))
    final_img_arr_inverted = np.dstack((img_arr_inverted, lum_img_arr))

    removedTransparency = remove_transparency(Image.fromarray(final_img_arr))
    removedTransparencyInverted = remove_transparency(Image.fromarray(final_img_arr_inverted))
    removedTransparency.save(r'screenshots\cropped_letter_circle.png', format='png')
    removedTransparencyInverted.save(r'screenshots\cropped_letter_circle_inverted.png', format='png')

    # loadRemoved = cv2.imread(r'screenshots\cropped_letter_circle.png')
    # show_image('removed', loadRemoved)


def process_ocr(letterElement, psmMode):
    letterElement['letter'] = pytesseract.image_to_string(letterElement['image'],
                                                          lang='eng',
                                                          config=(
                                                              "-c tessedit_char_whitelist"
                                                              "=ABCDEFGHIJKLMNOPQRSTUVWXYZ "
                                                              fr" --psm {psmMode} "
                                                              # Treat the image as a single word.
                                                              # " --psm 8 "
                                                              # Treat the image as a single character.
                                                              # Has trouble with Ps looking like Js
                                                              # " --psm 10 "
                                                              # Raw line. Treat the image as a single
                                                              # text line, bypassing hacks that are
                                                              # Tesseract-specific.
                                                              # " --psm 13 "
                                                              # " -l osd"
                                                          )
                                                          )
    if letterElement['letter'] == '':
        letterElement['letter'] = 'I\n'
    global showIndividualChars
    show_image(f"letter: {letterElement['letter']}", letterElement['image'], showIndividualChars)


def print_time(name, start):
    end = time.time()
    print(f'{name} time: {end - start}')


def get_letters(letterColor='black', psmMode=8, numTries = 1):
    if letterColor == 'black':
        image = cv2.imread(r'screenshots\cropped_letter_circle.png')
    else:
        image = cv2.imread(r'screenshots\cropped_letter_circle_inverted.png')

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    cv2.imwrite(r'screenshots\hsv.png', hsv)

    global showImage

    # show_image('image', image)

    # black letters on light background
    mask = cv2.inRange(hsv, (0, 0, 0), (255, 255, 100))

    onlyLetters = cv2.bitwise_not(mask)

    cv2.imwrite(r'screenshots\onlyLetters.png', onlyLetters)

    image = cv2.imread(r'C:\Users\twang\Dropbox\Workspace\AutoWordscapes\screenshots\onlyLetters.png')

    mask = np.zeros(image.shape, dtype=np.uint8)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    cv2.imwrite(r'screenshots\gray.png', gray)
    show_image('gray', gray)

    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

    # Find contours and filter using aspect ratio and area
    cnts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    cnts = cnts[0] if len(cnts) == 2 else cnts[1]

    individualLetters = {}
    index = 0

    grayCopy = gray.copy()
    global letterPadding

    for c in cnts:
        area = cv2.contourArea(c)
        x, y, w, h = cv2.boundingRect(c)
        ar = w / float(h)
        # if area > 100 and .2 < ar < 1.2:
        if 90 < area < 3000 and h > 40:
            individualLetters[index] = {'coord': {'x': x, 'y': y, 'w': w, 'h': h},
                                        'image': grayCopy[y - letterPadding:y + h + letterPadding,
                                                 x - letterPadding:x + w + letterPadding],
                                        'letter': ''}
            index += 1
            cv2.rectangle(gray, (x - letterPadding, y - letterPadding), (x + w + letterPadding, y + h + letterPadding),
                          (36, 255, 12), 2)
            # cv2.rectangle(mask, (x, y), (x + w, y + h), (255, 255, 255), -1)
            # ROI = original[y:y + h, x:x + w]

    cv2.imwrite(r'screenshots\gray_boxes.png', gray)
    show_image('gray with boxes', gray)

    # Bitwise-and to isolate characters
    result = cv2.bitwise_and(image, mask)
    result[mask == 0] = 255

    # OCR
    for i, val in individualLetters.items():
        try:
            process_ocr(individualLetters[i], psmMode)
        except SystemError as error:
            print(f'Caught SystemError: {error}')

    if len(individualLetters) < 5 and numTries == 1:
        if letterColor == 'black':
            return get_letters(letterColor='white', psmMode=psmMode, numTries=2)
        return get_letters(letterColor='black', psmMode=psmMode, numTries=2)

    return individualLetters


def get_letter_data(letterBoxX, letterBoxY, sameLettersCount, letterColor):
    time.sleep(1)
    screenshot_letter_circle(letterBoxX, letterBoxY)
    psmMode = 8
    if sameLettersCount >= 8 or sameLettersCount == 6:
        print('using psm mode 10')
        psmMode = 10
    return get_letters(letterColor=letterColor, psmMode=psmMode)


def click_all_buttons(retries=1):
    # todo: update piggy bank to look for X
    # piggy bank X button
    pydirectinput.leftClick(425, 358)
    # first screen level button
    pydirectinput.leftClick(269, 695)
    # next button
    pydirectinput.leftClick(280, 900)
    # next button after daily challenge
    pydirectinput.leftClick(267, 981)
    # lose star rush bonus button
    pydirectinput.leftClick(267, 822)
    # star rush compete in under 3 minutes prompt 'got it' button
    pydirectinput.leftClick(267, 574)
    time.sleep(0.5)
    # word definition X button
    if pyautogui.pixel(507, 376) == (76, 102, 127):
        pydirectinput.leftClick(507, 376)
        time.sleep(0.5)
    # # word definition X button
    # pydirectinput.leftClick(478, 382)
    # # click the word definition X button again in case the last click was on a word
    # if retries % 2 == 0:
    #     time.sleep(0.5)
    #     # word definition X button
    #     pydirectinput.leftClick(478, 382)


def android_back_button():
    pydirectinput.keyDown('ctrl')
    pydirectinput.press('backspace')
    pydirectinput.keyUp('ctrl')


def too_many_i(letters):
    countOfIs = 0
    for char in letters:
        if char == 'I':
            countOfIs = countOfIs + 1

    if countOfIs >= 3:
        return True
    return False


def print_letters(lettersToPrint):
    letters = []
    for i, val in lettersToPrint.items():
        if len(lettersToPrint[i]['letter']) == 0:
            continue
        letters.append(lettersToPrint[i]['letter'][0])

    print(f'letters: {letters}')

    return letters
