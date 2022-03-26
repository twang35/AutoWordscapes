import time

import pyautogui
import pydirectinput
import copy
from pywinauto import Application


lastLetters = []


def get_midpoint(coord, letterBoxX, letterBoxY):
    return {'x': round(letterBoxX + coord['x'] + coord['w']/2),
            'y': round(letterBoxY + coord['y'] + coord['h']/2)}


def move_to(coord, letterBoxX, letterBoxY):
    midpoint = get_midpoint(coord, letterBoxX, letterBoxY)
    pydirectinput.moveTo(midpoint['x'], midpoint['y'])
    # time.sleep(0.2)


def input_word(word, letters, letterBoxX, letterBoxY):
    # letters = {'S': [{'x': 206, 'y': 217, 'w': 38, 'h': 59}],
    #            'H': [{'x': 79, 'y': 217, 'w': 46, 'h': 59}, {'x': 123, 'y': 456, 'w': 46, 'h': 59}],
    #            'E': [{'x': 243, 'y': 101, 'w': 40, 'h': 58}]}
    tempLetters = copy.deepcopy(letters)
    firstLetterMidpoint = get_midpoint(tempLetters[word[0]][0], letterBoxX, letterBoxY)
    pydirectinput.moveTo(firstLetterMidpoint['x'], firstLetterMidpoint['y'])
    pydirectinput.mouseDown()

    for i in word:
        # print(f"moving to {i}")
        move_to(tempLetters[i].pop(0), letterBoxX, letterBoxY)

    pydirectinput.mouseUp()


def user_input(letters, letterBoxX, letterBoxY):
    app = Application().connect(title_re="AutoWordscapes.*")
    app_dialog = app.top_window()
    app_dialog.set_focus()

    word = input("Enter word: ")

    while word != "":
        input_word(word.upper(), letters, letterBoxX, letterBoxY)
        app_dialog.set_focus()
        word = input("Enter word: ")


def puzzle_finished():
    # pixel is back button in upper left that disappears when puzzle is finished
    if pyautogui.pixel(37, 152) != (255, 255, 255):
        return True


def solve_puzzle(letters, dictionary, letterBoxX, letterBoxY):
    # letters[index] = {'coord': {'x': x, 'y': y, 'w': w, 'h': h},
    #                   'image': image[y - 5:y + h + 5, x - 5:x + w + 5],
    #                   'letter': 'x'}
    useableLetters = []
    letterPositions = {}
    for i, val in letters.items():
        # print(f"i: {i} letter: {letters[i]['letter']}")
        if len(letters[i]['letter']) == 0:
            continue
        letter = letters[i]['letter'][0]
        useableLetters.append(letter)
        if letter in letterPositions:
            letterPositions[letter].append(letters[i]['coord'])
        else:
            letterPositions[letter] = [letters[i]['coord']]

    # user_input(letterPositions, letterBoxX, letterBoxY)

    foundWords = generate_all_possible_words(useableLetters, dictionary)
    totalWords = 0

    for i in range(7, 2, -1):
        wordsToInput = foundWords[i]
        for word in wordsToInput:
            if puzzle_finished():
                return
            totalWords = totalWords + 1
            input_word(word, letterPositions, letterBoxX, letterBoxY)


def generate_dictionary(useLargerDict = False):
    dictionary = set()
    wordListFile = open('wordlist.txt', 'r')

    for word in wordListFile:
        dictionary.add(word.rstrip().upper())

    if useLargerDict:
        largerWordlist = open('wordlistBigger.txt', 'r')
        for word in largerWordlist:
            dictionary.add(word.rstrip().upper())

    return dictionary


def generate_all_possible_words(letters, dictionary):
    foundWords = {3: [], 4: [], 5: [], 6: [], 7: []}

    generate_words_recur("", letters.copy(), dictionary, foundWords)

    return foundWords


def generate_words_recur(currentWord, remainingLetters, dictionary, foundWords):
    if len(remainingLetters) == 0:
        return

    for char in remainingLetters:
        remainingLettersCopy = remainingLetters.copy()
        remainingLettersCopy.remove(char)
        nextWord = currentWord + char
        check_word_exists(nextWord, dictionary, foundWords)
        generate_words_recur(nextWord, remainingLettersCopy, dictionary, foundWords)

    return


def check_word_exists(word, dictionary, foundWords):
    if 3 <= len(word) <= 7:
        if word in dictionary and word not in foundWords[len(word)]:
            foundWords[len(word)].append(word)
