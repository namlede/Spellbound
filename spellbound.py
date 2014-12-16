import sys, string, requests, enchant,collections # requests is for HTTP requests; enchant is for checking spelling
word_repeat_limit=3
counted_comment_words=collections.Counter()#keeps track of words counted
dictionaryUS = enchant.Dict("en_US")
dictionaryGB = enchant.Dict("en_GB")

def most_popular(amount):
    # GitHub's API only allows us to return up to 100 results per page, so amount should be <= 100
    if amount > 100:
        raise Exception("amount must be less than or equal to 100")
    req = requests.get("https://api.github.com/search/repositories?q=stars:>0&per_page=" + str(amount))
    popular = [tuple(repo["full_name"].split('/')) for repo in req.json()["items"]]
    # the format of the returned value is (owner,repo)
    return popular

def get_owner_repos(owner):
    req = requests.get("https://api.github.com/users/" + owner + "/repos")
    repos = [tuple(repo["full_name"].split('/')) for repo in req.json()]
    return repos

def get_file_type(path):
    if "." in path:
        return path.rsplit(".")[1]
    else:
        return ""

def file_paths(owner,repo,branch):
    tree = requests.get("https://api.github.com/repos/" + owner + "/" + repo + "/git/trees/"+branch+"?recursive=1").json()
    # we look for the paths of files, not directories
    files = [item["path"] for item in tree["tree"] if item["type"] == "blob"]
    # ignore hidden files
    files = [x for x in files if x[0] !="."]
    files = [x for x in files if get_file_type(x) in ["js","py","rb","php","java"]] # we only can detect comments in certain file formats
    return files


def get_words(line):
    # returns a list of words in a given line (words can only include letters)
    words = filter(lambda s: s.isalpha(),line.split())
    return set(words)

def get_word_types(text,file_type): #returns the line number and text of each single-line comment in a file
    text="\n".join(text)
    code_words=set([])
    comment_words=set([])
    line_number=1
    current_word=""
    in_code=True#This indicates what character is bounding.
    comment_type=""
    skip_next=False
    if file_type=="js" or file_type=="java":
        for i in range(len(text)):
            if skip_next:
                skip_next=False
                continue
            char=text[i]
            if char=="\\":
                skip_next=True
            elif in_code:
                if char in string.lowercase:
                    current_word+=char
                else:
                    code_words.add(current_word)

                    current_word=""
                    if char in string.uppercase:
                        current_word+=char.lower()
                    elif char=="/" and text[i+1]=="/":
                            skip_next=True
                            in_code=False
                            comment_type="//"
                    elif char=="/" and text[i+1]=="*":
                            skip_next=True
                            in_code=False
                            comment_type="/*"
                    elif char=="\n":
                        line_number+=1
            else:
                if char.lower() in string.lowercase:
                    current_word+=char.lower()
                else:
                    if current_word!="":
                        comment_words.add((current_word,line_number))
                        counted_comment_words[current_word]+=1
                        current_word=""
                    if char=="\n" and comment_type=='//':
                        in_code=True
                        line_number+=1
                    elif char=="*" and text[i+1]=="/" and comment_type=='/*':
                        in_code=True
                        skip_next=True
                    elif char=="\n":
                        line_number+=1
    elif file_type=="php":
        for i in range(len(text)):
            if skip_next:
                skip_next=False
                continue
            char=text[i]
            if char=="\\":
                skip_next=True
            elif in_code:
                if char in string.lowercase:
                    current_word+=char
                else:
                    code_words.add(current_word)
                    current_word=""
                    if char in string.uppercase:
                        current_word+=char.lower()
                    elif char=="/" and text[i+1]=="/":
                            skip_next=True
                            in_code=False
                            comment_type="//"
                    elif char=="/" and text[i+1]=="*":
                            skip_next=True
                            in_code=False
                            comment_type="/*"
                    elif char=="#":
                            in_code=False
                            comment_type="#"
                    elif char=="\n":
                        line_number+=1
            else:
                if char.lower() in string.lowercase:
                    current_word+=char.lower()
                else:
                    if current_word!="":
                        comment_words.add((current_word,line_number))
                        counted_comment_words[current_word]+=1
                        current_word=""
                    if char=="\n" and comment_type=='//':
                        in_code=True
                        line_number+=1
                    elif char=="*" and text[i+1]=="/" and comment_type=='/*':
                        in_code=True
                        skip_next=True
                    elif char=="\n" and comment_type=='#':
                        in_code=True
                        line_number+=1
                    elif char=="\n":
                        line_number+=1
    elif file_type=="py":
        for i in range(len(text)):
            if skip_next:
                skip_next=False
                continue
            char=text[i]
            if char=="\\":
                skip_next=True
            elif in_code:
                if char in string.lowercase:
                    current_word+=char
                else:
                    code_words.add(current_word)
                    current_word=""
                    if char in string.uppercase:
                        current_word+=char.lower()
                    elif char=="#":
                            in_code=False
                            comment_type="#"
                    elif char=="\n":
                        line_number+=1
            else:
                if char.lower() in string.lowercase:
                    current_word+=char.lower()
                else:
                    if current_word!="":
                        comment_words.add((current_word,line_number))
                        counted_comment_words[current_word]+=1
                        current_word=""
                    if char=="\n" and comment_type=='#':
                        in_code=True
                        line_number+=1
                    elif char=="\n":
                        line_number+=1
    for i in counted_comment_words:
        if counted_comment_words[i]>=word_repeat_limit:#yes its 5 for now
            code_words.add(i)
    return code_words.difference([""]),comment_words

def words_in_file(text):
    wordset = set([])
    for line in text:
        wordset = wordset.union(get_words(line))
    return wordset

def get_text(owner,repo,branch,file_path):
    raw = requests.get("https://raw.githubusercontent.com/" + owner + "/" + repo + "/"+branch+"/" + file_path).text
    text = raw.split("\n")
    return text

def edits1(word): # this function is stolen from Peter Norvig's article http://norvig.com/spell-correct.html
   splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in string.lowercase if b]
   inserts    = [a + c + b     for a, b in splits for c in string.lowercase]
   return set(deletes + transposes + replaces + inserts)

#from nltk.tag import pos_tag
def check_spelling(owner,repo,branch="master"):
    paths = file_paths(owner,repo,branch)
    print("Writing down domain-specific words....")
    #special_words = [(path,words_in_file(get_text(owner,repo,branch,path))) for path in paths]
    print("Done!")
    for path in paths:
        text = get_text(owner,repo,branch,path)
        code_words,comment_words = get_word_types(text,get_file_type(path))
        excused_words = code_words
        for item in comment_words:
            word,line_number=item
            wordl = word.lower()
            if not dictionaryUS.check(wordl) and not dictionaryGB.check(wordl):
                if not word in excused_words:
                    # to narrow down the list of candidates, we only look at words that are one edit away from real words
                    edits = edits1(wordl)
                    try:
                        if True in map(lambda w: dictionaryUS.check(w), edits) or True in map(lambda w: dictionaryGB.check(w), edits):
                            url = "https://github.com/" + owner + "/" + repo + "/blob/"+branch+"/" + path + "#L" + str(line_number)
                            print(word + " from " + url)
                    except:
                        print("Error on word " + word)

def main():
    if len(sys.argv) > 3:
        check_spelling(sys.argv[1],sys.argv[2],sys.argv[3])
    elif len(sys.argv)==3:
        if sys.argv[1] == "popular":
            for (owner,repo) in most_popular(int(sys.argv[2])):
                print("Checking " + owner + "/" + repo + "....")
                check_spelling(owner,repo)
        else:
            check_spelling(sys.argv[1],sys.argv[2])
    else:
        for (owner,repo) in get_owner_repos(sys.argv[1]):
            print("Checking " + owner + "/" + repo + "....")
            check_spelling(owner,repo)


if __name__ == '__main__':
    main()
