import os
import cv2 as cv2
import numpy as np
import math
import time
import tkinter as tk
from tkinter import filedialog
import pygame as p
import chess_constants as ct
import sys

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"


class BayesClassifier:
    """Piece classifier of the system
       Can train, test, debug and return performance results
       on a digital chess board (besides predicted board)
    """
    def __init__(self, train, debug):
        self.piece_to_class = {'bP': 0, 'bN': 1, 'bR': 2, 'bB': 3, 'bQ': 4, 'bK': 5,
                               'wP': 6, 'wN': 7, 'wR': 8, 'wB': 9, 'wQ': 10, 'wK': 11}

        self.class_to_piece = {0: 'bP', 1: 'bN', 2: 'bR', 3: 'bB', 4: 'bQ', 5: 'bK',
                               6: 'wP', 7: 'wN', 8: 'wR', 9: 'wB', 10: 'wQ', 11: 'wK'}

        self.piece_accuracy = {'bP': [0, 0], 'bN': [0, 0], 'bR': [0, 0], 'bB': [0, 0], 'bQ': [0, 0], 'bK': [0, 0],
                               'wP': [0, 0], 'wN': [0, 0], 'wR': [0, 0], 'wB': [0, 0], 'wQ': [0, 0], 'wK': [0, 0]}

        self.work = 0
        self.nr_classes = 12
        self.interest = 65
        self.train = train
        self.debug = debug
        self.imported_image = None
        self.file = None
        self.predicted_board = ct.blank_board
        self.white_king_location = (None, None)
        self.black_king_location = (None, None)

    def split_board(self, input_image, d, likelihood, priori):
        """Divides the digital board into 64 pieces
           Each piece will be classified and the predicted
           board will be built and returned

           Keyword arguments:
           input_image -- loaded digital chess board
           d           -- interest area (default 60x60 or 65x65)
           likelihood  -- likelihood data (after train process)
           priori      -- priori data (after train process)
        """
        img_h = input_image.shape[0]
        img_w = input_image.shape[1]

        predicted_array = []

        if img_h > img_w:
            while img_h % 8 != 0:
                img_h = img_h + 1
                self.work += 1
            input_image = cv2.resize(input_image, (img_h, img_h), interpolation=cv2.INTER_AREA)
            img_w = img_h
        if img_h < img_w:
            while img_w % 8 != 0:
                self.work += 1
                self.work += 1
                img_w = img_w + 1
            input_image = cv2.resize(input_image, (img_w, img_w), interpolation=cv2.INTER_AREA)
            img_h = img_w

        h = img_h // 8
        w = img_w // 8

        tiles = [input_image[x:x+h, y:y+w]
                 for x in range(0, img_h, h) for y in range(0, img_w, w)]

        for i in range(0, 64):
            resized_im = cv2.resize(tiles[i], (ct.test_img_size, ct.test_img_size), interpolation=cv2.INTER_AREA)
            ret, bin_image = cv2.threshold(resized_im, 127, 255, cv2.THRESH_BINARY)

            s = 0
            n = 0
            for k in range(30, 60):
                for j in range(30, 60):
                    s = s + bin_image[k, j]
                    n = n + 1
                    self.work += 1

            if np.mean(bin_image) > 250:
                predicted_array.append("xx")
            else:
                feature_vector = []

                if s/n > 120:
                    bin_image = 255 - bin_image

                for k in range((ct.test_img_size - self.interest) // 2, (ct.test_img_size + self.interest) // 2):
                    for j in range((ct.test_img_size - self.interest) // 2, (ct.test_img_size + self.interest) // 2):
                        feature_vector.append(bin_image[k, j])
                        self.work += 1

                probabilities = []

                for c in range(0, self.nr_classes):
                    probability = 0
                    for u in range(0, d - 1):
                        if feature_vector[u] == 255:
                            probability = probability + math.log(likelihood[c, u])
                        else:
                            probability = probability + math.log(1 - likelihood[c, u])
                        self.work += 1
                    if priori[c, 0] > 0:
                        probability = probability + math.log(priori[c, 0])
                    probabilities.append(probability)

                max_class = 0
                max_prob = -sys.maxsize

                for j in range(0, self.nr_classes):
                    if probabilities[j] > max_prob:
                        max_class = j
                        max_prob = probabilities[j]
                        self.work += 1

                if max_class == 5:
                    self.black_king_location = (i//8, i % 8)
                elif max_class == 11:
                    self.white_king_location = (i//8, i % 8)

                predicted_array.append(self.class_to_piece[max_class])
                self.predicted_board[i//8][i % 8] = self.class_to_piece[max_class]

                if self.debug:
                    self.bayes_debug(probabilities, max_class, bin_image, "Test image")
                    print(self.class_to_piece[max_class])
                    cv2.imshow("Test image", bin_image)
                    cv2.waitKey()

        self.predicted_board = np.asarray(predicted_array)
        self.predicted_board = np.reshape(self.predicted_board, (8, 8))
        print(self.predicted_board)
        print(f"White king location = {self.white_king_location}")
        print(f"Black king location = {self.black_king_location}")

    def bayes_train(self, test):
        """Naive Bayes training process

           Keyword arguments:
           test -- True if the tests (from the test directory)
                   will be executed after the training process
        """
        n = ct.count_folder_files(sys.path[1] + f'\\train\\')
        d = self.interest * self.interest

        x = np.zeros((n, d), dtype=int)
        y = np.zeros((n, 1), dtype=int)

        priori = np.zeros((self.nr_classes, 1), dtype=float)

        for i in range(0, self.nr_classes):
            priori[i, 0] = ct.count_folder_files(sys.path[1] + f'\\train\\{self.class_to_piece[i]}') / n

        if self.train:
            row = 0
            for subdir, dirs, files in os.walk(sys.path[1] + f'\\train\\'):
                for file in files:

                    filepath = subdir + os.sep + file
                    image_train = cv2.imread(filepath)
                    gray_image = cv2.cvtColor(image_train, cv2.COLOR_BGR2GRAY)
                    print(gray_image)
                    ret, bin_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)

                    if subdir[-2] == 'w':
                        bin_image = 255 - bin_image

                    values = []

                    for i in range((ct.test_img_size - self.interest) // 2,
                                   (ct.test_img_size + self.interest) // 2):
                        for j in range((ct.test_img_size - self.interest) // 2,
                                       (ct.test_img_size + self.interest) // 2):
                            values.append(bin_image[i, j])
                            self.work += 1

                    for i in range(0, d):
                        x[row, i] = values[i]
                        self.work += 1

                    piece_name = subdir[-2] + subdir[-1]
                    y[row, 0] = self.piece_to_class[piece_name]
                    row = row + 1

            priori_file = open(ct.classifier_priori, "w")
            for row in priori:
                np.savetxt(priori_file, row)
                self.work += 1

            priori_file.close()
            likelihood = np.zeros((self.nr_classes, d), dtype=float)

            for c in range(0, d-1):
                for i in range(0, n-1):
                    if x[i, c] == 255:
                        likelihood[y[i, 0], c] = likelihood[y[i, 0], c] + 1
                        self.work += 1

            for i in range(0, self.nr_classes):
                for j in range(0, d-1):
                    likelihood[i, j] = likelihood[i, j] + 1
                    likelihood[i, j] = likelihood[i, j] / (self.count_folder_files(sys.path[1] +
                                                           f'\\train\\{self.class_to_piece[i]}') + self.nr_classes)
                    self.work += 1

            likelihood_file = open(ct.classifier_likelihood, "w")
            for row in likelihood:
                np.savetxt(likelihood_file, row)
                self.work += 1
            likelihood_file.close()

        else:
            likelihood = np.loadtxt(ct.classifier_likelihood).reshape(self.nr_classes, d)
            priori = np.loadtxt(ct.classifier_priori).reshape(self.nr_classes, 1)

        if test:
            self.bayes_test(likelihood, priori, d)
        else:
            root = tk.Tk()
            root.withdraw()
            self.file = filedialog.askopenfilename()
            try:
                self.imported_image = p.image.load(self.file)
                root.destroy()
                board_image = cv2.imread(self.file)
                gray_image = cv2.cvtColor(board_image, cv2.COLOR_BGR2GRAY)
                self.split_board(gray_image, d, likelihood, priori)
            except:
                print("Wrong file or file path")
                self.imported_image = 0
                return

    def bayes_debug(self, probabilities, max_class, bin_image, image_name):
        """Will display probabilities of all classes
           and the final result after a piece is classified

           Keyword arguments:
           probabilities -- results from the classifier process
           max_class     -- the winner of the classifier process
           bin_image     -- the processed image
           image_name    -- the label of the example
        """
        for i in range(0, self.nr_classes):
            print(f'Probability for class {self.class_to_piece[i]} : {probabilities[i]}')
            self.work += 1

        print(f'Predicted class is {self.class_to_piece[max_class]}')

        cv2.namedWindow(image_name, cv2.WINDOW_NORMAL)
        bin_image = cv2.resize(bin_image, (200, 200))
        cv2.imshow(image_name, bin_image)
        cv2.waitKey()

    def bayes_test(self, likelihood, priori, d):
        """Naive Bayes test process

           Keyword arguments:
           likelihood  -- likelihood data (after train process)
           priori      -- priori data (after train process)
           d           -- interest area (default 60x60 or 65x65)
        """
        nr_correct = 0
        nr_test = 0
        confusion_matrix = np.zeros((self.nr_classes, self.nr_classes), dtype=int)

        for subdir, dirs, files in os.walk(sys.path[1] + f'\\test\\'):
            for file in files:

                filepath = subdir + os.sep + file
                image_test = cv2.imread(filepath)

                gray_image = cv2.cvtColor(image_test, cv2.COLOR_BGR2GRAY)
                ret, bin_image = cv2.threshold(gray_image, 127, 255, cv2.THRESH_BINARY)

                assert not isinstance(bin_image, type(None)), 'Image not found'

                if subdir[-2] == 'w':
                    bin_image = 255 - bin_image

                feature_vector = []

                for i in range((ct.test_img_size - self.interest) // 2,
                               (ct.test_img_size + self.interest) // 2):
                    for j in range((ct.test_img_size - self.interest) // 2,
                                   (ct.test_img_size + self.interest) // 2):
                        feature_vector.append(bin_image[i, j])
                        self.work += 1

                probabilities = []

                for c in range(0, self.nr_classes):
                    probability = 0
                    for i in range(0, d-1):
                        if feature_vector[i] == 255:
                            probability = probability + math.log(likelihood[c, i])
                        else:
                            probability = probability + math.log(1 - likelihood[c, i])
                        self.work += 1
                    if priori[c, 0] > 0:
                        probability = probability + math.log(priori[c, 0])
                    probabilities.append(probability)

                max_class = 0
                max_prob = -sys.maxsize

                for i in range(0, self.nr_classes):
                    if probabilities[i] > max_prob:
                        max_class = i
                        max_prob = probabilities[i]
                        self.work += 1

                confusion_matrix[self.piece_to_class[subdir[-2] + subdir[-1]]][max_class] += 1

                if max_class == self.piece_to_class[subdir[-2] + subdir[-1]]:
                    self.piece_accuracy[subdir[-2] + subdir[-1]][0] = \
                        self.piece_accuracy[subdir[-2] + subdir[-1]][0] + 1
                    nr_correct = nr_correct + 1

                self.piece_accuracy[subdir[-2] + subdir[-1]][1] = self.piece_accuracy[subdir[-2] + subdir[-1]][1] + 1

                nr_test = nr_test + 1
                if self.debug:
                    self.bayes_debug(probabilities, max_class, bin_image, subdir)

        for key in self.piece_accuracy:
            if self.piece_accuracy[key][1] != 0:
                print(f'Accuracy for {key} is'
                      f' {round(self.piece_accuracy[key][0] * 100 / self.piece_accuracy[key][1], 2)}%')

        print(f'Total accuracy is {round(nr_correct * 100 / nr_test, 2)}%')
        print(f'Total tests: {nr_test}')
        print(f'Total correct tests: {nr_correct}')
        print(f'Confusion matrix:\n  {confusion_matrix}')

    def bayes(self):
        """Main method
           If self.train is false then the process
           will be skipped and the likelihood and priori
           data will be taken from their respective  files
        """
        self.work = 0
        start = time.time()
        self.bayes_train(test=False)
        end = time.time() - start
        print(f'Runtime {round(end, 2)} [s]')
        print(f'Work = {self.work}')
        self.work = 2100000
