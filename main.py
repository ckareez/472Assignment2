# COMP472 - Assignment 2 - Summer 2021
# Programmed By:
# Constantine Karellas - 40109253
# Max Burah - 40077075

from matplotlib.pyplot import cla
import pandas as pd
import requests
import math
import string
import re
from bs4 import BeautifulSoup
import numpy as np
import matplotlib.pyplot as plt


class Episode:
    def __init__(self, name, season, reviewLink, year):
        self.name = name
        self.season = season
        self.reviewLink = reviewLink
        self.year = year

    def printEpisode(self):
        print(self.name, " ", self.season, " ", self.reviewLink, " ", self.year)


class Review:
    def __init__(self, title, review, reviewRating, isPositive):
        self.title = title
        self.review = review
        self.reviewRating = reviewRating
        self.isPositive = isPositive

    def printReview(self):
        print(self.title, " ", self.review, " ", self.reviewRating, " ", self.isPositive)


######### Extract the Data and Build the Model  ###########
# Using words for tokens in this model
# Method to count word frequency for a review
def wordFrequency(paragraph):
    wordList = paragraph.split()
    wordFreq = []
    for w in wordList:
        wordFreq.append(wordList.count(w))
    print("Review:\n" + paragraph)
    print("List:\n" + str(wordList) + "\n")
    print("Frequencies:\n" + str(wordFreq) + "\n")
    print("Pairs:\n" + str(list(zip(wordList, wordFreq))))


removeFile = open("remove.txt", 'w')
removedTotal = []


# method to remove stopwords from a given paragraph
def removeStopwords(paragraph, stopwords):
    wordList = paragraph.split()
    resultWords = [word for word in wordList if word not in stopwords]

    # find removed words and write to removed.txt
    removedWords = [word for word in wordList if word in stopwords]
    for word in removedWords:
        if word not in removedTotal:
            removedTotal.append(word)
            removeFile.write(word + "\n")
    result = ' '.join(resultWords)
    return result


# Read the stopword file into a stopWordList
stopWordFile = open("Stopword_File.txt", "r")
stopWordList = stopWordFile.read()
stopWordFile.close()

positiveWords = []
negativeWords = []
FreqPositiveWords = []
FreqNegativeWords = []

titleReview = []
ratingReview = []


def extractReviewData(seasonURL, posWordList, negWordList):
    seasonResponse = requests.get(seasonURL)
    seasonSoup = BeautifulSoup(seasonResponse.content, 'html.parser')
    episodeData = seasonSoup.findAll('div', attrs={'class': 'list_item'})

    # iterate through all episodes of given season URL
    for k in episodeData:
        episodeURL = k.find('a').get('href')
        reviewURL = 'https://www.imdb.com' + str(episodeURL) + "reviews?ref_=tt_ov_rt"

        # Extract the review data given a review URL of an episode
        reviewResponse = requests.get(reviewURL)
        reviewSoup = BeautifulSoup(reviewResponse.content, 'html.parser')
        # lister-item-content can be used to find review ratings
        reviewData = reviewSoup.findAll('div', attrs={'class': 'lister-item-content'})

        # iterate through all reviews of the season, clean the string and count the word frequency for each word
        for j in reviewData:
            r = Review(None, None, None, None)
            # Find review rating, only consider reviews that have a rating
            if j.find('div', class_='ipl-ratings-bar') is not None:
                reviewRating = j.find('div', class_='ipl-ratings-bar').text.replace('\n', '')
                if len(reviewRating) == 5:
                    r.reviewRating = int(reviewRating[0:2])
                else:
                    r.reviewRating = int(reviewRating[0:1])

                # Assign positive or negative review status
                if r.reviewRating >= 8:
                    r.isPositive = True
                    ratingReview.append(r.isPositive)
                else:
                    r.isPositive = False
                    ratingReview.append(r.isPositive)

                # get the review Title
                r.title = j.find('a', class_='title').text.replace('\n', '')
                titleReview.append(r.title)

                # get the actual review
                r.review = j.find('div', class_='content').div.text.lower()

                # print(wordCount)
                # clean review by inserting <s>

                r.review = r.review.replace(".", " ").replace("(", " ").replace(")", " ").replace("?", " ").replace("!",
                                                                                                                    " ").replace(
                    ":", " ").replace(";", " ").replace(",", " ").replace("\\", " ").replace("[", " ").replace("]",
                                                                                                               " ").replace(
                    "[", " ").replace('"', ' ').replace('"]', ' ').replace("*", " ").replace("-", " ")
                r.review = removeStopwords(r.review, stopWordList)

                # check if review is positive or negative and place in corresponding list
                if r.isPositive:
                    # posWordList.append(r.review.split())
                    posWordList.append(r.review)

                else:
                    negWordList.append(r.review)

    # we have obtained a list of all negative words and all positive words plus their respective counts
    # print("Positive Word List:\n" + str(posWordList) + "\n")
    # print("Negative Word List:\n" + str(negWordList) + "\n")

    return posWordList, negWordList


# compute positive wordlist frequencies
def computeFrequency(wordList):
    wordList = str(wordList).split()
    wordFreq = []
    wordList = [word.replace("[", "") for word in wordList]
    wordList = [word.replace("]", "") for word in wordList]

    for w in wordList:
        wordFreq.append(wordList.count(w))

    return dict(zip(wordList, wordFreq))


def computeProbability(dictPos, dictNeg, smoothing):
    count1 = 1
    modelFile = open("model.txt", 'w')
    posSize = len(dictPos)
    negSize = len(dictNeg)

    # print("POS SIZE: " + str(posSize))
    # print("NEG SIZE: " + str(negSize))

    for word in dictPos:
        posFrequency = (dictPos[word]) + smoothing
        posProbability = math.log10(posFrequency / posSize)
        if word in dictNeg:
            negFrequency = (dictNeg[word]) + smoothing
        else:
            negFrequency = smoothing
        negProbability = math.log10(negFrequency / negSize)

        modelFile.write(
            "No." + str(count1) + "  " + str(word.replace('.', '').replace(',', '').replace('"', '')) + "\n")
        modelFile.write(
            str(str(posFrequency) + ", " + str(posProbability) + ", " + str(negFrequency) + ", " + str(
                negProbability) + "\n\n"))
        count1 += 1

        # print("Word: ", word, " PosFreq: ", posFrequency, " NegFreq: ", negFrequency," PosProbability: ",
        # posProbability," NEGProbability: ",negProbability)

    for word in dictNeg:
        negFrequency = (dictNeg[word]) + smoothing
        negProbability = math.log10(negFrequency / negSize)
        if word in dictPos:
            posFrequency = (dictPos[word]) + smoothing
        else:
            posFrequency = smoothing
        posProbability = math.log10(posFrequency / posSize)

        modelFile.write(
            "No." + str(count1) + "  " + str(word.replace('.', '').replace(',', '').replace('"', '')) + "\n")
        modelFile.write(
            str(str(posFrequency) + ", " + str(posProbability) + ", " + str(negFrequency) + ", " + str(
                negProbability) + "\n\n"))
        count1 += 1

        # print("Word: ", word, " PosFreq: ", posFrequency, " NegFreq: ", negFrequency, " PosProbability: ",
        # posProbability, " NEGProbability: ", negProbability)


############################# RUN CODE ##############################

print("\nProgram Start:\n")
# Use extract review data to create complete positive and negative word lists

season1URL = 'https://www.imdb.com/title/tt0098904/episodes?season=1&ref_=ttep_ep_sn_pv'

print("\nCalculating Season 1...\n")
season1Lists = extractReviewData(season1URL, [], [])
season1posList = season1Lists[0]
season1negList = season1Lists[1]

# print("Season 1:" + str(season1posList))
# print("Season 1:" + str(season1negList))

print("\nCalculating Season 2...\n")
season2URL = 'https://www.imdb.com/title/tt0098904/episodes?season=2'

season2Lists = extractReviewData(season2URL, season1posList, season1negList)
season2posList = season2Lists[0]
season2negList = season2Lists[1]

# print("Season 2:" + str(season2posList))
# print("Season 2:" + str(season2negList))

print("\nCalculating Season 3...\n")
season3URL = 'https://www.imdb.com/title/tt0098904/episodes?season=3'

season3Lists = extractReviewData(season3URL, season2posList, season2negList)
season3posList = season3Lists[0]
season3negList = season3Lists[1]

# print("Season 3:" + str(season3posList))
# print("Season 3:" + str(season3negList))

print("\nCalculating Season 4...\n")
season4URL = 'https://www.imdb.com/title/tt0098904/episodes?season=4'

season4Lists = extractReviewData(season4URL, season3posList, season3negList)
season4posList = season4Lists[0]
season4negList = season4Lists[1]

# print("Season 4 POS:" + str(season4posList))
# print("Season 4 NEG:" + str(season4negList))

print("\nCalculating Probabilities...\n")
posDict = computeFrequency(season4posList)
negDict = computeFrequency(season4negList)
computeProbability(posDict, negDict, 1)

seasonEpisodeNum = []
episodeName = []
episodeRating = []
episodeDate = []
episodeLink = []
reviewLink = []

url1 = 'https://www.imdb.com/title/tt0098904/episodes?season=1&ref_=ttep_ep_sn_pv'
response1 = requests.get(url1)
soup1 = BeautifulSoup(response1.content, 'html.parser')
episodeData1 = soup1.findAll('div', attrs={'class': 'list_item'})

# Webscraping for Season 1
for i in episodeData1:
    # Webscraping the episode number and season number
    season_episode = i.div.a.text.replace('\n', '')
    seasonEpisodeNum.append(season_episode)
    # print("Season and Episode Number:" + str(season_episode))
    # Webscraping the episode title
    episodeTitle = soup1.strong.extract()
    name = episodeTitle.text.replace('\n', '')
    episodeName.append(name)
    # print("Episode Title: " + str(name))
    # Webscraping the episode rating
    rating = i.find('div', class_='ipl-rating-star small').text.replace('\n', '')
    episodeRating.append(rating[:-7])
    # print("Episode Rating: " + str(rating[:-7]))
    # Webscraping the episode date
    date = i.find('div', class_='airdate').text.replace(' ', '').replace('\n', '').replace('.', '')
    episodeDate.append(date[-4:])
    # print("Episode Date of Release: " + str(date[-4:]))
    # pageLink = soup.strong.extract()
    # if pageLink.has_attr('href'):
    episodeLink = i.find('a').get('href')
    urlOfEpisode = 'https://www.imdb.com' + str(episodeLink)
    urlOfReview = str(urlOfEpisode) + "reviews?ref_=tt_ov_rt"
    reviewLink.append(urlOfReview)
    # print("Review Link: " + str(urlOfReview))
    # print("\n")

url2 = 'https://www.imdb.com/title/tt0098904/episodes?season=2'
response2 = requests.get(url2)
soup2 = BeautifulSoup(response2.content, 'html.parser')
episodeData2 = soup2.findAll('div', attrs={'class': 'list_item'})

# Webscraping for Season 2
for i in episodeData2:
    # Webscraping the episode number and season number
    season_episode = i.div.a.text.replace('\n', '')
    seasonEpisodeNum.append(season_episode)
    # print("Season and Episode Number:" + str(season_episode))
    # Webscraping the episode title
    episodeTitle = soup2.strong.extract()
    name = episodeTitle.text.replace('\n', '')
    episodeName.append(name)
    # print("Episode Title: " + str(name))
    # Webscraping the episode rating
    rating = i.find('div', class_='ipl-rating-star small').text.replace('\n', '')
    episodeRating.append(rating[:-7])
    # print("Episode Rating: " + str(rating[:-7]))
    # Webscraping the episode date
    date = i.find('div', class_='airdate').text.replace(' ', '').replace('\n', '').replace('.', '')
    episodeDate.append(date[-4:])
    # print("Episode Date of Release: " + str(date[-4:]))
    # pageLink = soup.strong.extract()
    # if pageLink.has_attr('href'):
    episodeLink = i.find('a').get('href')
    urlOfEpisode = 'https://www.imdb.com' + str(episodeLink)
    urlOfReview = str(urlOfEpisode) + "reviews?ref_=tt_ov_rt"
    reviewLink.append(urlOfReview)
    # print("Review Link: " + str(urlOfReview))
    # print("\n")

url3 = 'https://www.imdb.com/title/tt0098904/episodes?season=3'
response3 = requests.get(url3)
soup3 = BeautifulSoup(response3.content, 'html.parser')
episodeData3 = soup3.findAll('div', attrs={'class': 'list_item'})

# Webscraping for Season 3
for i in episodeData3:
    # Webscraping the episode number and season number
    season_episode = i.div.a.text.replace('\n', '')
    seasonEpisodeNum.append(season_episode)
    # print("Season and Episode Number:" + str(season_episode))
    # Webscraping the episode title
    episodeTitle = soup3.strong.extract()
    name = episodeTitle.text.replace('\n', '')
    episodeName.append(name)
    # print("Episode Title: " + str(name))
    # Webscraping the episode rating
    rating = i.find('div', class_='ipl-rating-star small').text.replace('\n', '')
    episodeRating.append(rating[:-7])
    # print("Episode Rating: " + str(rating[:-7]))
    # Webscraping the episode date
    date = i.find('div', class_='airdate').text.replace(' ', '').replace('\n', '').replace('.', '')
    episodeDate.append(date[-4:])
    # print("Episode Date of Release: " + str(date[-4:]))
    # pageLink = soup.strong.extract()
    # if pageLink.has_attr('href'):
    episodeLink = i.find('a').get('href')
    urlOfEpisode = 'https://www.imdb.com' + str(episodeLink)
    urlOfReview = str(urlOfEpisode) + "reviews?ref_=tt_ov_rt"
    reviewLink.append(urlOfReview)
    # print("Review Link: " + str(urlOfReview))

url4 = 'https://www.imdb.com/title/tt0098904/episodes?season=4'
response4 = requests.get(url4)
soup4 = BeautifulSoup(response4.content, 'html.parser')
episodeData4 = soup4.findAll('div', attrs={'class': 'list_item'})

# Webscraping for Season 4
for i in episodeData4:
    # Webscraping the episode number and season number
    season_episode = i.div.a.text.replace('\n', '')
    seasonEpisodeNum.append(season_episode)
    # print("Season and Episode Number:" + str(season_episode))
    # Webscraping the episode title
    episodeTitle = soup4.strong.extract()
    name = episodeTitle.text.replace('\n', '')
    episodeName.append(name)
    # print("Episode Title: " + str(name))
    # Webscraping the episode rating
    rating = i.find('div', class_='ipl-rating-star small').text.replace('\n', '')
    episodeRating.append(rating[:-7])
    # print("Episode Rating: " + str(rating[:-7]))
    # Webscraping the episode date
    date = i.find('div', class_='airdate').text.replace(' ', '').replace('\n', '').replace('.', '')
    episodeDate.append(date[-4:])
    # print("Episode Date of Release: " + str(date[-4:]))
    # pageLink = soup.strong.extract()
    # if pageLink.has_attr('href'):
    episodeLink = i.find('a').get('href')
    urlOfEpisode = 'https://www.imdb.com' + str(episodeLink)
    urlOfReview = str(urlOfEpisode) + "reviews?ref_=tt_ov_rt"
    reviewLink.append(urlOfReview)
    # print("Review Link: " + str(urlOfReview))

# Building DataFrame
print("\n\n")
season_DF = pd.DataFrame(
    {'Name': episodeName, 'Season': seasonEpisodeNum, 'Review Link': reviewLink, 'Year': episodeDate})
print(season_DF)
print("\n\n")

# Putting Datafram into data.csv file
season_DF.to_csv('data.csv', sep='|', encoding='utf-8')

# Creating result.txt file
resultFile = open("result.txt", "w")

# making the isPostive list display positive or negative
pos = 'Positive'
neg = 'Negative'
ratingPosNeg = []
for i in ratingReview:
    if i == True:
        ratingPosNeg.append(pos)
    else:
        ratingPosNeg.append(neg)


def testReviewTitles(smoothing):
    count2 = 1

    reviewDict = dict(zip(titleReview, ratingPosNeg))
    # print(reviewDict)

    correctnessCounter = 0

    for reviewTitle in reviewDict:
        # make the review name a list of words
        reviewName = reviewTitle.lower().replace(".", " ").replace("(", " ").replace(")", " ").replace("?",
                                                                                                       " ").replace(
            "!",
            " ").replace(
            ":", " ").replace(";", " ").replace(",", " ").replace("\\", " ").replace("[", " ").replace("]",
                                                                                                       " ").replace(
            "[", " ").replace('"', ' ').replace('"]', ' ').replace("*", " ").replace("-", " ")
        reviewName = reviewName.split()
        # print(reviewName)

        totalPosFrequency = 0
        totalNegFrequency = 0
        for word in reviewName:
            if word in posDict:
                posFrequency = posDict[word] + smoothing
            else:
                posFrequency = smoothing
            if word in negDict:
                negFrequency = negDict[word]
            else:
                negFrequency = smoothing

            # print(word, "  Frequency in Pos: ", posFrequency, "  Frequency in Neg: ", negFrequency)

            totalPosFrequency += posFrequency
            totalNegFrequency += negFrequency

        # print("TotalPosFrequency ", totalPosFrequency, " TotalNegFrequency ", totalNegFrequency)

        posSize = len(posDict)
        negSize = len(negDict)

        posProbability = math.log10(totalPosFrequency / posSize)
        negProbability = math.log10(totalNegFrequency / negSize)

        actual = reviewDict[reviewTitle]

        if posProbability > negProbability:
            prediction = "Positive"
        else:
            prediction = "Negative"

        if prediction == actual:
            correctness = "Prediction was Right"
            correctnessCounter += 1
        else:
            correctness = "Prediction was Wrong"

        resultFile.write("No." + str(count2) + "  " + str(reviewTitle) + "\n")
        resultFile.write(
            str(posProbability) + " , " + str(
                negProbability) + " , " + prediction + " , " + actual + " , " + correctness + "\n\n")
        count2 += 1

    numReviews = len(reviewDict)
    precision = (correctnessCounter / numReviews) * 100

    resultFile.write("Prediction Correctness is " + str(precision) + "%\n\n")
    return precision


print("\nTesting Data...\n")

testReviewTitles(1)


########## TASK 2.2: WORD SMOOTHING FILTERING ################

def computeProbabilitySmoothing(dictPos, dictNeg, smoothing):
    count1 = 1
    modelFile = open("smooth-model.txt", 'w')
    posSize = len(dictPos)
    negSize = len(dictNeg)

    # print("POS SIZE: " + str(posSize))
    # print("NEG SIZE: " + str(negSize))

    for word in dictPos:
        posFrequency = (dictPos[word]) + smoothing
        posProbability = math.log10(posFrequency / posSize)
        if word in dictNeg:
            negFrequency = (dictNeg[word]) + smoothing
        else:
            negFrequency = smoothing
        negProbability = math.log10(negFrequency / negSize)

        modelFile.write(
            "No." + str(count1) + "  " + str(word.replace('.', '').replace(',', '').replace('"', '')) + "\n")
        modelFile.write(
            str(str(posFrequency) + ", " + str(posProbability) + ", " + str(negFrequency) + ", " + str(
                negProbability) + "\n\n"))
        count1 += 1

        # print("Word: ", word, " PosFreq: ", posFrequency, " NegFreq: ", negFrequency," PosProbability: ",
        # posProbability," NEGProbability: ",negProbability)

    for word in dictNeg:
        negFrequency = (dictNeg[word]) + smoothing
        negProbability = math.log10(negFrequency / negSize)
        if word in dictPos:
            posFrequency = (dictPos[word]) + smoothing
        else:
            posFrequency = smoothing
        posProbability = math.log10(posFrequency / posSize)

        modelFile.write(
            "No." + str(count1) + "  " + str(word.replace('.', '').replace(',', '').replace('"', '')) + "\n")
        modelFile.write(
            str(str(posFrequency) + ", " + str(posProbability) + ", " + str(negFrequency) + ", " + str(
                negProbability) + "\n\n"))
        count1 += 1

        # print("Word: ", word, " PosFreq: ", posFrequency, " NegFreq: ", negFrequency, " PosProbability: ",
        # posProbability, " NEGProbability: ", negProbability)


resultSmoothingFile = open("smooth-result.txt", "w")

def testReviewTitlesSmoothing1(smoothing):
    count2 = 1

    reviewDict = dict(zip(titleReview, ratingPosNeg))
    # print(reviewDict)

    correctnessCounter = 0

    for reviewTitle in reviewDict:
        # make the review name a list of words
        reviewName = reviewTitle.lower().replace(".", " ").replace("(", " ").replace(")", " ").replace("?",
                                                                                                       " ").replace(
            "!",
            " ").replace(
            ":", " ").replace(";", " ").replace(",", " ").replace("\\", " ").replace("[", " ").replace("]",
                                                                                                       " ").replace(
            "[", " ").replace('"', ' ').replace('"]', ' ').replace("*", " ").replace("-", " ")
        reviewName = reviewName.split()
        # print(reviewName)

        totalPosFrequency = 0
        totalNegFrequency = 0
        for word in reviewName:
            if word in posDict:
                posFrequency = posDict[word] + smoothing
            else:
                posFrequency = smoothing
            if word in negDict:
                negFrequency = negDict[word]
            else:
                negFrequency = smoothing

            # print(word, "  Frequency in Pos: ", posFrequency, "  Frequency in Neg: ", negFrequency)

            totalPosFrequency += posFrequency
            totalNegFrequency += negFrequency

        # print("TotalPosFrequency ", totalPosFrequency, " TotalNegFrequency ", totalNegFrequency)

        posSize = len(posDict)
        negSize = len(negDict)

        posProbability = math.log10(totalPosFrequency / posSize)
        negProbability = math.log10(totalNegFrequency / negSize)

        actual = reviewDict[reviewTitle]

        if posProbability > negProbability:
            prediction = "Positive"
        else:
            prediction = "Negative"

        if prediction == actual:
            correctness = "Prediction was Right"
            correctnessCounter += 1
        else:
            correctness = "Prediction was Wrong"

    numReviews = len(reviewDict)
    precision = (correctnessCounter / numReviews) * 100

    return precision

def testReviewTitlesSmoothing2(smoothing):
    count2 = 1

    reviewDict = dict(zip(titleReview, ratingPosNeg))
    # print(reviewDict)

    correctnessCounter = 0

    for reviewTitle in reviewDict:
        # make the review name a list of words
        reviewName = reviewTitle.lower().replace(".", " ").replace("(", " ").replace(")", " ").replace("?",
                                                                                                       " ").replace(
            "!",
            " ").replace(
            ":", " ").replace(";", " ").replace(",", " ").replace("\\", " ").replace("[", " ").replace("]",
                                                                                                       " ").replace(
            "[", " ").replace('"', ' ').replace('"]', ' ').replace("*", " ").replace("-", " ")
        reviewName = reviewName.split()
        # print(reviewName)

        totalPosFrequency = 0
        totalNegFrequency = 0
        for word in reviewName:
            if word in posDict:
                posFrequency = posDict[word] + smoothing
            else:
                posFrequency = smoothing
            if word in negDict:
                negFrequency = negDict[word]
            else:
                negFrequency = smoothing

            # print(word, "  Frequency in Pos: ", posFrequency, "  Frequency in Neg: ", negFrequency)

            totalPosFrequency += posFrequency
            totalNegFrequency += negFrequency

        # print("TotalPosFrequency ", totalPosFrequency, " TotalNegFrequency ", totalNegFrequency)

        posSize = len(posDict)
        negSize = len(negDict)

        posProbability = math.log10(totalPosFrequency / posSize)
        negProbability = math.log10(totalNegFrequency / negSize)

        actual = reviewDict[reviewTitle]

        if posProbability > negProbability:
            prediction = "Positive"
        else:
            prediction = "Negative"

        if prediction == actual:
            correctness = "Prediction was Right"
            correctnessCounter += 1
        else:
            correctness = "Prediction was Wrong"

        resultSmoothingFile.write("No." + str(count2) + "  " + str(reviewTitle) + "\n")
        resultSmoothingFile.write(
            str(posProbability) + " , " + str(
                negProbability) + " , " + prediction + " , " + actual + " , " + correctness + "\n\n")
        count2 += 1

    numReviews = len(reviewDict)
    precision = (correctnessCounter / numReviews) * 100

    resultSmoothingFile.write("Prediction Correctness is " + str(precision) + "%\n\n")
    return precision


print("\nPerforming Task 2.2: Word Smoothing Filtering ....\n")

# changing smoothing value
precision12 = testReviewTitlesSmoothing1(1.2)
precision14 = testReviewTitlesSmoothing1(1.4)
precision16 = testReviewTitlesSmoothing2(1.6)
precision18 = testReviewTitlesSmoothing1(1.8)
precision2 = testReviewTitlesSmoothing1(2)
precision1 = testReviewTitlesSmoothing1(1)

# Write results of 1.6
computeProbabilitySmoothing(posDict, negDict, 1.6)

# Matplotlib plotting

smoothValues = 1, 1.2, 1.4, 1.6, 1.8, 2
precisionValues = precision1, precision12, precision14, precision16, precision18, precision2

plt.scatter(precisionValues, smoothValues)
plt.title("Word Smoothing Filtering")
plt.xlabel("Precision Values (%)")
plt.ylabel("Smoothing Values")
plt.show()

########## TASK 2.3: WORD LENGTH FILTERING ################
print("\nPerforming Task 2.3: Word Length Filtering ....\n")


def computeFrequencyLength2(wordList):
    wordList = str(wordList).split()
    wordFreq = []
    for w in wordList:
        w.replace(' ', '').replace("'","")
        if len(w) <= 2:
            wordList.remove(w)
        else:
            wordFreq.append(wordList.count(w))

    return dict(zip(wordList, wordFreq))


def computeFrequencyLength4(wordList):
    wordList = str(wordList).split()
    wordFreq = []
    for w in wordList:
        w.replace(' ', '').replace("'","")
        if len(w) > 4:
            wordFreq.append(wordList.count(w))
        else:
            wordList.remove(w)

    return dict(zip(wordList, wordFreq))


def computeFrequencyLength9(wordList):
    wordList = str(wordList).split()
    wordFreq = []
    for w in wordList:
        w.replace(' ', '').replace("'","")
        if len(w) < 9:
            wordFreq.append(wordList.count(w))
        else:
            wordList.remove(w)

    return dict(zip(wordList, wordFreq))


def computeProbabilityLength(dictPos, dictNeg, smoothing):
    count1 = 1
    modelFile = open("length-model.txt", 'w')
    posSize = len(dictPos)
    negSize = len(dictNeg)

    # print("POS SIZE: " + str(posSize))
    # print("NEG SIZE: " + str(negSize))

    for word in dictPos:
        posFrequency = (dictPos[word]) + smoothing
        posProbability = math.log10(posFrequency / posSize)
        if word in dictNeg:
            negFrequency = (dictNeg[word]) + smoothing
        else:
            negFrequency = smoothing
        negProbability = math.log10(negFrequency / negSize)

        modelFile.write(
            "No." + str(count1) + "  " + str(word.replace('.', '').replace(',', '').replace('"', '')) + "\n")
        modelFile.write(
            str(str(posFrequency) + ", " + str(posProbability) + ", " + str(negFrequency) + ", " + str(
                negProbability) + "\n\n"))
        count1 += 1

        # print("Word: ", word, " PosFreq: ", posFrequency, " NegFreq: ", negFrequency," PosProbability: ",
        # posProbability," NEGProbability: ",negProbability)

    for word in dictNeg:
        negFrequency = (dictNeg[word]) + smoothing
        negProbability = math.log10(negFrequency / negSize)
        if word in dictPos:
            posFrequency = (dictPos[word]) + smoothing
        else:
            posFrequency = smoothing
        posProbability = math.log10(posFrequency / posSize)

        modelFile.write(
            "No." + str(count1) + "  " + str(word.replace('.', '').replace(',', '').replace('"', '')) + "\n")
        modelFile.write(
            str(str(posFrequency) + ", " + str(posProbability) + ", " + str(negFrequency) + ", " + str(
                negProbability) + "\n\n"))
        count1 += 1

        # print("Word: ", word, " PosFreq: ", posFrequency, " NegFreq: ", negFrequency, " PosProbability: ",
        # posProbability, " NEGProbability: ", negProbability)


resultLengthFile = open("length-result.txt", "w")

# Removing Lenth 2
posDictLength2 = computeFrequencyLength2(season4posList)
negDictLength2 = computeFrequencyLength2(season4negList)
# computeProbabilityLength(posDictLength2, negDictLength2, 1)
# Removing Lenth 4
posDictLength4 = computeFrequencyLength4(season4posList)
negDictLength4 = computeFrequencyLength4(season4negList)

computeProbabilityLength(posDictLength4, negDictLength4, 1)
# Removing Lenth 9
posDictLength9 = computeFrequencyLength9(season4posList)
negDictLength9 = computeFrequencyLength9(season4negList)
# computeProbabilityLength(posDictLength9, negDictLength9, 1)

totalWords = []
def testReviewTitlesLength(posDict, negDict, smoothing):

    count2 = 1

    reviewDict = dict(zip(titleReview, ratingPosNeg))
    # print(reviewDict)

    correctnessCounter = 0

    for reviewTitle in reviewDict:
        # make the review name a list of words
        reviewName = reviewTitle.lower().replace(".", " ").replace("(", " ").replace(")", " ").replace("?",
                                                                                                       " ").replace(
            "!",
            " ").replace(
            ":", " ").replace(";", " ").replace(",", " ").replace("\\", " ").replace("[", " ").replace("]",
                                                                                                       " ").replace(
            "[", " ").replace('"', ' ').replace('"]', ' ').replace("*", " ").replace("-", " ")
        reviewName = reviewName.split()
        # print(reviewName)

        totalPosFrequency = 0
        totalNegFrequency = 0
        for word in reviewName:
            if word in posDict:
                posFrequency = posDict[word] + smoothing
            else:
                posFrequency = smoothing
            if word in negDict:
                negFrequency = negDict[word]
            else:
                negFrequency = smoothing

            # print(word, "  Frequency in Pos: ", posFrequency, "  Frequency in Neg: ", negFrequency)

            totalPosFrequency += posFrequency
            totalNegFrequency += negFrequency

        # print("TotalPosFrequency ", totalPosFrequency, " TotalNegFrequency ", totalNegFrequency)

        posSize = len(posDict)
        negSize = len(negDict)

        posProbability = math.log10(totalPosFrequency / posSize)
        negProbability = math.log10(totalNegFrequency / negSize)

        actual = reviewDict[reviewTitle]

        if posProbability > negProbability:
            prediction = "Positive"
        else:
            prediction = "Negative"

        if prediction == actual:
            correctness = "Prediction was Right"
            correctnessCounter += 1
        else:
            correctness = "Prediction was Wrong"

        resultLengthFile.write("No." + str(count2) + "  " + str(reviewTitle) + "\n")
        resultLengthFile.write(
            str(posProbability) + " , " + str(
                negProbability) + " , " + prediction + " , " + actual + " , " + correctness + "\n\n")
        count2 += 1

    totalWords.append(count2)
    numReviews = len(reviewDict)
    precision = (correctnessCounter / numReviews) * 100

    resultLengthFile.write("Prediction Correctness is " + str(precision) + "%\n\n")
    #print(totalWords)
    return precision

# changing length value
length2 = testReviewTitlesLength(posDictLength2,negDictLength2,1)
length4 = testReviewTitlesLength(posDictLength4,negDictLength4,1)
length9 = testReviewTitlesLength(posDictLength9,negDictLength9,1)

# Matplotlib plotting
lengthValues = 2, 4, 9
precisionLengthValues = length2, length4, length9

plt.scatter(precisionLengthValues, lengthValues)
plt.title("Word Length Filtering")
plt.xlabel("Precision Values (%)")
plt.ylabel("Length Values")
plt.show()

print("\nProgram Terminated.\n")
