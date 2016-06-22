# coding=UTF-8
from __future__ import division
import re

# This is a naive text summarization algorithm
# Created by Shlomi Babluki
# April, 2013


class SummaryTool(object):

    # Naive method for splitting a text into sentences
    def split_content_to_sentences(self, content):
        content = content.replace("\n", ". ")
        return content.split(". ")

    # Naive method for splitting a text into paragraphs
    def split_content_to_paragraphs(self, content):
        return content.split("\n\n")

    # Caculate the intersection between 2 sentences
    def sentences_intersection(self, sent1, sent2):

        # split the sentence into words/tokens
        s1 = set(sent1.split(" "))
        s2 = set(sent2.split(" "))

        # If there is not intersection, just return 0
        if (len(s1) + len(s2)) == 0:
            return 0

        # We normalize the result by the average number of words
        return len(s1.intersection(s2)) / ((len(s1) + len(s2)) / 2)

    # Format a sentence - remove all non-alphbetic chars from the sentence
    # We'll use the formatted sentence as a key in our sentences dictionary
    def format_sentence(self, sentence):
        sentence = re.sub(r'\W+', '', sentence)
        return sentence

    # Convert the content into a dictionary <K, V>
    # k = The formatted sentence
    # V = The rank of the sentence
    def get_senteces_ranks(self, content):

        # Split the content into sentences
        sentences = self.split_content_to_sentences(content)

        # Calculate the intersection of every two sentences
        n = len(sentences)
        values = [[0 for x in xrange(n)] for x in xrange(n)]
        for i in range(0, n):
            for j in range(0, n):
                values[i][j] = self.sentences_intersection(sentences[i], sentences[j])

        # Build the sentences dictionary
        # The score of a sentences is the sum of all its intersection
        sentences_dic = {}
        for i in range(0, n):
            score = 0
            for j in range(0, n):
                if i == j:
                    continue
                score += values[i][j]
            sentences_dic[self.format_sentence(sentences[i])] = score
        return sentences_dic

    # Return the best sentence in a paragraph
    def get_best_sentence(self, paragraph, sentences_dic):

        # Split the paragraph into sentences
        sentences = self.split_content_to_sentences(paragraph)

        # Ignore short paragraphs
        if len(sentences) < 2:
            return ""

        # Get the best sentence according to the sentences dictionary
        best_sentence = ""
        max_value = 0
        for s in sentences:
            strip_s = self.format_sentence(s)
            if strip_s:
                if sentences_dic[strip_s] > max_value:
                    max_value = sentences_dic[strip_s]
                    best_sentence = s

        return best_sentence

    # Build the summary
    def get_summary(self, title, content, sentences_dic):

        # Split the content into paragraphs
        paragraphs = self.split_content_to_paragraphs(content)

        # Add the title
        summary = []
        summary.append(title.strip())
        summary.append("")

        # Add the best sentence from each paragraph
        for p in paragraphs:
            sentence = self.get_best_sentence(p, sentences_dic).strip()
            if sentence:
                summary.append(sentence)

        return ("\n").join(summary)


# Main method, just run "python summary_tool.py"
def main():

    # Demo
    # Content from: "http://thenextweb.com/apps/2013/03/21/swayy-discover-curate-content/"

    title = """
    Swayy is a beautiful new dashboard for discovering and curating online content [Invites]
    """

    content = """
    
 Creating history, the first batch of three female pilots — Avani Chaturvedi, Bhawana Kanth and Mohana Singh were inducted in Indian Air Force fighter squadron on Saturday.

On successful completion of their training, the trio were formally commissioned by Defence Minister Manohar Parrikar. Being the first to break barriers, they were the cynosure of all eyes at the parade in their immaculate turnout. On completion of their Stage III training at Bidar in adjoining Karnataka next year, they will get to fly fighter jets like the Sukhoi and Tejas.

Ms. Avani from Satna in Madhya Pradesh was inspired by her brother who is in the Army and said she always wanted to conquer the skies and hence joined the Flying Club in her college.

Ms. Mohana Singh from Jhunjhunu in Rajasthan boasts of a grandfather who was a Flight Gunner in the Aviation Research Centre and father who is a Warrant Officer in the IAF and is all excited to continue the family legacy of working in the armed forces.

Ms. Bhawana Kanth, who hails from Darbhanga in Bihar and daughter of an officer in the Indian Oil Corporation, dreamt of flying planes from her childhood days and opted for the fighter stream after her Stage I training.

All excited, the trio chorused that while getting commissioned into the IAF meant an achievement, getting trained to fly fighter jets was a dream come true. While they did nurse their hobby with a passion, they said without family support and constant motivation they could not have realized it. As for the training, they said it was the same as it was for men. “We are giving out 100 per cent all the time. The challenges and rigours of the training schedule are the same,” they said, in voices that showed their grit.

Creating history

The achievement of the three is a significant milestone for the Indian military, as this is the first time it has permitted women into combat roles.

Last October, the government decided to open the fighter stream for women on an experimental basis for five years. But combat roles in the Army and the Navy are still off limits due to a combination of operational concerns and logistical constraints.

“Joining the Indian Air Force for flying was a dream instilled by parents and grandparents,” says Ms. Mohana Singh, whose father is with the IAF and grandfather is still serving as a flight gunner in the Aviation Research Centre.

The three will begin advanced training on advanced jet trainer Hawks. It will take another 145 hours on the Hawks for almost a year before they would actually get into the cockpit of a supersonic fighter. 

    """

    # Create a SummaryTool object
    st = SummaryTool()

    # Build the sentences dictionary
    sentences_dic = st.get_senteces_ranks(content)

    # Build the summary with the sentences dictionary
    summary = st.get_summary(title, content, sentences_dic)

    # Print the summary
    print summary

    # Print the ratio between the summary length and the original length
    print ""
    print "Original Length %s" % (len(title) + len(content))
    print "Summary Length %s" % len(summary)
    print "Summary Ratio: %s" % (100 - (100 * (len(summary) / (len(title) + len(content)))))


if __name__ == '__main__':
    main()