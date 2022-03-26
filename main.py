import sys
import threading
import time
import keyboard
import pydirectinput

from capture import *
from solver import *

letterBoxX = 110
letterBoxY = 825
startingTopSpeed = 0.02
topSpeed = startingTopSpeed
pydirectinput.PAUSE = startingTopSpeed
slowestSpeed = 0.08
botRunning = True
# getMousePosition = True
getMousePosition = False

# For expanding the window back to the original location
windowEndX = 556
windowEndY = 1190

def check_bot_running():
    global botRunning
    if keyboard.is_pressed('esc') and botRunning:
        botRunning = False
        print("bot paused")
    time.sleep(0.1) #Check every 10th of a second
    check_bot_running()


def get_mouse_location():
    global getMousePosition
    if getMousePosition:
        time.sleep(3)
        pixel_position = pyautogui.position()
        print(f"mouse position: {pixel_position}, pixel color: {pyautogui.pixel(pixel_position[0], pixel_position[1])}")
        sys.exit()


if __name__ == '__main__':
    print('bot starting')
    # check_thread = threading.Thread(target=check_bot_running)
    # check_thread.start()
    time.sleep(2)

    print('move emulator window to corner')
    move_window_to_corner()

    get_mouse_location()

    oldLetters = ['t']
    sameLettersCount = 0
    retriesBeforeSolveCount = 0

    pydirectinput.PAUSE = topSpeed
    oldLettersSpeed = topSpeed
    letterColor = 'black'

    while botRunning:
        retriesBeforeSolveCount = retriesBeforeSolveCount + 1
        click_all_buttons(retriesBeforeSolveCount)
        if sameLettersCount > 0:
            print(f'sameLettersCount: {sameLettersCount} letterColor: {letterColor}')

        try:
            # print('get letter data')
            letterData = get_letter_data(letterBoxX, letterBoxY, sameLettersCount, letterColor)
        except AttributeError as error:
            print(f'Caught AttributeError: {error}')
            click_all_buttons()
            continue

        letters = print_letters(letterData)

        # Handling odd scenarios with the app =========================================================
        if oldLetters == letters:
            sameLettersCount = sameLettersCount + 1
            topSpeed = oldLettersSpeed
        # stuck in clan screen
        if retriesBeforeSolveCount % 11 == 0:
            print('too many retries, entering android back button')
            android_back_button()
            time.sleep(2)
            continue
        # backgrounds like lavender fields produce lots of Is
        if sameLettersCount > 1 and too_many_i(letters):
            print('too many Is')
            letterColor = 'white'
            continue
        # not enough letters found for a puzzle, must be a different screen
        if len(letterData) < 5:
            print(f'less than 5 letters found, retrying')
            continue
        # too many letters, must be a different screen
        if len(letterData) > 7:
            print('too many letters found, retrying')
            continue

        if oldLetters != letters:
            sameLettersCount = 0
            oldLettersSpeed = topSpeed
        # inputs may be too fast, slow down
        if letters == oldLetters:
            topSpeed = min(topSpeed + 0.02, slowestSpeed)
            oldLettersSpeed = topSpeed
            pydirectinput.PAUSE = topSpeed
            print(f'same letters, slowing down. topSpeed: {topSpeed}')
        # there may be a missing word in the smaller dictionary
        if sameLettersCount < 3:
            # print('generating dictionary')
            dictionary = generate_dictionary()
        else:
            print('puzzle is stuck, generating larger dictionary')
            dictionary = generate_dictionary(True)
        # weird scenarios end =========================================================================

        # print('solving puzzle')
        solve_puzzle(letterData, dictionary, letterBoxX, letterBoxY)
        android_back_button()
        time.sleep(1.5)

        # resetting variables
        retriesBeforeSolveCount = 0
        topSpeed = startingTopSpeed
        pydirectinput.PAUSE = topSpeed
        oldLetters = letters
        letterColor = 'black'

    # check_thread.join()
