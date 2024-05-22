import cv2
import numpy as np
from matplotlib import pyplot as plt
from PIL import Image
import easyocr
import requests

fileName = input("Enter file name: ")
img = cv2.imread('images/'+fileName)

(height, width, _) = img.shape

gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
kernel_size = 3
blur_gray = cv2.GaussianBlur(gray,(kernel_size, kernel_size),0)

edges = cv2.Canny(blur_gray, 50, 150, apertureSize=3)
kernel = np.ones((3,3), np.uint8);
canned = cv2.dilate(edges, kernel, iterations = 5);

# plt.imshow(canned, cmap='gray', aspect='auto')

# cv2_imshow(canned)

list = []
goodList = [0]

cropped = []

lines = cv2.HoughLinesP(canned, 1, np.pi/180, 100, minLineLength=0.6*width, maxLineGap=5)
for line in lines:
    x1, y1, x2, y2 = line[0]
    if (not (x1 == x2)) and abs((y2 - y1)/(x2 - x1)) < 0.2:
      list.append((y1+y2)//2)

list.sort()
for i in range(0, len(list)):
  if list[i] - goodList[-1] > 0.1 * height:
    goodList.append(list[i])

goodList.append(height)
for y in goodList:
  cv2.line(img, (0, y), (width, y), (255, 0, 0), 10)
plt.imshow(img, aspect='auto')

for i in range(1, len(goodList)):
  crop_img = img[goodList[i-1]:goodList[i], 0:width]
  cropped.append(crop_img)



class Book:
  def __init__(self):
    self.row = -1
    self.Title = ""
    self.Authors = ""
    self.ISBN_10 = ""
    self.ISBN_13 = ""

bookList = []


def draw_bounding_boxes(image, result, threshold):
  for (bbox, text, score) in result:
    if score > threshold:
      (x1, y1) = tuple(map(int, bbox[0]))
      (x2, y2) = tuple(map(int, bbox[2]))
      cv2.rectangle(image, (x1, y1 + (y2 - y1)//3), (x2, y2 - (y2 - y1)//3), (0, 255, 0), 5)

def valid(text):
  # length check: at least 5 characters
  if(len(text) < 5):
    return False
  # at least 2 words in info
  if(text.count(' ') == 0):
    return False

  return True

def find_book(result, threshold, row):
  for (bbox, text, score) in result:
    book = Book()
    if (score > threshold) and valid(text):
      response = requests.get("https://www.googleapis.com/books/v1/volumes?q="+text+"&maxResults=1")
      if(response.status_code == 200):
        book.row = row+1
        # find title
        try:
          data = response.json()
          # print(data['items'][0]['volumeInfo']['title'])
          book.Title = data['items'][0]['volumeInfo']['title']
        except Exception:
          continue
        # find author
        try:
          # print("Author(s) ", end="")
          # print(*(data['items'][0]['volumeInfo']['authors']), sep=", ")
          book.Authors = ", ".join(author for author in data['items'][0]['volumeInfo']['authors'])
        except:
          pass
        # find ISBN
        try:
          # ISBN
          for info in data['items'][0]['volumeInfo']['industryIdentifiers']:
            if(info['type'] == "ISBN_10"):
              book.ISBN_10 = info['identifier']
            elif(info['type'] == "ISBN_13"):
              book.ISBN_13= info['identifier']
        except:
          pass
        bookList.append(book)

reader = easyocr.Reader(['en'])
for i in range(0, len(cropped)):
  img = cropped[i]
  img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
  result = reader.readtext(img, width_ths=1000)
  find_book(result, 0.1, i)

f = open("result.txt", 'w')
for book in bookList:
  f.write("row: " + str(book.row) + "\n")
  f.write("title: " + book.Title + "\n")
  f.write("authors: " + book.Authors + "\n")
  f.write("ISBN_10: " + book.ISBN_10 + "\n")
  f.write("ISBN_13: " + book.ISBN_13 + "\n")
  f.write("\n")















