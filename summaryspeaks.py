# -*- coding: utf-8 -*-
from __future__ import division
import re
import urllib
import praw
import webarticle2text
import time
from textteaser import TextTeaser
import blacklist
from decimal import Decimal
import os
from goose import Goose


HELP_MSG = "\n\n---\n\n^If ^I ^am ^not ^working ^properly, ^please ^contact [^Blackbird-007](http://www.reddit.com/message/compose/?to=Blackbird-007) ^or [^send ^a ^message ^to ^moderators](https://www.reddit.com/message/compose?to=\%2Fr\%2FIndiaSpeaks) ^of ^r/IndiaSpeaks. ^Is ^the ^summary ^incorrect? [^Send ^a ^message ^to ^our ^approved ^operators](https://www.reddit.com/message/compose?to=\%2Fr\%2FSummarySpeaks) ^and ^one ^of ^them ^will ^fix ^it. ^OP ^and ^approved ^operators ^can ^remove ^this ^summary ^by ^replying ^'delete'."

EX_HELP_MSG = "\n\n---\n\n^If ^I ^am ^not ^working ^properly, ^please ^contact [^Blackbird-007](http://www.reddit.com/message/compose/?to=Blackbird-007) ^or [^send ^a ^message ^to ^moderators](https://www.reddit.com/message/compose?to=\%2Fr\%2FIndiaSpeaks) ^of ^r/IndiaSpeaks."

def create_approved_ops_list():
    APPROVED_LIST = APPROVED_OPS.split('+')
    return APPROVED_LIST

BOT_SUBREDDIT = os.environ['BOT_SUBREDDIT']
POST_ON_SUBS = os.environ['POST_ON_SUBS']
APPROVED_OPS = os.environ['APPROVED_OPS']
USER_NAME = os.environ['REDDIT_USER']
USER_PASS = os.environ['REDDIT_PASS']
SUBMISSION_LIMIT = os.environ['SUBMISSION_LIMIT']

stats = [1, 1, 1]
short_summary_stats = 1


# This is a naive text summarization algorithm
# Created by Shlomi Babluki
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

caps = "([A-Z])"
prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov)"

def split_into_sentences(text):
    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + caps + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(caps + "[.]" + caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(caps + "[.]" + caps + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + caps + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences
  
def merge_sentences(sentences):
    text = ' '
    gap = '\n\n'
    
    if (len(sentences) < 30):
        # I know a stupid approach, mind's /g/oing fucked up right now aka rewrite this later
        # making only three paragraphs
        i = 0
        while (i < (len(sentences)/3)):
	    text = text + ' ' + sentences[i]
	    i = i + 1
	text = text + gap
	while (i < len(sentences)*2/3):
	    text = text + ' ' + sentences[i]
	    i = i + 1
	text = text + gap
	while (i < len(sentences)):
	    text = text + ' ' + sentences[i]
	    i = i + 1
    
    elif (len(sentences) < 60):
        # making only four paragraphs
        i = 0
        while (i < (len(sentences)/4)):
	    text = text + ' ' + sentences[i]
	    i = i + 1
	text = text + gap
	while (i < len(sentences)/2):
	    text = text + ' ' + sentences[i]
	    i = i + 1
	text = text + gap
	while (i < len(sentences)*3/4):
	    text = text + ' ' + sentences[i]
	    i = i + 1
	text = text + gap
	while (i < len(sentences)):
	    text = text + ' ' + sentences[i]
	    i = i + 1
    else:
        # making only five paragraphs
        i = 0
        while (i < (len(sentences)/5)):
	    text = text + ' ' + sentences[i]
	    i = i + 1
	text = text + gap
	while (i < len(sentences)*2/5):
	    text = text + ' ' + sentences[i]
	    i = i + 1
	text = text + gap
	while (i < len(sentences)*3/5):
	    text = text + ' ' + sentences[i]
	    i = i + 1
	text = text + gap
	while (i < len(sentences)*4/5):
	    text = text + ' ' + sentences[i]
	    i = i + 1
	text = text + gap
	while (i < len(sentences)):
	    text = text + ' ' + sentences[i]
	    i = i + 1
    
    #while (i < len(sentences)):
        ##try: text = text + ' ' + sentences[i] + ' ' + sentences[i+1] + ' ' + sentences[i+2] + '\n\n'
        #except:
	  #try: text = text + ' ' + sentences[i] + ' ' + sentences[i+1] + '\n\n'
	  #except:
	    #try: text = text + ' ' + sentences[i] + '\n\n'
	    #except: print "Cannot merge all sentences"
        #i = i + 3
    return text
  
def merge_sentences_individual_para(sentences):
    i = 0
    content = ' '
    text = ' '
    gap = '\n\n'
    while (i < len(sentences)):
        content = content + gap + ' ' + sentences[i]
        i = i + 1
        
    return content
  
def scrap_news(link):
    print "\nTrying to scrap link from scrap_method1"
    text = scrap_method1(link)
    
    if (len(text) < 200):
        print "Trying to scrap link from scrap_method2"
        text = scrap_method2(link)
        if (len(text) < 200):
	    text = ' ';
	    return text
	  
    return text

def make_summary(title, content):
    
    # Create a SummaryTool object
    st = SummaryTool()
    
    try: 
        sentences_dic = st.get_senteces_ranks(content)
        # Build the summary with the sentences dictionary
        summary = st.get_summary(title, content, sentences_dic)
    
        summary = summary.replace("`", "")
        summary = summary.replace("#", "\#")
        summary = summary.replace("\n", ".\n\n")
        summary = summary.replace("\n\n.\n\n", "\n\n")
        summary = summary + '.'

        # Print the summary
        print summary

        stats[0] = len(title) + len(content)
	stats[1] = len(summary)
	stats[2] = 100 - (100 * (len(summary) / (len(title) + len(content))))
	        
        # Print the ratio between the summary length and the original length
        print ""
        print "Original Length %s" % stats[0]
        print "Summary Length %s" % stats[1]
        print "Summary Ratio: %s" % stats[2]
    
    except Exception as e:
        print "3Unknown ERROR: while usig summary method 1\n"
        print type(e)
        print e.args
        print e
        print submission.id
        print "\n"
        
    return summary

# Main method, ~~just run "python summary_tool.py"~~
def make_short_summary1(title, content):
    
    title = "**" + title + "**"
    summary = """
    Summary
    """
    
    # Formatting into desired format for further processing
    sentences = split_into_sentences(content)
    content = merge_sentences(sentences)
    #print "**** Here's the merged para: \n\n", content
    
    short_summary = make_summary(title, content)
    return short_summary
  
def make_short_summary2(title, text):
    # third party program, uses nltk, makes decent summaries
    tt = TextTeaser()
    sentences = tt.summarize(title, text)
    
    return sentences
  

def make_short_summary(title,  content):
    
    text1 = make_short_summary1(title, content.encode('ascii', 'ignore'))
    
    # TextTeaser
    text2 = "**"+title+"**\n\n"
    sentences_of_text2 = make_short_summary2(title, content)
    text2 = text2 + merge_sentences_individual_para(sentences_of_text2)
    
    
    if len(text1) > len(text2):
        summary = text2
    else:
        summary = text1
    
    if len(summary) < (150 + len(title)): 
        print "Less than 150 characters"
	return "No Summary"
	     
    return summary
     

def make_extended_summary(title, article_copy):
    
    # dividing into individual sentences
    article_copy = article_copy.replace("\n\n", ' ')
    article_copy = article_copy.encode('ascii', 'ignore')
    sentences = split_into_sentences(article_copy)
    
    title = "**" + title + "**"
    # Formatting into desired format for further processing
    i = 0
    content = ' '
    text = ' '
    gap = '\n\n'
    #while (i < len(sentences)):
        #content = content + gap + ' ' + sentences[i]
        #i = i + 1
    
    # Reminder: below code was just for getting stuff done, rewrite this in future
    while (i < len(sentences)):
        try: text = text + ' ' + sentences[i] + ' ' + sentences[i+1] + ' ' + sentences[i+2] + '\n\n'
        except:
	  try: text = text + ' ' + sentences[i] + ' ' + sentences[i+1] + '\n\n'
	  except:
	    try: text = text + ' ' + sentences[i] + '\n\n'
	    except: print "Cannot merge all sentences"
        i = i + 3
    
    #print "Here's what I got: \n", text
    
    extended_summary = make_summary(title, text)
    return extended_summary

def post_extended_summary(extended_summary, submission, summary_comment):
        
    short_summary_percent = str(round(short_summary_stats))
    pre_msg = "A shorter version (reduced by " + short_summary_percent + "%) can be found on [" + str(submission.subreddit) + "](" + summary_comment.permalink+").\n\nThis is an extended summary, orginal article can be found [here]("+submission.url+")\n\n"
    
    stats[1] = len(extended_summary)
    stats[2] = 100 - (100 * (len(extended_summary) / stats[0]))
    
    stats_for_nerds = "\n\n# Stats For Nerds:\n\nOriginal Length %s" % stats[0] + "\n\nSummary Length %s" % stats[1] + "\n\nSummary Ratio: %s" % str(round(stats[2], 2)) + "%\n\n---\n\n"
    summ_title = "# Extended Summary:\n\n"
    post_msg = EX_HELP_MSG
    
    post = pre_msg + stats_for_nerds + summ_title + extended_summary + post_msg
    
    new_submission = r.submit(BOT_SUBREDDIT, submission.title, text=post, url=None)
    new_submission.add_comment(str(summary_comment.id))
    
    return new_submission

# Following codes interact with Reddit

r = praw.Reddit(user_agent="********")

r.login(USER_NAME, USER_PASS)

subreddits = str(POST_ON_SUBS)
subreddit = r.get_subreddit(subreddits)

while True:
    fo = open("looked.txt", "a+")
    position=fo.tell()
    fo.seek(0,0)
    already_done_list = fo.read()
    fo.seek(position)
    
    APPROVED_LIST = create_approved_ops_list()
    print "splited", APPROVED_LIST
    
    try:
        submissions = subreddit.get_new(limit=int(SUBMISSION_LIMIT))
    except praw.errors.HTTPException as h:
        sleep(300)
        continue

    print "Got %s submissions" % SUBMISSION_LIMIT
    for submission in submissions:
        #print "\n\nWaiting for 5 seconds"
        #time.sleep(5)
        visited = False
        
        #if submission.domain in blacklist.blocked:
	    #print "Blacklisted: " + submission.domain
	    
        if (submission.id not in already_done_list and submission.domain not in blacklist.blocked):
	    
            # check again if comment is already posted by bot and flip visited variable
            try:
                forest_comments = submission.comments
            except Exception as e:
                continue

            for comment in forest_comments:
                if str(comment.author) == USER_NAME:
		    print "Oops, I already did it: ", submission.id
                    visited = True

            # skip post if posted already
            if visited == True:
		fo.write(submission.id + " ")
                continue
		  
	    if submission.url == submission.permalink:
	        fo.write(submission.id + " ")
	        continue
	    
	    print "\nUnderreview: " + submission.id
	    
	    # Scraping the main content from the site
	    # get url and text from link
            for i in range (0, 5):
                g = Goose()
                try:
                    article_link = submission.url
                    article = g.extract(url=article_link)
                    print "extracted:\n\n"
                    main_article = article.cleaned_text
                    if len(main_article.encode('ascii', 'ignore')) > 10:
		        break
		      
		    print "waiting for 3 minutes before trying to scrape again"
		    time.sleep(180)

                except Exception as e:
                    print "2Unknown ERROR: while using goose\n"
                    print type(e)
                    print e.args
                    print e
                    print submission.id
                    print "\n"
                    continue
		
                       
            if (len(main_article) > 150):
	        summary_made = True
	        short_text = make_short_summary(submission.title, main_article)
                short_summary_stats = 100 - (100 * (len(short_text) / (len(submission.title) + len(main_article)))) # saving % reduction in short summary
                extended_text = make_extended_summary(submission.title, main_article)
            else:
	        summary_made = False
	        short_text = extended_text = "**%s**\n\nArticle could not be scraped. Approved Operators have been automatically informed. Summary will be posted shortly." % (submission.title)
            
            if short_text == "No Summary":
	        summary_made = False
	        short_text = extended_text = "No summary could be made: An operator will manually add one soon."
	    
	    short_text = short_text.replace("`", "")
            short_text = short_text.replace("#", "\#")
            extended_text = extended_text.replace("`", "")
            extended_text = extended_text.replace("#", "\#")
            
            if "cloudflare" in short_text.lower() or "cloudflare" in extended_text.lower():
	        short_text = extended_text = "cloudflare blocked. \n\n Error: I know about this, Will be fixed."
            
	    message = short_text + HELP_MSG
	    
            for i in range(0, 5):
                try:
                    summary_comment = submission.add_comment(message.encode('ascii', 'ignore'))
                    print "summary posted"
                    break
                
                except Exception as e:
                    print "1Unknown ERROR: While trying to add the make the comment on r/IndiaSpeaks"
                    print type(e)
                    print e.args
                    print e
                    print submission.id
                    print "\n"
                    time.sleep(120)
                    continue
	      
	    new_submission = post_extended_summary(extended_text, submission, summary_comment)
	    print "extended summary posted"
	    message = message + "\n\n[Extended Summary](" + new_submission.permalink + ")"
	    summary_comment.edit(message.encode('ascii', 'ignore'))
	    
	    if not(summary_made):
	        # informing the operators
	        title = "This summary needs your attention"
	        body = "Please add/edit the summary on this page: " + str(summary_comment.permalink)
	        r.send_message(BOT_SUBREDDIT, title, body)
	        print "modmail sent!"
            
            fo.write(submission.id + " ")
            print "Rest of 0.5 min before next summary"
            time.sleep(30)
            	    
    # Do secondary jobs when there is no more summaries    
    
    unread = r.get_unread(limit=None)
    for msg in unread:
        # Code to delete summaries
        # only works if the word delete is posted as it is, without edit.
        if msg.body.lower() == 'delete':
            try:

                # get comment id from message.
                idd = msg.id
                idd = 't1_' + idd

                # find comment from id
                comment = r.get_info(thing_id=idd)

                # find parent comment i.e comment containing the summary
                parentid = comment.parent_id
                comment_parent = r.get_info(thing_id=parentid)

                # get submission author through submission link id
                sublink = comment_parent.link_id
                author1 = r.get_info(thing_id=sublink)

                # verify author of message is OP, then delete message and mark unread.
                if (str(msg.author.name) == str(author1.author) or str(msg.author.name) in APPROVED_LIST):
                    comment_parent.delete()
                    print "deleted"

                    msg.mark_as_read()
                else:

                    msg.mark_as_read()
                    continue
            except Exception as e:
                print "4Unknown ERROR: While deleting a summary"
                print type(e)
                print e.args
                print e
                print "\n"
                # continue
                msg.mark_as_read()
                continue
	     
	# code to edit summaries
	else:
	    try:
	        # get the subreddit on which comment was posted
	        idd = msg.id
                idd = 't1_' + idd

                # find comment from id
                msg_comment = r.get_info(thing_id=idd)
                
                # find the submission
                extended_summary_id = msg_comment.link_id
                extended_summary_submission = r.get_info(thing_id=extended_summary_id)
                
                # find the subreddit
                extended_summary_subreddit = extended_summary_submission.subreddit
                
                # only proceed if the given subreddit is r/SummarySpeaks
                if str(extended_summary_subreddit) == BOT_SUBREDDIT and str(msg_comment.author) in APPROVED_LIST:
	            
		    print "prepare edited summary"
		    edited_summary = "**" + extended_summary_submission.title + "**\n\n" + msg_comment.body + "\n\nSummary edited by: %s \n\n" % str(msg_comment.author)
		    message = edited_summary.encode('ascii','ignore') + HELP_MSG
		    
		    print "find the original summary on r/IndiaSpeaks through another comment on extended_summary_submission"
                    print "finding the id"
                    original_summary_id = "none"
                    forest_comments = extended_summary_submission.comments
                    
                    for comment in forest_comments:
                        if str(comment.author) == USER_NAME:
		            original_summary_id = str(comment.body)
		            
		    if original_summary_id == "none": 
		        continue
		      
		    original_summary_id = 't1_' + original_summary_id  
		      
		    print "id found, now fetching the original comment"
		    original_summary_comment = r.get_info(thing_id=original_summary_id)
		    
		    print "replacing current summary with edited summary"
		    original_summary_comment.edit(message.encode('ascii', 'ignore'))
		    
		    msg.mark_as_read()
		    
	    except Exception as e:
                print "5Unknown ERROR: While editing a summary"
                print type(e)
                print e.args
                print e
                print "\n"
                # continue
                msg.mark_as_read()
                continue
    
    print "rest for 5 mins"
    time.sleep(300)
