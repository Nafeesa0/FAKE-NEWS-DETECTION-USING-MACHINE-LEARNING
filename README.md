# FAKE-NEWS-DETECTION-USING-MACHINE-LEARNING


**Project Overview** 

The rapid growth of digital media and online news platforms has led to the widespread dissemination of fake news, which poses serious social, political, and cultural challenges. The inability to distinguish between genuine and misleading information can negatively influence public opinion and decision-making.

This project presents a Unified News Aggregation and Verification Portal that automatically collects news from multiple trusted sources and classifies them as Real or Fake using a deep learning model.

Unlike traditional fake news detection systems, this project not only detects fake news but also provides a centralized portal where users can access categorized news from multiple sources in one interface.



**Project Objective**

- To develop an automated fake news detection system using Deep Learning.

- To build a web-based news aggregation portal.

- To classify news articles into categories (Politics, Sports, Technology,    etc.).

- To verify news authenticity using an LSTM-based model.

- To allow users to manually input news content for verification.

**Algorithm**

Long Short-Term Memory (LSTM)

LSTM is a type of Recurrent Neural Network (RNN) used for sequential text data analysis.

Why LSTM?

- Captures contextual relationships in text

- Handles long-term dependencies

- Suitable for Natural Language Processing tasks

- Provides improved accuracy for text classification

- The model is implemented using:

      - TensorFlow
      
      - Keras

**System Architecture**

1️- Web Scraping Module

- Collects news articles from trusted online newspapers

- Extracts title, content, category, and source

2️- NLP Preprocessing

- Tokenization

- Stopword Removal

- Text Cleaning

- Text to Sequence Conversion

3️- LSTM Model

- Trained on labeled dataset

- Predicts Real or Fake

4️- Web Application

- Displays categorized news

- Shows source name

- Displays Real/Fake label

- Allows manual news input verification

**Dataset**

A labeled dataset of news articles is used for training the LSTM model.

Dataset Classes:

- Real – Genuine news articles

- Fake – Fabricated or misleading news

**Key Features**

- News aggregation from multiple sources
- Category-based filtering
- Real/Fake prediction label
- Source transparency
- Manual text verification feature
- User-friendly web interface

**Development Environment**

***Software Environment***

- Python 3.8+

- Django

- TensorFlow

- Keras

- Jupyter Notebook / VS Code 

***Hardware Requirements***

- Minimum 4 GB RAM

- Intel i3 processor or higher

- 500 MB free disk space

**Dependencies**

The following Python libraries are required:

- Python 3

- Pandas

- NumPy

- TensorFlow

- Keras

- BeautifulSoup (for scraping)

- Requests

- Scikit-learn

- Matplotlib

- Seaborn

- Django

- Regular Expressions (re)

***Installation commands:***

      - pip install pandas
      - pip install numpy
      - pip install tensorflow
      - pip install keras
      - pip install scikit-learn
      - pip install beautifulsoup4
      - pip install requests
      - pip install django
      - pip install matplotlib
      - pip install seaborn


**Research Papers Referenced**

[1] U. Sharma, S. Saran, and M. P. Shankar, 
    “Fake News Detection Using Machine Learning Techniques,” 
    International Journal of Computer Applications, 2020.

[2] Z. Khanam, B. N. Alwasel, and M. Rashid, 
    “Fake News Detection Using Ensemble Machine Learning Techniques,” 
    in IEEE Conference Proceedings, 2020.

[3] S. Pandey, S. Prabhakaran, N. V. S. Reddy, and D. Acharya, 
    “Detection of Fake News Using Machine Learning Algorithms,” 
    IEEE Access, 2021.

[4] J. Jouhar, A. Pratap, N. Tijo, and M. Mony, 
    “Fake News Detection Using Python and Machine Learning,” 
    Procedia Computer Science, vol. 233, pp. 763–771, 2024.

[5] J. Qiu et al., 
    “Deep Learning-Based Models for Misinformation Detection in Social Media,” 
    IEEE Transactions on Computational Social Systems, 2021.
