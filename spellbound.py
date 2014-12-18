import sys, string, requests, enchant,collections,data_getter,time # requests is for HTTP requests; enchant is for checking spelling
word_repeat_limit=3
counted_comment_words=collections.Counter()#keeps track of words counted
dictionaryUS = enchant.Dict("en_US")
dictionaryGB = enchant.Dict("en_GB")

def most_popular(amount):
    # GitHub's API only allows us to return up to 100 results per page, so amount should be <= 100
    if amount > 100:
        raise Exception("amount must be less than or equal to 100")
    req = requests.get("https://api.github.com/search/repositories?q=stars:>0&per_page=" + str(amount)+str(secret))
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
    tree = requests.get("https://api.github.com/repos/" + owner + "/" + repo + "/git/trees/"+branch+"?recursive=1"+str(secret)).json()
    if tree.has_key("message"):
        return []
    # we look for the paths of files, not directories
    files = [item["path"] for item in tree["tree"] if item["type"] == "blob"]
    # ignore hidden files
    files = [x for x in files if x[0] !="."]
    files = [x for x in files if get_file_type(x) in ["js","py","rb","php","java","rs","c","md","txt"]] # we only can detect comments in certain file formats
    return files


def get_words(line):
    # returns a list of words in a given line (words can only include letters)
    words = filter(lambda s: s.isalpha(),line.split())
    return set(words)

def get_word_types(text,file_type,adding=False): #returns the line number and text of each single-line comment in a file
    code_words=set([])
    comment_words=set([])
    line_number=1
    current_word=""
    in_code=True#This indicates what character is bounding.
    comment_type=""
    skip_next=False
    if file_type in ("js","c","rs","java"):
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
                        current_word+=char
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
                if char.lower() in string.lowercase or (current_word and char=="'" and (text[i+1] in string.lowercase)):
                    current_word+=char
                else:
                    if current_word!="":
                        comment_words.add((current_word,line_number))
                        if adding: counted_comment_words[current_word]+=1
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
                        current_word+=char
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
                if char.lower() in string.lowercase or (current_word and char=="'" and (text[i+1] in string.lowercase)):
                    current_word+=char
                else:
                    if current_word!="":
                        comment_words.add((current_word,line_number))
                        if adding: counted_comment_words[current_word]+=1
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
                        current_word+=char
                    elif char=="#":
                            in_code=False
                            comment_type="#"
                    elif char=="\n":
                        line_number+=1
            else:
                if char.lower() in string.lowercase or (current_word and char=="'" and (text[i+1] in string.lowercase)):
                    current_word+=char
                else:
                    if current_word!="":
                        comment_words.add((current_word,line_number))
                        if adding: counted_comment_words[current_word]+=1
                        current_word=""
                    if char=="\n" and comment_type=='#':
                        in_code=True
                        line_number+=1
                    elif char=="\n":
                        line_number+=1
    elif file_type in ["md","txt"]:
        in_code=False
        for i in range(len(text)):
            char=text[i]
            if char.lower() in string.lowercase or (current_word and char=="'" and (text[i+1] in string.lowercase)):
                    current_word+=char
            elif current_word!="":
                    comment_words.add((current_word,line_number))
                    if adding: counted_comment_words[current_word]+=1
                    current_word=""
    for i in counted_comment_words:
        if counted_comment_words[i]>=word_repeat_limit:#yes its 5 for now
            code_words.add(i)
    return code_words.difference([""]),comment_words

def words_in_file(text):
    wordset = set([])
    for line in text:
        wordset = wordset.union(get_words(line))
    return wordset

def edits1(word): # this function is stolen from Peter Norvig's article http://norvig.com/spell-correct.html
   splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in string.lowercase if b]
   inserts    = [a + c + b     for a, b in splits for c in string.lowercase]
   return set(deletes + transposes + replaces + inserts)


def check_spelling(owner,repo,branch="master",nltk=False):
    print("Getting file paths.")
    start_time=time.time()
    paths = filter(get_file_type, file_paths(owner,repo,branch))
    print("Getting paths took %s seconds."%(str(time.time()-start_time)))

    print("Setting up requests.")
    start_time=time.time()
    data_getter.init(secret)
    for path in paths:
        if get_file_type(path):
            data_getter.get_text(owner,repo,branch,path)
    print("Setting up took %s seconds."%(str(time.time()-start_time)))

    print("Getting text.")
    start_time=time.time()
    data_getter.start()
    print("Getting text took %s seconds."%(str(time.time()-start_time)))
    print("Counting words.")
    start_time=time.time()
    for path in paths:
        text = data_getter.data[path]
        get_word_types(text,get_file_type(path),True)#Adding to counted_comment_words
    print("Counting words took %s seconds."%(str(time.time()-start_time)))
    print("Finding misspellings.")
    start_time=time.time()
    for path in paths:
        text = data_getter.data[path]
        code_words,comment_words = get_word_types(text,get_file_type(path))
        excused_words = code_words
        for item in comment_words:
            word,line_number=item
            if len(word)<=2: #skip really short words
                continue
            if nltk and pos_tag([word])[0][1]=="NNS":
                continue
            word=word.lower()
            if word[-2:]=="'s":#ignore ending in 's
                word=word[:-2]
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
    print("Finding misspellings took %s seconds"%(str(time.time()-start_time)))
secret=""
def main():
    using_nltk=False
    if sys.argv[1]=="nltk":
        from nltk.tag import pos_tag
        using_nltk=True
        sys.argv=[sys.argv[0]]+sys.argv[2:]
    if sys.argv[1]=="secret":
        secret="&client_id="+sys.argv[2]+"&client_secret="+sys.argv[3]
        sys.argv=[sys.argv[0]]+sys.argv[4:]
    if len(sys.argv) == 4:
        check_spelling(sys.argv[1],sys.argv[2],sys.argv[3],using_nltk=using_nltk)
    elif len(sys.argv)==3:
        if sys.argv[1] == "popular":
            for (owner,repo) in most_popular(int(sys.argv[2])):
                print("Checking " + owner + "/" + repo + "....")
                check_spelling(owner,repo,using_nltk=using_nltk)
        else:
            check_spelling(sys.argv[1],sys.argv[2])
    else:
        for (owner,repo) in get_owner_repos(sys.argv[1]):
            print("Checking " + owner + "/" + repo + "....")
            check_spelling(owner,repo,using_nltk=using_nltk)


if __name__ == '__main__':
    main()
