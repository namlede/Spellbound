import sys, string, requests, enchant # requests is for HTTP requests; enchant is for checking spelling

def most_popular(amount):
    # GitHub's API only allows us to return up to 100 results per page, so amount should be <= 100
    if amount > 100:
        raise Exception("amount must be less than or equal to 100")
    req = requests.get("https://api.github.com/search/repositories?q=stars:>0&per_page=" + str(amount))
    popular = [tuple(repo["full_name"].split('/')) for repo in req.json()["items"]]
    # the format of the returned value is (owner,repo)
    return popular

def get_file_type(path):
    if "." in path:
        return path.rsplit(".")[1]
    else:
        return ""

def file_paths(owner,repo):
    tree = requests.get("https://api.github.com/repos/" + owner + "/" + repo + "/git/trees/master?recursive=1").json()
    # we look for the paths of files, not directories
    files = [item["path"] for item in tree["tree"] if item["type"] == "blob"]
    # ignore hidden files
    files = [x for x in files if x[0] !="."]
    files = [x for x in files if get_file_type(x) in ["js","py","rb"]] # we only can detect comments in certain file formats
    return files

def get_comment(line,file_type): # if a given line is a comment, this returns the comment text; otherwise, it returns False
    stripped_line = line.lstrip()
    if stripped_line == "":
        return False
    elif file_type == "js":
        if len(stripped_line) < 2:
            return False
        elif stripped_line[0:2] == "//":
            return stripped_line[2:]
        else:
            return False
    elif file_type in ["py","rb"]:
        if stripped_line[0] == "#":
            return stripped_line[1:]
        else:
            return False
    else:
        raise Exception("File format ." + file_type + " not recognized")

def get_words(line):
    # returns a list of words in a given line (words can only include letters)
    words = filter(lambda s: s.isalpha(),line.split())
    return set(words)

def get_comments(text,file_type): #returns the line number and text of each single-line comment in a file
    comments = [(line_index+1,get_comment(line,file_type)) for (line_index,line) in enumerate(text) if get_comment(line,file_type)]
    return comments

def words_in_file(text):
    wordset = set([])
    for line in text:
        wordset = wordset.union(get_words(line))
    return wordset

def words_outside_comments(text,file_type): #returns all the words in a file that are part of the actual code
    wordset = set([])
    for line in text:
        if not get_comment(line,file_type):
            wordset = wordset.union(get_words(line))
    return wordset

def get_text(owner,repo,file_path):
    raw = requests.get("https://raw.githubusercontent.com/" + owner + "/" + repo + "/master/" + file_path).text
    text = raw.split("\n")
    return text

def edits1(word): # this function is stolen from Peter Norvig's article http://norvig.com/spell-correct.html
   splits     = [(word[:i], word[i:]) for i in range(len(word) + 1)]
   deletes    = [a + b[1:] for a, b in splits if b]
   transposes = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b)>1]
   replaces   = [a + c + b[1:] for a, b in splits for c in string.lowercase if b]
   inserts    = [a + c + b     for a, b in splits for c in string.lowercase]
   return set(deletes + transposes + replaces + inserts)


def check_spelling(owner,repo):
    dictionaryUS = enchant.Dict("en_US")
    dictionaryGB = enchant.Dict("en_GB")
    paths = file_paths(owner,repo)
    print("Writing down domain-specific words....")
    special_words = [(path,words_in_file(get_text(owner,repo,path))) for path in paths]
    print("Done!")
    for path in paths:
        text = get_text(owner,repo,path)
        code_words = words_outside_comments(text,get_file_type(path))
        # excused_words includes all the words in the repo outside the comments of the file under consideration
        # this way, we allow words that are "repo-specific"
        excused_words = set.union(*[words for (fpath,words) in special_words if fpath != path])
        excused_words = excused_words.union(code_words)
        comments = get_comments(text,get_file_type(path))
        for (line_number,comment) in comments:
            word_list = filter(lambda s: s.isalpha(),comment.split())
            for word in word_list:
                wordl = word.lower()
                if not dictionaryUS.check(wordl) and not dictionaryGB.check(wordl):
                    if not word in excused_words:
                        # to narrow down the list of candidates, we only look at words that are one edit away from real words
                        edits = edits1(wordl)
                        try:
                            if True in map(lambda w: dictionaryUS.check(w), edits) or True in map(lambda w: dictionaryGB.check(w), edits):
                                url = "https://github.com/" + owner + "/" + repo + "/blob/master/" + path + "#L" + str(line_number)
                                print(word + " from " + url)
                        except:
                            print("Error on word " + word)

def main():
    if len(sys.argv) > 2:
        check_spelling(sys.argv[1],sys.argv[2])
    else:
        for (owner,repo) in most_popular(int(sys.argv[1])):
            print("Checking " + owner + "/" + repo + "....")
            check_spelling(owner,repo)

if __name__ == '__main__':
    main()